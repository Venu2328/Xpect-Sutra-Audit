from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)

@app.route("/api/audit", methods=["POST"])
def audit():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file"}), 400
    
    try:
        df = pd.read_csv(request.files["file"], engine='python').dropna(how="all")
        amt_col = next((c for c in df.columns if any(k in c.lower() for k in ['amt', 'amount', 'bal', 'val'])), None)
        
        if not amt_col:
            return jsonify({"status": "error", "message": "No financial column"}), 400

        vals = pd.to_numeric(df[amt_col], errors='coerce').fillna(0).values
        
        # 1000-Year Logic: Gini + Z-Score
        mean, std = np.mean(vals), np.std(vals)
        z_scores = (vals - mean) / std if std > 0 else np.zeros(len(vals))
        anomalies = np.sum(np.abs(z_scores) > 2.5)
        
        # Gini Calculation
        sorted_vals = np.sort(vals)
        n = len(vals)
        index = np.arange(1, n + 1)
        gini = ((np.sum((2 * index - n - 1) * sorted_vals)) / (n * np.sum(sorted_vals))) if np.sum(sorted_vals) > 0 else 0
        
        health = max(0, (1 - (anomalies / len(vals))) * 100 - (gini * 20))

        return jsonify({
            "status": "success",
            "metrics": {
                "health": f"{round(health, 1)}%",
                "risk": f"{round(100 - health, 1)}%",
                "vol": f"${np.sum(vals):,.0f}"
            },
            "analyst_report": {
                "concentration": "High Alert" if gini > 0.6 else "Stable" if gini < 0.3 else "Moderate",
                "velocity": f"Mean: ${round(mean, 2)} | Outliers: {anomalies}",
                "verdict": "INTEGRITY SECURE" if health > 80 else "STRUCTURAL RISK"
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        
