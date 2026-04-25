import os
import io
import json
import pdfplumber
import pytesseract
from PIL import Image
from groq import Groq
from dotenv import load_dotenv

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def get_api_key():
    load_dotenv(override=True)
    return os.getenv("GROQ_API_KEY")

def is_ai_configured():
    key = get_api_key()
    return bool(key and key != "YOUR_API_KEY_HERE")

def extract_text_from_pdf(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        max_pages = min(len(pdf.pages), 5)
        for page in pdf.pages[:max_pages]:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_image(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        # Using PSM 6 to assume a single uniform block of text, which helps with tables
        text = pytesseract.image_to_string(image, config='--psm 6')
        return text
    except Exception as e:
        return f"OCR Error: {str(e)}"

def analyze_with_groq(document_content):
    key = get_api_key()
    if not key or key == "YOUR_API_KEY_HERE":
        raise ValueError("GROQ_API_KEY not configured in .env")
        
    client = Groq(api_key=key)
        
    prompt = """
    You are an expert accountant and data extractor. Analyze the provided raw text of a receipt or bank statement.
    
    IMPORTANT RULES FOR EXTRACTION:
    1. IF IT IS A BANK/CREDIT CARD STATEMENT: 
       - You MUST extract EVERY SINGLE transaction row found in the document. Do not miss any.
       - Do NOT just output the first or last row. Output an array containing ALL transactions.
       - Ignore the running "Balance" column. The "Amount" should ONLY be the actual Withdrawal (Debit) or Deposit (Credit) value for that specific transaction, NOT the total account balance.
       - The text is from OCR and may have columns merged together. Use your best judgment to separate the Date, Description/Merchant, and Amount.
    2. IF IT IS A SINGLE RECEIPT (like a restaurant or store bill): 
       - Do NOT itemize the individual purchases. 
       - Extract exactly ONE transaction representing the final GRAND TOTAL paid (this MUST include all taxes, tips, and delivery fees).
    
    For each transaction, provide exactly:
    - "Date": The date of the transaction (string, format YYYY-MM-DD if possible)
    - "Merchant": The name of the store or entity (string)
    - "Amount": The final net cost or amount spent (number, do not include currency symbols)
    - "Category": A categorized label (Choose ONLY from: Food & Dining, Groceries, Transport & Auto, Utilities, Entertainment, Shopping, Health & Medical, Housing, Insurance, Education, Personal Care, Subscriptions, Debt & Loans, Travel, Income/Refunds, Other). Try your best to categorize the item specifically; ONLY use 'Other' if absolutely necessary. (string)
    - "Type": The type of transaction (Choose ONLY from: Debit, Credit). 'Debit' is money spent/going out. 'Credit' is money received/coming in. (string)
    
    IF THE TEXT DOES NOT APPEAR TO BE A RECEIPT, INVOICE, OR BANK STATEMENT, OR IF NO TRANSACTIONS CAN BE FOUND, YOU MUST RETURN AN EMPTY ARRAY []. 
    Do not guess or hallucinate transactions if they are not clearly present.

    Return the result STRICTLY as a JSON array of objects. Do not include markdown formatting or any other text.
    Example output format:
    [
      {"Date": "2023-10-25", "Merchant": "Starbucks", "Amount": 5.50, "Category": "Food & Dining", "Type": "Debit"}
    ]
    """
    
    combined_text = "\n\n".join(document_content).strip()
    
    # Simple check for meaningless content
    if not combined_text or len(combined_text) < 10 or "OCR Error" in combined_text:
        return "[]"

    full_prompt = f"{prompt}\n\nRAW EXTRACTED TEXT:\n{combined_text}"
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": full_prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=8192
    )
    return response.choices[0].message.content

def generate_financial_advice(summary_data_text):
    key = get_api_key()
    if not key or key == "YOUR_API_KEY_HERE":
        raise ValueError("GROQ_API_KEY not configured in .env")
        
    client = Groq(api_key=key)
        
    prompt = f"""
    You are an expert financial advisor. Review the following summary of a user's expenses and income:
    {summary_data_text}
    
    Please provide:
    1. A brief, 2-3 sentence summary of what happened this month (e.g., where most money went).
    2. 3 highly actionable, specific tips to save money based on these exact spending categories.
    
    Keep the tone encouraging and professional. Do not use markdown headers, just bullet points and bold text.
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.7
    )
    return response.choices[0].message.content
