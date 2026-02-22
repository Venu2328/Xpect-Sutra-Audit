import pandas as pd
import numpy as np
import hashlib
import os
import hmac
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Secret key for hashing
PEPPER = os.getenv("XPECT_PEPPER", "ARCHITECT_SECRET_999").encode()

class XpectEngine:
    @staticmethod
    def identify_cols(df):
        return {
            'amount': next((c for c in df.columns if any(k in c.lower() for k in ['amount', 'bal', 'val'])), None),
            'pii': [c for c in df.columns if any(k in c.lower() for k in ['name', 'phone', 'email', 'acc', 'id', 'customer'])]
        }

    @classmethod
    def run_audit(cls, file):
        df = pd.read_csv(file).dropna(how="all")
        if df.empty: return {"error": "Vault empty"}
        
        schema = cls.identify_cols(df)
        if not schema['amount']: return {"error": "No amount column found"}

        # Masking
        for col in schema['pii']:
            df[col] = df[col].apply(lambda x: hmac.new(PEPPER, str(x).encode(), hashlib.sha256).hexdigest()[:16])

        # Logic
        vals = pd.to_numeric(df[schema['amount']], errors='coerce').dropna()
        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr
        
        anomaly_val = vals[vals > upper].sum()
        total_val = vals.sum()
        risk_ratio = anomaly_val / total_val if total_val else 0
        
        health = round((1 - risk_ratio) * 100, 2)
        
        return {
            "status": "success",
            "audited_capacity": "100%",
            "risk_score": f"{round(100 - health, 2)}%",
            "sutra_health": f"{health}%",
            "summary": "Protocol Green: Integrity verified." if health > 80 else "Protocol Red: Risk detected."
        }

@app.route("/api/audit", methods=["POST"])
def audit():
    if "file" not in request.files: return jsonify({"error": "No file"}), 400
    return jsonify(XpectEngine.run_audit(request.files["file"]))
  
