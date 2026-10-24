"""Answers that never need the model: small talk, help and "where do I…" navigation.

Matching is deliberately conservative. Small talk must be the whole message ("hi", "thanks!"),
so "hi, how many employees are in Sales?" still goes to the model. These replies are not AI
calls: they skip the provider, the rate limit and ``ai_logs``.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from ..models import Role, User

MANAGERS = {Role.ADMIN, Role.HR}
STAFF = {Role.HR, Role.EMPLOYEE}

_FILLER = r"(?:\s+(?:there|assistant|bot|again|so much|a lot|very much))*"


def _whole(pattern: str) -> re.Pattern[str]:
    return re.compile(rf"^(?:{pattern}){_FILLER}$")


GREETING = _whole(r"hi+|hello+|hey+|hiya|yo|salam|assalam ?(?:o|u)? ?alaikum|good (?:morning|afternoon|evening)")
HOW_ARE_YOU = _whole(r"how are you(?: doing)?|how(?:'s| is) it going|what'?s up")
THANKS = _whole(r"thanks?|thank you|thx|ty|cheers|shukriya|jazakallah(?: khair)?|appreciate it")
GOODBYE = _whole(r"bye|goodbye|see you|see ya|good night|khuda hafiz|allah hafiz")
ACK = _whole(r"ok(?:ay)?|cool|great|nice|got it|alright|perfect|sure")
HELP = _whole(r"help|help me|what can you do|what do you do|who are you|what are you|how does this work|menu")


def _first_name(user: User) -> str:
    return user.employee.full_name.split()[0]


def _help_text(user: User) -> str:
    if user.role in MANAGERS:
        examples = [
            "How many active employees are in each department?",
            "Who came late most often this month?",
            "What is this month's attendance rate?",
            "Who is on leave today?",
            "What is the total payroll for this month?",
        ]
    else:
        examples = [
            "How many sick leaves do I have left this year?",
            "What is my attendance this month?",
            "What happens if I check in late?",
            "Has my latest payslip been finalized?",
        ]
    return "I can answer questions about your HR data and company policy. Try asking:\n" + "\n".join(
        f"- {example}" for example in examples
    )


@dataclass(frozen=True)
class _Route:
    pattern: re.Pattern[str]
    roles: set[Role]
    answer: str


def _route(pattern: str, roles: set[Role], answer: str) -> _Route:
    return _Route(re.compile(pattern), roles, answer)


# "How do I / where can I …" questions about using the app. Data questions never match these.
_HOW_TO = r"^(?:how|where)\b.*\b(?:do|can|to|should|would)\b.*"
NAVIGATION = [
    _route(
        _HOW_TO + r"\b(?:apply|request|take|ask)\b.*\bleave\b",
        STAFF,
        'Open the Leave page and type what you need into "Describe your leave", for example '
        '"Next Monday off for a family event". It fills in the form, and you review it before submitting.',
    ),
    _route(
        _HOW_TO + r"\bcancel\b.*\bleave\b",
        STAFF,
        "Open the Leave page and press Cancel next to the request. You can cancel a request while it is still pending.",
    ),
    _route(
        _HOW_TO + r"\bcheck(?:\s|-)?(?:in|out)\b",
        STAFF,
        "Open the Attendance page and press Check in when you start, and Check out when you finish. "
        "The time comes from the server clock.",
    ),
    _route(
        _HOW_TO + r"\b(?:see|view|find|get|download)\b.*\bpayslips?\b",
        STAFF,
        "Open the Payslips page. A payslip appears there once an Admin has finalized that month's payroll.",
    ),
    _route(
        _HOW_TO + r"\b(?:approve|reject|review)\b.*\bleave",
        MANAGERS,
        "Open Leave approvals. Pending requests are listed first; choose Approve or Reject and add an optional comment.",
    ),
    _route(
        _HOW_TO + r"\b(?:add|create|register|onboard)\b.*\bemployees?\b",
        MANAGERS,
        "Open the Employees page and press Add employee. This also creates their sign-in account.",
    ),
    _route(
        _HOW_TO + r"\b(?:run|create|process|finalize)\b.*\bpayroll\b",
        MANAGERS,
        "Open the Payroll page. HR creates a draft for the month with Run payroll, and an Admin reviews and finalizes it.",
    ),
    _route(
        _HOW_TO + r"\bchange\b.*\bpassword\b",
        {Role.ADMIN, Role.HR, Role.EMPLOYEE},
        "Use Password at the bottom of the sidebar. Enter your current password, then the new one twice.",
    ),
]


def _normalize(message: str) -> str:
    text = message.lower().replace("’", "'")
    text = re.sub(r"[^\w\s'-]", " ", text)  # drop punctuation and emoji
    return re.sub(r"\s+", " ", text).strip()


def match(message: str, user: User) -> str | None:
    """A ready answer for small talk, help or navigation, or ``None`` to ask the model."""
    text = _normalize(message)
    small_talk: list[tuple[re.Pattern[str], Callable[[], str]]] = [
        (GREETING, lambda: f"Hello {_first_name(user)}! How can I help you today?"),
        (HOW_ARE_YOU, lambda: "I'm doing well, thank you for asking. What can I help you with?"),
        (THANKS, lambda: "You're welcome! Let me know if there is anything else."),
        (GOODBYE, lambda: f"Goodbye, {_first_name(user)}. Have a great day!"),
        (ACK, lambda: "Great. Is there anything else you'd like to know?"),
        (HELP, lambda: _help_text(user)),
    ]
    for pattern, reply in small_talk:
        if pattern.match(text):
            return reply()
    for route in NAVIGATION:
        if user.role in route.roles and route.pattern.search(text):
            return route.answer
    return None
