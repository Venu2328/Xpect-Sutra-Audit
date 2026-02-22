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


class XpectEngine:

    @staticmethod
    def identify_financial_columns(df):
        cols = {
            'amount': next((c for c in df.columns if any(k in c.lower()
                        for k in ['amount', 'val', 'bal', 'debit', 'credit'])), None),

            'pii': [c for c in df.columns if any(k in c.lower()
                    for k in ['name', 'phone', 'email', 'acc', 'id',
                              'aadhar', 'pan', 'customer'])]
        }
        return cols

    @staticmethod
    def mask_pii(df, pii_cols):
        for col in pii_cols:
            df[col] = df[col].apply(
                lambda x: hmac.new(PEPPER, str(x).encode(),
                                   hashlib.sha256).hexdigest()[:16]
            )
        return df

    @staticmethod
    def fintech_risk_model(df, amount_col):

        total_rows = len(df)

        vals = pd.to_numeric(df[amount_col], errors='coerce')

        valid_rows = vals.notna().sum()
        audited_capacity = valid_rows / total_rows if total_rows else 0

        vals = vals.dropna()

        total_value = vals.sum()

        # ---------- IQR anomaly detection ----------
        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr

        anomaly_mask = vals > upper
        anomalies = anomaly_mask.sum()

        anomaly_value = vals[anomaly_mask].sum()

        risk_ratio = anomaly_value / total_value if total_value else 0

        # ---------- Duplicate ratio ----------
        duplicate_ratio = df.duplicated().sum() / total_rows if total_rows else 0

        data_integrity = 1 - duplicate_ratio

        # ---------- Composite health score ----------
        health = (
            audited_capacity * 35 +
            (1 - risk_ratio) * 35 +
            data_integrity * 20 +
            (1 - duplicate_ratio) * 10
        )

        risk = 100 - health

        return {
            "audited_capacity": round(audited_capacity * 100, 2),
            "risk_ratio": round(risk_ratio * 100, 2),
            "duplicate_ratio": round(duplicate_ratio * 100, 2),
            "anomaly_count": int(anomalies),
            "health": round(health, 2),
            "risk": round(risk, 2)
        }

    @staticmethod
    def verdict(health):
        if health > 90:
            return "Protocol Green: Low operational and transactional risk."
        elif health > 70:
            return "Protocol Yellow: Moderate anomaly exposure. Review recommended."
        else:
            return "Protocol Red: Material audit risk detected. Immediate attention required."

    @classmethod
    def audit(cls, file_stream):

        try:
            df = pd.read_csv(file_stream, skip_blank_lines=True, engine='python').dropna(how='all')
        except Exception:
            file_stream.seek(0)
            df = pd.read_csv(file_stream, encoding='latin1', skip_blank_lines=True)

        if df.empty:
            return {"status": "error", "message": "Vault empty."}

        schema = cls.identify_financial_columns(df)

        if not schema['amount']:
            return {"status": "error", "message": "No financial amount column detected."}

        df = cls.mask_pii(df, schema['pii'])

        metrics = cls.fintech_risk_model(df, schema['amount'])

        return {
            "status": "success",
            "transaction_count": len(df),

            "sutra_health": f"{metrics['health']}%",
            "risk_score": f"{metrics['risk']}%",

            "audited_capacity": f"{metrics['audited_capacity']}%",
            "transaction_risk_ratio": f"{metrics['risk_ratio']}%",
            "duplicate_ratio": f"{metrics['duplicate_ratio']}%",

            "anomaly_count": metrics['anomaly_count'],
            "masked_features": schema['pii'],

            "summary": cls.verdict(metrics['health'])
        }


@app.route('/api/audit', methods=['POST'])
def audit_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400

    try:
        return jsonify(XpectEngine.audit(request.files['file']))
    except Exception as e:
        return jsonify({"error": f"System Fault: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(threaded=True, port=5000)
