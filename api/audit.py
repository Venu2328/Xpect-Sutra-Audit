from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import hashlib
import hmac
import os

app = Flask(__name__)
CORS(app)

# Fallback for secret key
PEPPER = os.getenv("XPECT_PEPPER", "ARCHITECT_SECRET_999").encode()

@app.route("/api/audit", methods=["POST"])
def audit():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    try:
        # Load data
        file = request.files["file"]
        df = pd.read_csv(file).dropna(how="all")
        
        if df.empty:
            return jsonify({"status": "error", "message": "Empty file"}), 400

        # Identify Columns
        cols = df.columns
        amount_col = next((c for c in cols if any(k in c.lower() for k in ['amount', 'bal', 'val'])), None)
        pii_cols = [c for c in cols if any(k in c.lower() for k in ['name', 'phone', 'email', 'acc', 'id', 'customer'])]

        if not amount_col:
            return jsonify({"status": "error", "message": "No amount column found"}), 400

        # 1. Mask PII
        for col in pii_cols:
            df[col] = df[col].apply(lambda x: hmac.new(PEPPER, str(x).encode(), hashlib.sha256).hexdigest()[:16])

        # 2. Risk Math
        vals = pd.to_numeric(df[amount_col], errors='coerce').dropna()
        total_rows = len(df)
        
        # IQR Anomaly Detection
        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
        iqr = q3 - q1
        upper_limit = q3 + (1.5 * iqr)
        
        anomalies = (vals > upper_limit).sum()
        risk_ratio = (vals[vals > upper_limit].sum() / vals.sum()) if vals.sum() > 0 else 0
        
        # 3. Final Health Score
        health = round((1 - risk_ratio) * 100, 2)
        risk = round(100 - health, 2)

        return jsonify({
            "status": "success",
            "audited_capacity": "100%",
            "risk_score": f"{risk}%",
            "sutra_health": f"{health}%",
            "summary": "Protocol Green: Integrity verified." if health > 80 else "Protocol Red: Risk detected."
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# DO NOT ADD app.run() HERE
