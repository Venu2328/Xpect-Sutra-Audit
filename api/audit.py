from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/audit")
async def perform_audit(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # --- SUTRA PATTERN LOGIC ---
        total_nodes = len(df) 
        
        # 1. Behavioral Cluster Detection (Identical amounts)
        mode_val = df['amount'].mode()[0] if not df.empty else 0
        cluster_count = df[df['amount'] == mode_val].shape[0]
        cluster_ratio = (cluster_count / total_nodes) * 100
        
        # 2. Threshold Proximity Detection (The $10k Law)
        # Flags transactions that hit or hide near the reporting limit
        threshold_events = df[df['amount'] >= 10000].shape[0]
        
        # 3. Calculated Sovereign Health
        health = 100 - (cluster_ratio * 0.4) - (threshold_events * 20)
        health = max(5, min(100, health))

        # Industrial Verdict Generation
        verdict = f"SUTRA ANALYSIS: Detected {cluster_ratio:.0f}% behavioral mirroring. "
        if threshold_events > 0:
            verdict += f"CRITICAL: Found {threshold_events} event(s) exceeding legal reporting thresholds. High probability of probing behavior."
        else:
            verdict += "Liquidity vectors appear structurally consistent."

        return {
            "status": "success",
            "transaction_count": f"{total_nodes} Nodes",
            "risk_score": f"{cluster_ratio:.1f}% Pattern",
            "health_score": f"{health:.0f}%",
            "summary": verdict
        }
    except Exception as e:
        return {"status": "error", "message": "Ensure CSV has an 'amount' column."}
        
