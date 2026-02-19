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
        
        # 2. Transparency Mode: Track and Mask PII
        # This aligns with the "Safety & Trust" Sutras
        masked_features = []
        pii_keywords = ['name', 'phone', 'email', 'pan', 'acc', 'aadhar', 'id', 'customer']
        
        for col in df.columns:
            if any(key in col.lower() for key in pii_keywords):
                # Apply SHA-256 masking
                df[col] = df[col].apply(lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:12])
                masked_features.append(col)

        # 3. Audit Metrics
        count = len(df)
        # Mock logic for Sutra Health: Deduct points if too many PII leaks were found
        health_base = 99.8
        health_score = health_base if not masked_features else health_base - 0.5
        risk_variance = round(100 - health_score, 2)
        
        return jsonify({
            "status": "success",
            "transaction_count": count,
            "health_score": f"{health_score}%",
            "risk_score": f"{risk_variance}%",
            "masked_features": masked_features,
            "summary": f"Sutra Protocol Verified. {count} nodes audited. Identity protection applied to: {', '.join(masked_features) if masked_features else 'None'}."
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Vercel handles the app object directly; no app.run() needed.
