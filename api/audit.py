from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import hashlib
import hmac
import os

app = Flask(__name__)
CORS(app)

PEPPER = os.getenv("XPECT_PEPPER", "XPECT_SECURE_777").encode()

class XpectAnalyticalEngine:
    @staticmethod
    def calculate_gini(array):
        """Calculates the Gini coefficient for wealth/transaction concentration."""
        array = array.flatten()
        if np.any(array < 0): return 0
        array += 0.0000001 # prevent div by zero
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1)
        n = array.shape[0]
        return ((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array)))

    @classmethod
    def analyze(cls, file):
        try:
            df = pd.read_csv(file, engine='python').dropna(how="all")
            if df.empty: return {"status": "error", "message": "Zero nodes detected."}

            # Smart Column Mapping
            amt_col = next((c for c in df.columns if any(k in c.lower() for k in ['amt', 'amount', 'bal', 'val', 'debit'])), None)
            id_col = next((c for c in df.columns if any(k in c.lower() for k in ['id', 'cust', 'name', 'acc'])), df.columns[0])

            if not amt_col: return {"status": "error", "message": "No financial vector found."}

            vals = pd.to_numeric(df[amt_col], errors='coerce').fillna(0).values
            
            # 1. Advanced Risk (Z-Score & IQR Hybrid)
            mean, std = np.mean(vals), np.std(vals)
            z_scores = (vals - mean) / std if std > 0 else np.zeros(len(vals))
            anomalies = np.sum(np.abs(z_scores) > 2.5) # Points outside 2.5 Std Dev
            
            # 2. Wealth Concentration (Gini)
            gini_index = cls.calculate_gini(vals)
            concentration = "High" if gini_index > 0.7 else "Moderate" if gini_index > 0.4 else "Healthy"

            # 3. Capital Velocity
            total_vol = np.sum(vals)
            avg_txn = np.mean(vals)
            
            # 4. Integrity Score (Sutra Health)
            # Deducing score based on concentration risk and anomalies
            health_base = (1 - (anomalies / len(vals))) * 100
            health_final = max(0, health_base - (gini_index * 20))

            return {
                "status": "success",
                "metrics": {
                    "health": f"{round(health_final, 2)}%",
                    "risk": f"{round(100 - health_final, 2)}%",
                    "nodes": len(df),
                    "gini": round(gini_index, 3),
                    "vol": f"${total_vol:,.2f}"
                },
                "analyst_report": {
                    "concentration": f"{concentration} (Index: {round(gini_index, 2)})",
                    "velocity": f"Avg Flow: ${round(avg_txn, 2)} / Z-Anomaly Count: {anomalies}",
                    "verdict": cls.generate_verdict(health_final, anomalies)
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def generate_verdict(health, anomalies):
        if health > 85 and anomalies == 0: return "OPTIMAL: Structural integrity verified. No material variance."
        if health > 60: return "CAUTION: Minor concentration risks or outliers detected."
        return "CRITICAL: High volatility or significant capital concentration detected."

@app.route("/api/audit", methods=["POST"])
def audit():
    if "file" not in request.files: return jsonify({"status": "error", "message": "No file"}), 400
    result = XpectAnalyticalEngine.analyze(request.files["file"])
    return jsonify(result)
    
