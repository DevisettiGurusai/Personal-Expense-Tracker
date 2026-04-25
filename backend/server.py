from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
import pandas as pd
import io

from database import init_db, save_transactions, load_all_statements, load_transactions
from ai_processor import is_ai_configured, extract_text_from_pdf, extract_text_from_image, analyze_with_groq, generate_financial_advice

app = FastAPI(title="Expense Tracker API")

# Enable CORS for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
init_db()

# Check key on startup
if is_ai_configured():
    print("✅ Backend: GROQ_API_KEY detected successfully.")
else:
    print("❌ Backend: GROQ_API_KEY NOT found. Please check your .env file.")

@app.get("/health")
def health_check():
    return {"status": "healthy", "ai_configured": is_ai_configured()}

@app.get("/statements")
def get_statements():
    return {"statements": load_all_statements()}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    if not is_ai_configured():
        raise HTTPException(status_code=500, detail="AI API Key not configured")
    
    document_content = []
    
    for file in files:
        content = await file.read()
        if file.filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(content)
            document_content.append(f"PDF Content from {file.filename}:\n{text}")
        elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            # Convert bytes to file-like object for PIL
            text = extract_text_from_image(io.BytesIO(content))
            document_content.append(f"Image Content from {file.filename}:\n{text}")
            
    if not document_content:
        raise HTTPException(status_code=400, detail="No valid PDF or Image files found")
        
    try:
        result_text = analyze_with_groq(document_content)
        
        # Clean JSON markdown if present
        if result_text.startswith("```json"): result_text = result_text[7:]
        if result_text.startswith("```"): result_text = result_text[3:]
        if result_text.endswith("```"): result_text = result_text[:-3]
        
        data = json.loads(result_text.strip())
        
        if not data:
            raise HTTPException(
                status_code=400, 
                detail="The uploaded document does not appear to contain any valid financial transactions. Please upload a receipt or bank statement."
            )
            
        return {"transactions": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save")
async def save_data(data: dict):
    # Expects {"statement_name": "...", "transactions": [...]}
    statement_name = data.get("statement_name")
    transactions = data.get("transactions")
    
    if not statement_name or not transactions:
        raise HTTPException(status_code=400, detail="Missing statement_name or transactions")
        
    try:
        df = pd.DataFrame(transactions)
        save_transactions(df, statement_name)
        return {"message": f"Successfully saved {len(transactions)} transactions"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dashboard")
async def get_dashboard_data(data: dict):
    # Expects {"selected_statements": [...]}
    selected = data.get("selected_statements", [])
    if not selected:
        return {"summary": {}, "transactions": [], "charts": {}}
        
    try:
        df = load_transactions(selected)
        if df.empty:
            return {"summary": {}, "transactions": [], "charts": {}}
            
        # Ensure Amount is numeric
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        
        # Calculate summary
        debit_df = df[df['Type'].str.upper() == 'DEBIT']
        credit_df = df[df['Type'].str.upper() == 'CREDIT']
        
        total_expenses = float(debit_df['Amount'].sum())
        total_income = float(credit_df['Amount'].sum())
        net_balance = total_income - total_expenses
        
        # Category breakdown for pie chart
        category_data = debit_df.groupby('Category')['Amount'].sum().reset_index().to_dict(orient='records')
        
        # Trend data
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        trend_df = df.dropna(subset=['Date'])
        trend_data = []
        if not trend_df.empty:
            trend_df['Month'] = trend_df['Date'].dt.to_period('M').astype(str)
            monthly = trend_df[trend_df['Type'].str.upper() == 'DEBIT'].groupby('Month')['Amount'].sum().reset_index()
            trend_data = monthly.sort_values('Month').to_dict(orient='records')

        return {
            "summary": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_balance": net_balance
            },
            "transactions": df.to_dict(orient='records'),
            "charts": {
                "categories": category_data,
                "trend": trend_data
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/advice")
async def get_advice(data: dict):
    # Expects {"summary_text": "..."}
    summary_text = data.get("summary_text")
    if not summary_text:
        raise HTTPException(status_code=400, detail="Missing summary_text")
        
    try:
        advice = generate_financial_advice(summary_text)
        return {"advice": advice}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
