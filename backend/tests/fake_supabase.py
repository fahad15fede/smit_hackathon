"""In-memory stand-in for the Supabase client, covering the PostgREST features the repositories use.

Supported: select with ``alias:table!fk_column(columns)`` embedding (many-to-one when the hint
column is a foreign key on the parent table, one-to-many otherwise), eq/neq/gt/gte/lt/lte/in_ filters, order,
limit, insert/update/delete returning rows, unique constraints and ``on delete cascade``.
"""

import copy
import itertools
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from postgrest.exceptions import APIError

Row = dict[str, Any]

# Mirrors supabase/schema.sql. A ``lower:`` prefix means case-insensitive uniqueness.
UNIQUE = {
    "holidays": [("day",)],
    "departments": [("lower:name",)],
    "leave_types": [("lower:name",)],
    "employees": [("email",)],
    "users": [("email",), ("employee_id",)],
    "attendance": [("employee_id", "day")],
    "payroll_runs": [("month",)],
    "payslips": [("payroll_run_id", "employee_id")],
}
CASCADE = {
    "employees": [("users", "employee_id"), ("attendance", "employee_id"), ("leave_requests", "employee_id"), ("payslips", "employee_id")],
    "payroll_runs": [("payslips", "payroll_run_id")],
}
# (table, column) pairs that reference another table's id, i.e. many-to-one relationships.
FOREIGN_KEYS = {
    ("employees", "department_id"), ("users", "employee_id"), ("attendance", "employee_id"),
    ("leave_requests", "employee_id"), ("leave_requests", "leave_type_id"), ("leave_requests", "reviewed_by_id"),
    ("payroll_runs", "created_by_id"), ("payslips", "payroll_run_id"), ("payslips", "employee_id"),
    ("audit_logs", "actor_id"),
}
TIMESTAMPED = {"companies", "employees", "users", "leave_requests", "payroll_runs", "audit_logs"}


@dataclass
class Response:
    data: list[Row]


@dataclass
class Embed:
    alias: str
    table: str
    hint: str
    columns: list["str | Embed"]


def _split_top_level(text: str) -> list[str]:
    parts, depth, current = [], 0, ""
    for char in text:
        if char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
            continue
        depth += {"(": 1, ")": -1}.get(char, 0)
        current += char
    if current.strip():
        parts.append(current.strip())
    return parts


def _parse_columns(text: str) -> list[str | Embed]:
    columns: list[str | Embed] = []
    for part in _split_top_level(text):
        if "(" not in part:
            columns.append(part)
            continue
        head, inner = part.split("(", 1)
        alias, _, target = head.rpartition(":")
        table, _, hint = target.partition("!")
        if not hint:
            raise ValueError(f"Fake Supabase requires an explicit !fk hint in embed {part!r}")
        columns.append(Embed(alias or table, table, hint, _parse_columns(inner[:-1])))
    return columns


def _comparable(left: Any, right: Any) -> tuple[Any, Any]:
    """Numeric columns come back as strings after JSON serialization; compare them as numbers."""
    if isinstance(right, (int, float)) and not isinstance(right, bool) and isinstance(left, str):
        return float(left), right
    return left, right


