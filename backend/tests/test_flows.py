from datetime import date

from .conftest import PASSWORD, auth, create_user


def test_setup_runs_only_once(client, admin_token):
    status = client.get("/api/setup/status").json()
    assert status == {"ready": True, "company_name": "Acme"}
    again = client.post(
        "/api/setup",
        json={"company_name": "Other", "admin_name": "Bob", "email": "bob@x.io", "password": PASSWORD},
    )
    assert again.status_code == 409


def test_login_and_me(client, admin_token):
    assert client.post("/api/auth/login", json={"email": "admin@acme.io", "password": "wrong-pass"}).status_code == 401
    me = client.get("/api/auth/me", headers=auth(admin_token)).json()
    assert me["role"] == "admin"
    assert me["employee"]["full_name"] == "Ada Admin"
    assert client.get("/api/auth/me").status_code == 401


def test_role_permissions(client, admin_token):
    hr = create_user(client, admin_token, "hr@acme.io", role="hr")
    employee = create_user(client, hr, "emp@acme.io")

    assert client.get("/api/employees", headers=auth(employee)).status_code == 403
    assert client.get("/api/audit", headers=auth(hr)).status_code == 403
    # HR may register employees but not promote anyone to HR.
    promoted = client.post(
        "/api/employees",
        headers=auth(hr),
        json={
            "full_name": "Sneaky",
            "email": "sneaky@acme.io",
            "designation": "Staff",
            "join_date": "2024-01-01",
            "monthly_salary": 1,
            "role": "hr",
            "password": PASSWORD,
        },
    )
    assert promoted.status_code == 403


def test_deactivated_user_cannot_log_in(client, admin_token):
    create_user(client, admin_token, "gone@acme.io")
    employee_id = next(e["id"] for e in client.get("/api/employees", headers=auth(admin_token)).json() if e["email"] == "gone@acme.io")
    deactivated = client.patch(f"/api/employees/{employee_id}", headers=auth(admin_token), json={"is_active": False})
    assert deactivated.json()["is_active"] is False
    assert client.post("/api/auth/login", json={"email": "gone@acme.io", "password": PASSWORD}).status_code == 401


def test_attendance_check_in_and_out(client, admin_token):
    employee = create_user(client, admin_token, "emp@acme.io")
    assert client.post("/api/attendance/check-out", headers=auth(employee)).status_code == 422

    check_in = client.post("/api/attendance/check-in", headers=auth(employee))
    assert check_in.status_code == 200, check_in.text
    assert check_in.json()["status"] in {"present", "late"}
    assert client.post("/api/attendance/check-in", headers=auth(employee)).status_code == 409

    assert client.post("/api/attendance/check-out", headers=auth(employee)).json()["check_out"] is not None
    assert client.get("/api/dashboard/me", headers=auth(employee)).json()["attendance"] is not None


def test_leave_request_lifecycle(client, admin_token):
    hr = create_user(client, admin_token, "hr@acme.io", role="hr")
    employee = create_user(client, hr, "emp@acme.io")
    leave_type = client.post(
        "/api/leave-types", headers=auth(admin_token), json={"name": "Annual", "annual_quota": 5}
    ).json()

    year = date.today().year
    payload = {"leave_type_id": leave_type["id"], "start_date": f"{year}-03-02", "end_date": f"{year}-03-04", "reason": "Family trip"}
    created = client.post("/api/leaves", headers=auth(employee), json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["working_days"] == 3

    # Overlapping and over-quota requests are rejected.
    assert client.post("/api/leaves", headers=auth(employee), json=payload).status_code == 409
    too_long = {**payload, "start_date": f"{year}-04-01", "end_date": f"{year}-04-10"}
    assert client.post("/api/leaves", headers=auth(employee), json=too_long).status_code == 422

    leave_id = created.json()["id"]
    decided = client.post(f"/api/leaves/{leave_id}/decision", headers=auth(hr), json={"approved": True, "comment": "Enjoy"})
    assert decided.json()["status"] == "approved"
    assert client.post(f"/api/leaves/{leave_id}/decision", headers=auth(hr), json={"approved": False}).status_code == 409

    balance = client.get("/api/leaves/me/balances", headers=auth(employee)).json()[0]
    assert (balance["used"], balance["remaining"]) == (3, 2)


def test_payroll_draft_finalize_and_payslip_visibility(client, admin_token):
    hr = create_user(client, admin_token, "hr@acme.io", role="hr")
    employee = create_user(client, hr, "emp@acme.io", salary=31000)
    month = "2025-01"  # Fully in the past, no attendance: every working day is unpaid.

    run = client.post("/api/payroll", headers=auth(hr), json={"month": month})
    assert run.status_code == 201, run.text
    slips = {slip["employee"]["full_name"]: slip for slip in run.json()["payslips"]}
    assert "Ada Admin" not in slips  # zero-salary profiles are skipped
    assert slips["Emp"]["working_days"] == 31
    assert slips["Emp"]["net"] == 0

    assert client.post("/api/payroll", headers=auth(hr), json={"month": month}).status_code == 409
    assert client.get("/api/payslips/me", headers=auth(employee)).json() == []  # drafts stay hidden

    run_id = run.json()["id"]
    assert client.post(f"/api/payroll/{run_id}/finalize", headers=auth(hr)).status_code == 403
    assert client.post(f"/api/payroll/{run_id}/finalize", headers=auth(admin_token)).json()["status"] == "finalized"
    assert len(client.get("/api/payslips/me", headers=auth(employee)).json()) == 1


def test_dashboard(client, admin_token):
    employee = create_user(client, admin_token, "emp@acme.io")
    client.post("/api/attendance/check-in", headers=auth(employee))

    stats = client.get("/api/dashboard/organization", headers=auth(admin_token)).json()
    assert stats["headcount"] == 2
    assert stats["present"] + stats["late"] == 1
    assert len(stats["trend"]) == 14

    assert stats["month_attendance_rate"] is not None
