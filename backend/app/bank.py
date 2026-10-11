import re
import uuid
import copy

INITIAL = {"owner": "Demo User", "balance": 5000.00, "per_txn_limit": 500.00,
           "daily_limit": 1000.00, "spent_today": 0.00}
RECIPIENTS = {"alice": "Alice Johnson", "bob": "Bob Smith", "carol": "Carol Lee"}

account = copy.deepcopy(INITIAL)
pending: dict = {}
events: list = []
trusted = {"enabled": False, "contact": "Mom", "verified": False}


def reset():
    account.clear()
    account.update(copy.deepcopy(INITIAL))
    pending.clear()
    events.clear()
    trusted.update({"enabled": False, "verified": False})


def detect_intent(msg: str) -> dict:
    t = msg.lower()
    if re.search(r"\bbalance\b", t):
        return {"type": "balance"}
    if re.search(r"\b(send|transfer|pay|wire)\b", t):
        amt = re.search(r"\$?\s*(\d+(?:\.\d{1,2})?)", t)
        rec = next((k for k in RECIPIENTS if k in t), None)
        return {"type": "transfer",
                "amount": float(amt.group(1)) if amt else None,
                "recipient": rec}
    return {"type": "question"}


def validate_transfer(amount, recipient) -> list:
    """Independent gate. Returns a list of failure reasons; empty means allowed."""
    problems = []
    if recipient not in RECIPIENTS:
        problems.append("Recipient is not in your saved payees")
    if amount is None or amount <= 0:
        problems.append("Amount must be greater than zero")
        return problems
    if amount > account["balance"]:
        problems.append("Insufficient funds")
    if amount > account["per_txn_limit"]:
        problems.append(f"Exceeds per-transfer limit of ${account['per_txn_limit']:.0f}")
    if account["spent_today"] + amount > account["daily_limit"]:
        problems.append(f"Exceeds daily limit of ${account['daily_limit']:.0f}")
    return problems


def create_pending(amount, recipient) -> str:
    pid = uuid.uuid4().hex[:8]
    pending[pid] = {"amount": amount, "recipient": recipient}
    return pid


def execute(pid: str):
    p = pending.pop(pid, None)  # single use
    if p is None:
        return False, ["Unknown or already-used confirmation"]
    problems = validate_transfer(p["amount"], p["recipient"])  # validate AGAIN
    if problems:
        return False, problems
    account["balance"] = round(account["balance"] - p["amount"], 2)
    account["spent_today"] += p["amount"]
    return True, []