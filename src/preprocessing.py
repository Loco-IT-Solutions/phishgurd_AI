# src/preprocessing.py
import re
import tldextract

SUSPICIOUS_WORDS = [
    "verify", "password", "account", "urgent", "click", "bank", "login", "confirm",
    "security", "update", "invoice", "payment", "suspend"
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    # remove weird whitespace and control chars
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_basic_features(subject: str, sender: str, body: str) -> dict:
    subject = clean_text(subject)
    body = clean_text(body)
    sender = (sender or "").strip()

    # simple suspicious-word count
    combined = " ".join([subject, body])
    s_count = sum(1 for w in SUSPICIOUS_WORDS if w in combined)

    # sender domain
    domain = ""
    try:
        ext = tldextract.extract(sender)
        if ext.domain:
            domain = ".".join([ext.domain, ext.suffix]) if ext.suffix else ext.domain
    except Exception:
        domain = ""

    # basic heuristics
    has_ip = bool(re.search(r'\d+\.\d+\.\d+\.\d+', sender))
    has_link_like = bool(re.search(r'http[s]?://', body + subject))

    return {
        "subject": subject,
        "body": body,
        "sender": sender,
        "domain": domain,
        "suspicious_word_count": s_count,
        "has_ip": int(has_ip),
        "has_link": int(has_link_like)
    }