class FakeSupabase:
    def __init__(self) -> None:
        self.tables: dict[str, list[Row]] = {}
        self._ids = itertools.count(1)

    def table(self, name: str) -> "Query":
        return Query(self, name)

    def rows(self, name: str) -> list[Row]:
        return self.tables.setdefault(name, [])

    # Writes --------------------------------------------------------------------------
    def insert(self, name: str, values: Row | list[Row]) -> list[Row]:
        inserted = []
        for row in values if isinstance(values, list) else [values]:
            row = {"id": next(self._ids), **copy.deepcopy(row)}
            if name in TIMESTAMPED:
                row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            self._check_unique(name, row)
            self.rows(name).append(row)
            inserted.append(copy.deepcopy(row))
        return inserted

    def update(self, name: str, matched: list[Row], changes: Row) -> list[Row]:
        for row in matched:
            candidate = {**row, **copy.deepcopy(changes)}
            self._check_unique(name, candidate, ignore=row)
            row.update(candidate)
        return copy.deepcopy(matched)

    def delete(self, name: str, matched: list[Row]) -> list[Row]:
        for row in matched:
            for child, column in CASCADE.get(name, []):
                self.delete(child, [r for r in self.rows(child) if r.get(column) == row["id"]])
        ids = {id(row) for row in matched}
        self.tables[name] = [row for row in self.rows(name) if id(row) not in ids]
        return copy.deepcopy(matched)

    def _check_unique(self, name: str, row: Row, ignore: Row | None = None) -> None:
        def key(candidate: Row, columns: tuple[str, ...]) -> tuple:
            return tuple(
                str(candidate.get(c.removeprefix("lower:"))).lower() if c.startswith("lower:") else candidate.get(c)
                for c in columns
            )

        for columns in UNIQUE.get(name, []):
            if any(other is not ignore and key(other, columns) == key(row, columns) for other in self.rows(name)):
                raise APIError({"code": "23505", "message": f"duplicate key value violates unique constraint on {name}"})

    # Reads ---------------------------------------------------------------------------
    def project(self, name: str, row: Row, columns: list[str | Embed]) -> Row:
        result: Row = {}
        for column in columns:
            if column == "*":
                result.update(copy.deepcopy(row))
            elif isinstance(column, str):
                result[column] = copy.deepcopy(row.get(column))
            elif (name, column.hint) in FOREIGN_KEYS:  # many-to-one: the foreign key lives on this row
                parent = next((r for r in self.rows(column.table) if r["id"] == row.get(column.hint)), None)
                result[column.alias] = self.project(column.table, parent, column.columns) if parent else None
            else:  # one-to-many: children point back at this row
                children = [r for r in self.rows(column.table) if r.get(column.hint) == row["id"]]
                result[column.alias] = [self.project(column.table, child, column.columns) for child in children]
        return result


class Query:
    def __init__(self, db: FakeSupabase, table: str):
        self._db, self._table = db, table
        self._action, self._values, self._columns = "select", None, ["*"]
        self._filters: list = []
        self._order: list[tuple[str, bool]] = []
        self._limit: int | None = None

    def select(self, columns: str = "*") -> "Query":
        self._action, self._columns = "select", _parse_columns(columns)
        return self

    def insert(self, values: Row | list[Row]) -> "Query":
        self._action, self._values = "insert", values
        return self

    def update(self, values: Row) -> "Query":
        self._action, self._values = "update", values
        return self

    def delete(self) -> "Query":
        self._action = "delete"
        return self

    def _filter(self, column: str, test) -> "Query":
        self._filters.append((column, test))
        return self

    def eq(self, column: str, value: Any) -> "Query":
        return self._filter(column, lambda v: v == value)

    def neq(self, column: str, value: Any) -> "Query":
        return self._filter(column, lambda v: v != value)

    def gt(self, column: str, value: Any) -> "Query":
        return self._filter(column, lambda v: v is not None and _comparable(v, value)[0] > _comparable(v, value)[1])

    def gte(self, column: str, value: Any) -> "Query":
        return self._filter(column, lambda v: v is not None and _comparable(v, value)[0] >= _comparable(v, value)[1])

    def lt(self, column: str, value: Any) -> "Query":
        return self._filter(column, lambda v: v is not None and _comparable(v, value)[0] < _comparable(v, value)[1])

    def lte(self, column: str, value: Any) -> "Query":
        return self._filter(column, lambda v: v is not None and _comparable(v, value)[0] <= _comparable(v, value)[1])

    def in_(self, column: str, values: list) -> "Query":
        return self._filter(column, lambda v: v in values)

    def order(self, column: str, *, desc: bool = False) -> "Query":
        self._order.append((column, desc))
        return self

    def limit(self, count: int) -> "Query":
        self._limit = count
        return self

    def execute(self) -> Response:
        if self._action == "insert":
            return Response(self._db.insert(self._table, self._values))
        matched = [row for row in self._db.rows(self._table) if all(test(row.get(c)) for c, test in self._filters)]
        if self._action == "update":
            return Response(self._db.update(self._table, matched, self._values))
        if self._action == "delete":
            return Response(self._db.delete(self._table, matched))
        for column, desc in reversed(self._order):
            matched.sort(key=lambda row: (row.get(column) is None, row.get(column)), reverse=desc)
        if self._limit is not None:
            matched = matched[: self._limit]
        return Response([self._db.project(self._table, row, self._columns) for row in matched])
