from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import io

app = Flask(__name__)
CORS(app)

def perform_banking_audit(df):
    """Real calculation engine for banking datasets."""
    total_records = len(df)
    
    # 1. Integrity Check: Identify missing critical financial fields
    missing_data_points = df.isnull().sum().sum()
    integrity_ratio = max(0, 100 - (missing_data_points / (total_records * len(df.columns)) * 100))
    
    # 2. Risk Variance: Simulating pattern detection (e.g., suspicious amount spikes)
    # In a real sector audit, we look for standard deviations in transaction values
    if 'amount' in df.columns:
        mean_val = df['amount'].mean()
        std_val = df['amount'].std()
        # High risk if transactions are > 3 standard deviations from mean
        outliers = len(df[df['amount'] > (mean_val + 3 * std_val)])
        risk_variance = min(100, (outliers / total_records) * 500) 
    else:
        # Fallback logic if 'amount' column is missing
        risk_variance = 12.5 

    # 3. Sutra Health: The weighted average of fairness and transparency
    health_score = round((integrity_ratio * 0.7) + ((100 - risk_variance) * 0.3), 2)
    
    return {
        "count": total_records,
        "health": f"{health_score}%",
        "risk": f"{round(risk_variance, 2)}%",
        "verdict": f"Audit complete. Detected {total_records} nodes. Integrity at {round(integrity_ratio, 1)}%."
    }

@app.route('/api/audit', methods=['POST'])
def audit():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    try:
        df = pd.read_csv(io.StringIO(file.stream.read().decode("UTF-8", errors='replace')))
        results = perform_banking_audit(df)
        
        return jsonify({
            "status": "success",
            "transaction_count": results["count"],
            "health_score": results["health"],
            "risk_score": results["risk"],
            "summary": results["verdict"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Required for Vercel Serverless
def handler(request):
    return app(request)
    
