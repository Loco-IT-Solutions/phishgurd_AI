# src/train.py
"""
Train a small demo model using synthetic data so you can test the pipeline locally.
This creates models/pipeline.joblib and models/model.joblib
"""
import os
import random
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

try:
    from .preprocessing import extract_basic_features
except ImportError:
    from src.preprocessing import extract_basic_features


ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)

# --- create synthetic dataset
phish_templates = [
    ("Your account has been suspended", "support@bank-example.com", "Please verify your password at http://bit.ly/fake"),
    ("Action required: Confirm payment", "billing@payments.example", "Click here to update your payment details"),
    ("Urgent: Reset your password", "security@mybank.example", "We detected unusual activity. Verify now"),
    ("Invoice attached", "invoices@company.example", "Please download the attached invoice and confirm payment"),
]

legit_templates = [
    ("Meeting notes", "colleague@company.local", "Please see meeting notes attached."),
    ("Your order has shipped", "orders@shop.example", "Your parcel #12345 is on the way"),
    ("Newsletter - October", "newsletter@trusted.example", "Here are the monthly updates and articles"),
    ("Event invite", "events@community.example", "You are invited to our annual event."),
]

rows = []
for _ in range(300):
    if random.random() < 0.45:
        subj, sender, body = random.choice(phish_templates)
        # small randomization
        body = body + " " + random.choice(["Please verify", "Verify now", "Click here"])
        label = 1
    else:
        subj, sender, body = random.choice(legit_templates)
        body = body + " " + random.choice(["Thanks", "See you", "Regards"])
        label = 0
    rows.append({"subject": subj, "from": sender, "body": body, "label": label})

df = pd.DataFrame(rows)
# --- feature extraction
features = df.apply(lambda r: extract_basic_features(r.subject, r["from"], r.body), axis=1)
f_df = pd.DataFrame(list(features))
f_df["text_combined"] = f_df["subject"] + " " + f_df["body"]
f_df["label"] = df["label"].values

# train/test split
X = f_df[["text_combined", "suspicious_word_count", "has_ip", "has_link"]]
y = f_df["label"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

# pipeline for text + numeric
text_pipe = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=2000, ngram_range=(1,2)))
])

from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import FunctionTransformer

def get_text(series):
    return series.values

# ColumnTransformer-like manual approach
from sklearn.compose import ColumnTransformer
preprocessor = ColumnTransformer([
    ("text", TfidfVectorizer(max_features=2000, ngram_range=(1,2)), "text_combined"),
    ("num", StandardScaler(), ["suspicious_word_count", "has_ip", "has_link"])
])

clf = Pipeline([
    ("pre", preprocessor),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))
])

clf.fit(X_train, y_train)
preds = clf.predict(X_test)
print(classification_report(y_test, preds))

# Save pipeline
joblib.dump(clf, MODELS_DIR / "pipeline.joblib")
print(f"Saved pipeline to {MODELS_DIR / 'pipeline.joblib'}")
