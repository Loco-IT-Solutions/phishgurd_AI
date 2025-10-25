# src/pull_outlook_and_score.py
import sys, json, requests, msal
from datetime import datetime

CLIENT_ID = "fc2d05ae-bf59-448f-90a3-fb288dfaa46d"  # <- your App (client) ID
# Personal Microsoft accounts (@outlook.com, @hotmail.com)
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Mail.Read"]

# Fetch latest 15 messages from Inbox with light fields only
API_ME_MESSAGES = (
    "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"
    "?$top=15&$orderby=receivedDateTime desc"
    "&$select=subject,from,bodyPreview,receivedDateTime,webLink"
)

PHISHGUARD_URL = "http://127.0.0.1:5000/predict"  # your local API

SEV_ICONS = {"high": "🚨 HIGH", "medium": "⚠️  MED", "low": "🟡 LOW", "safe": "✅ SAFE"}


def get_token_interactive():
    """Device Code flow sign-in for personal Microsoft accounts."""
    app = msal.PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError("Failed to create device flow. Response: %s" % json.dumps(flow, indent=2))
    print("\n== Sign in to Outlook ==", flush=True)
    print(flow["message"], flush=True)  # shows URL and code
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError("Could not obtain token: %s" % json.dumps(result, indent=2))
    return result["access_token"]


def fetch_recent_messages(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(API_ME_MESSAGES, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])


def score_with_phishguard(msg):
    subject = msg.get("subject") or ""
    sender = (msg.get("from") or {}).get("emailAddress", {}).get("address", "")
    body_preview = msg.get("bodyPreview") or ""
    payload = {"subject": subject, "from": sender, "body": body_preview}
    r = requests.post(PHISHGUARD_URL, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def fmt_dt(dt_str: str) -> str:
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str or ""


def main():
    try:
        token = get_token_interactive()
        msgs = fetch_recent_messages(token)
        if not msgs:
            print("No messages retrieved.")
            return

        print(f"\nScoring {len(msgs)} recent Inbox emails...\n")
        for i, m in enumerate(msgs, 1):
            res = score_with_phishguard(m)
            sev = res.get("severity", "safe")
            icon = SEV_ICONS.get(sev, "❓")
            subj = (m.get("subject") or "").strip()
            frm = (m.get("from", {}).get("emailAddress", {}).get("address", "")).strip()
            when = fmt_dt(m.get("receivedDateTime", ""))
            print(f"[{i}] {icon}  '{subj}'")
            print(f"    From: {frm}")
            print(f"    When: {when}")
            print(f"    Score: {res.get('score'):.3f}  Label: {res.get('label')}  Reasons: {res.get('reasons')}")
            wl = m.get("webLink")
            if wl:
                print(f"    Open: {wl}")
            print("-" * 90)

        # Simple summary counts
        counts = {"high": 0, "medium": 0, "low": 0, "safe": 0}
        for m in msgs:
            try:
                res = score_with_phishguard(m)
                counts[res.get("severity", "safe")] += 1
            except Exception:
                pass
        print("Summary:")
        for k in ("high", "medium", "low", "safe"):
            print(f"  {SEV_ICONS[k]}: {counts[k]}")

    except Exception as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
