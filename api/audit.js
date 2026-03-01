from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import io
import hashlib

app = Flask(__name__)
CORS(app)

@app.route('/api/audit', methods=['POST'])
def audit_transactions():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    
    file = request.files['file']
    try:
        # 1. Read the data
        raw_content = file.stream.read().decode("UTF-8", errors='replace')
        df = pd.read_csv(io.StringIO(raw_content))
        
        # 2. Sutra Masking logic
        masked_features = []
        pii_keywords = ['name', 'phone', 'email', 'pan', 'acc', 'aadhar', 'id', 'customer']
        for col in df.columns:
            if any(key in col.lower() for key in pii_keywords):
                df[col] = df[col].apply(lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:12])
                masked_features.append(col)

        # 3. ADVANCED STRESS TEST (The "Brain" update)
        # We calculate health based on actual data patterns now
        count = len(df)
        risk_deductions = 0
        
        # Check for potential duplicates (High risk in banking)
        if df.duplicated().any():
            risk_deductions += 5
            
        # Check for "Transaction Spikes" if an 'Amount' column exists
        amount_col = next((c for c in df.columns if 'amount' in c.lower() or 'val' in c.lower()), None)
        if amount_col:
            # If any transaction is 5x the average, it's a risk variance
            avg_val = df[amount_col].mean()
            if (df[amount_col] > (avg_val * 5)).any():
                risk_deductions += 7

        health_val = max(75, 99.8 - risk_deductions)
        risk_val = round(100 - health_val, 2)
        
        return jsonify({
            "status": "success",
            "transaction_count": count,
            "health_score": f"{health_val}%",
            "risk_score": f"{risk_val}%",
            "masked_features": masked_features,
            "summary": f"Sutra Audit Complete. Detected {len(masked_features)} sensitive nodes. Risk variance identified in structural patterns: {risk_val}%."
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        
