import pandas as pd
import numpy as np
import hashlib
import os
import hmac
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PEPPER = os.getenv("XPECT_PEPPER", "ARCHITECT_SECRET_999").encode()


def mask(value):
    return hmac.new(PEPPER, str(value).encode(), hashlib.sha256).hexdigest()[:16]


@app.route("/api/audit", methods=["POST"])
def audit():

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files["file"]

    try:
        df = pd.read_csv(file).dropna(how="all")
    except:
        return jsonify({"error": "Invalid CSV"}), 400

    if df.empty:
        return jsonify({"error": "Vault empty"}), 400

    amount_col = next(
        (c for c in df.columns if "amount" in c.lower() or "bal" in c.lower()),
        None,
    )

    if not amount_col:
        return jsonify({"error": "No amount column"}), 400

    vals = pd.to_numeric(df[amount_col], errors="coerce").dropna()

    health = round((vals.count() / len(df)) * 100, 2)
    risk = round(100 - health, 2)

    return jsonify({
        "status": "success",
        "audited_capacity": f"{health}%",
        "risk_score": f"{risk}%",
        "sutra_health": f"{health}%",
        "summary": "Protocol Green: System operational."
    })
