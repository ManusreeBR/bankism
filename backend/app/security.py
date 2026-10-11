import re
import unicodedata


def normalize(text: str) -> str:
    """Defeat tricks: unicode lookalikes, zero-width chars, odd spacing, caps."""
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]", "", t)
    return re.sub(r"\s+", " ", t).strip().lower()


# (category, points, regex, human explanation)
RULES = [
    # ---------- English ----------
    ("prompt_injection", 60,
     r"\bignore\b.{0,20}\b(previous|prior|above|earlier|all)\b.{0,20}\b(instructions|rules|prompts?)\b",
     "Tries to make the assistant ignore its instructions"),
    ("prompt_injection", 50,
     r"\b(disregard|forget|override|bypass)\b.{0,30}\b(rules|instructions|guidelines|limits|safety|security)\b",
     "Tries to override safety rules"),
    ("rule_override", 50,
     r"\b(developer|admin|god|debug|jailbreak|unrestricted)\s+mode\b|\byou are now\b|\bpretend (to be|you are)\b",
     "Attempts to change the assistant's role or privileges"),
    ("secret_extraction", 50,
     r"\b(reveal|show|print|repeat|leak)\b.{0,20}\b(system prompt|hidden instructions|api key|password|secret|pin)\b",
     "Tries to extract hidden instructions or secrets"),
    ("confirmation_bypass", 35,
     r"\b(skip|without|no need for|don'?t ask for|do not ask for)\b.{0,15}\b(confirmation|verification|otp|approval|confirming)\b",
     "Tries to skip the confirmation step"),
    ("limit_bypass", 35,
     r"\b(remove|ignore|raise|disable|bypass|increase)\b.{0,15}\b(daily |transfer |spending )?limits?\b",
     "Tries to bypass transfer limits"),
    ("suspicious_payment", 25,
     r"\b(transfer|send|wire|move)\b.{0,10}\b(all|everything|entire|full)\b",
     "Requests draining the entire account"),
    ("suspicious_payment", 20,
     r"\b(gift ?cards?|bitcoin|crypto|western union|wire to unknown)\b",
     "Mentions a common scam payment method"),
    ("urgency_pressure", 15,
     r"\b(urgent(ly)?|immediately|right now|asap|before anyone)\b",
     "Uses urgency pressure, a common scam tactic"),

    # ---------- Hindi ----------
    ("prompt_injection", 60,
     r"(निर्देश|नियम).{0,20}(अनदेखा|भूल जाओ|भूल जाइए|भूल जाएं)",
     "Tries to make the assistant ignore its instructions (Hindi)"),
    ("rule_override", 50,
     r"(डेवलपर|एडमिन|डीबग) मोड",
     "Attempts to change the assistant's role or privileges (Hindi)"),
    ("confirmation_bypass", 35,
     r"बिना.{0,10}(पुष्टि|कन्फर्म|कन्फर्मेशन)",
     "Tries to skip the confirmation step (Hindi)"),
    ("limit_bypass", 35,
     r"(सीमा|लिमिट).{0,10}(हटा|खत्म)",
     "Tries to bypass transfer limits (Hindi)"),
    ("secret_extraction", 50,
     r"(सिस्टम प्रॉम्प्ट|गुप्त निर्देश|पासवर्ड|पिन).{0,15}(बताओ|दिखाओ|बताइए|दिखाइए)",
     "Tries to extract hidden instructions or secrets (Hindi)"),
]


def analyze(message: str) -> dict:
    text = normalize(message)
    score, findings = 0, []
    for category, points, pattern, why in RULES:
        if re.search(pattern, text):
            score += points
            findings.append({"category": category, "points": points, "explanation": why})
    score = min(score, 100)

    if score >= 50:
        decision = "BLOCK"
    elif score >= 20:
        decision = "CLARIFY"
    else:
        decision = "APPROVE"

    severity = "high" if score >= 70 else "medium" if score >= 50 else "low" if score >= 20 else "none"
    return {
        "decision": decision,
        "risk_score": score,
        "severity": severity,
        "threats": sorted({f["category"] for f in findings}),
        "explanations": [f["explanation"] for f in findings] or ["No threats detected"],
    }