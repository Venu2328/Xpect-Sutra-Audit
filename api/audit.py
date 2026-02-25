from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import hashlib
import hmac
import os

app = Flask(__name__)
CORS(app)

# Security Pepper
PEPPER = os.getenv("XPECT_PEPPER", "ARCHITECT_SECRET_999").encode()

@app.route("/api/audit", methods=["POST"])
def audit():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    try:
        file = request.files["file"]
        df = pd.read_csv(file, engine='python', skip_blank_lines=True).dropna(how="all")
        
        if df.empty:
            return jsonify({"status": "error", "message": "Vault empty"}), 400

        # Identify Columns
        cols = df.columns
        amount_col = next((c for c in cols if any(k in c.lower() for k in ['amount', 'bal', 'val'])), None)
        pii_cols = [c for c in cols if any(k in c.lower() for k in ['name', 'phone', 'email', 'acc', 'id', 'customer'])]

        if not amount_col:
            return jsonify({"status": "error", "message": "No amount column found"}), 400

        # 1. Mask PII using HMAC-SHA256
        for col in pii_cols:
            df[col] = df[col].apply(lambda x: hmac.new(PEPPER, str(x).encode(), hashlib.sha256).hexdigest()[:16])

        # 2. Advanced Risk Math (IQR Method)
        vals = pd.to_numeric(df[amount_col], errors='coerce').dropna()
        if vals.empty:
            return jsonify({"status": "error", "message": "Financial column contains no numeric data"}), 400
            
        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
        iqr = q3 - q1
        upper_limit = q3 + (1.5 * iqr)
        
        anomaly_sum = vals[vals > upper_limit].sum()
        total_sum = vals.sum()
        risk_ratio = (anomaly_sum / total_sum) if total_sum > 0 else 0
        
        # 3. Final Health Score Calculation
        health = round((1 - risk_ratio) * 100, 2)
        risk = round(100 - health, 2)

        # Mapping keys exactly to match Frontend expectations
        return jsonify({
            "status": "success",
            "audited_capacity": "100%",
            "risk_score": f"{risk}%",
            "sutra_health": f"{health}%",
            "verdict": "Protocol Green: Integrity verified." if health > 80 else "Protocol Red: Risk detected.",
            "summary": f"Audit complete. Processed {len(df)} nodes. {len(pii_cols)} vectors masked."
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        
