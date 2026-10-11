import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import bank
from .security import analyze

app = FastAPI(title="Bankism")


class Chat(BaseModel):
    message: str


class Confirm(BaseModel):
    pending_id: str


class Trust(BaseModel):
    enabled: bool
    verified: bool = False


def log(kind, **data):
    bank.events.insert(0, {"time": time.strftime("%H:%M:%S"), "kind": kind, **data})


FAQ = {
    "interest": "Compound interest means you earn interest on your interest, so savings grow faster over time.",
    "budget": "A simple budget: 50% needs, 30% wants, 20% savings.",
    "emergency": "An emergency fund of 3-6 months of expenses is a good target.",
}


@app.post("/api/chat")
def chat(req: Chat):
    verdict = analyze(req.message)
    base = {"verdict": verdict, "balance": bank.account["balance"]}

    if verdict["decision"] == "BLOCK":
        log("blocked", message=req.message, score=verdict["risk_score"], threats=verdict["threats"])
        alert = None
        if verdict["severity"] == "high" and bank.trusted["enabled"] and bank.trusted["verified"]:
            alert = f"Alert sent to {bank.trusted['contact']}: suspicious activity on the account. (No details shared.)"
            log("alert", message=alert)
        return {**base, "status": "blocked",
                "reply": "I blocked that request because it looks unsafe. Your account was not changed.",
                "alert": alert}

    if verdict["decision"] == "CLARIFY":
        log("clarify", message=req.message, score=verdict["risk_score"])
        return {**base, "status": "clarify",
                "reply": "That request looks unusual. Can you tell me more about what you need?"}

    intent = bank.detect_intent(req.message)
    if intent["type"] == "balance":
        log("balance", message="Balance check")
        return {**base, "status": "ok", "reply": f"Your balance is ${bank.account['balance']:.2f}."}

    if intent["type"] == "transfer":
        amt, rec = intent["amount"], intent["recipient"]
        if amt is None or rec is None:
            return {**base, "status": "clarify",
                    "reply": "Who should I pay and how much? Example: 'Send 50 to Alice'."}
        problems = bank.validate_transfer(amt, rec)
        if problems:
            log("blocked", message=req.message + " -> " + "; ".join(problems))
            return {**base, "status": "blocked", "reply": "Transfer blocked: " + "; ".join(problems)}
        pid = bank.create_pending(amt, rec)
        log("pending", message=f"Transfer ${amt:.2f} to {rec} awaiting confirmation")
        return {**base, "status": "needs_confirmation", "pending_id": pid,
                "reply": f"Please confirm: send ${amt:.2f} to {bank.RECIPIENTS[rec]}?"}

    reply = next((v for k, v in FAQ.items() if k in req.message.lower()),
                 "I can help with balances, transfers to saved payees, and basic money questions.")
    return {**base, "status": "ok", "reply": reply}


@app.post("/api/confirm")
def confirm(req: Confirm):
    ok, problems = bank.execute(req.pending_id)
    log("executed" if ok else "blocked",
        message="Transfer confirmed" if ok else "; ".join(problems))
    return {"ok": ok, "problems": problems, "balance": bank.account["balance"]}


@app.get("/api/account")
def get_account():
    return {**bank.account, "trusted": bank.trusted}


@app.get("/api/events")
def get_events():
    return bank.events[:30]


@app.post("/api/trusted-circle")
def set_trusted(t: Trust):
    bank.trusted.update({"enabled": t.enabled, "verified": t.verified})
    return bank.trusted


@app.post("/api/reset")
def reset():
    bank.reset()
    return {"ok": True}


# Serve the built React app (present in Docker / after `npm run build`)
static = Path(__file__).resolve().parent.parent / "static"
if static.exists():
    app.mount("/", StaticFiles(directory=static, html=True), name="static")