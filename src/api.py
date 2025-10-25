# src/api.py
from flask import Flask, request, jsonify
import joblib
from pathlib import Path
import pandas as pd

from preprocessing import extract_basic_features

# ----- config -----
ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "pipeline.joblib"

THRESHOLDS = {
    "high": 0.85,
    "medium": 0.70,
    "low": 0.50
}

def to_severity(p: float) -> str:
    if p >= THRESHOLDS["high"]:
        return "high"
    if p >= THRESHOLDS["medium"]:
        return "medium"
    if p >= THRESHOLDS["low"]:
        return "low"
    return "safe"

# ----- app & model load -----
app = Flask("phishguard_api")
print("Loading model...", MODEL_PATH)
clf = None
if MODEL_PATH.exists():
    clf = joblib.load(MODEL_PATH)
    print("Model loaded.")
else:
    print("Model not found. Please run src/train.py first.")

# ----- routes -----
@app.route("/", methods=["GET"])
def index():
    return (
        "<h2>PhishGuard API</h2>"
        "<p>Try <code>GET /health</code> or send JSON to <code>POST /predict</code>.</p>"
    )

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_loaded": clf is not None})

@app.route("/predict", methods=["POST"])
def predict():
    if not clf:
        return jsonify({"error": "model not loaded. Run src/train.py first."}), 500

    data = request.get_json(silent=True) or {}
    subject = data.get("subject", "") or ""
    sender  = data.get("from", "") or ""
    body    = data.get("body", "") or ""

    # Build handcrafted features
    f = extract_basic_features(subject, sender, body)
    payload = {
        "text_combined": f["subject"] + " " + f["body"],
        "suspicious_word_count": f["suspicious_word_count"],
        "has_ip": f["has_ip"],
        "has_link": f["has_link"]
    }

    # Predict
    X = pd.DataFrame([payload])
    proba = float(clf.predict_proba(X)[0, 1])
    severity = to_severity(proba)
    label = 1 if severity in ("high", "medium") else 0  # threat vs safe

    reasons = []
    if f["suspicious_word_count"] > 0:
        reasons.append("suspicious words found")
    if f["has_link"]:
        reasons.append("contains link")
    if f["has_ip"]:
        reasons.append("sender contains IP")

    return jsonify({
        "score": proba,
        "label": label,
        "severity": severity,
        "reasons": reasons
    })

if __name__ == "__main__":
    # Dev server - local only
    app.run(host="127.0.0.1", port=5000, debug=True)
