import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import json
import os
from dotenv import load_dotenv
import fitz  # PyMuPDF
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key and api_key != "YOUR_API_KEY_HERE":
    genai.configure(api_key=api_key)

# Set up page
st.set_page_config(page_title="Personal Expense Tracker", page_icon="💸", layout="wide")

st.markdown("""
<style>
.summary-card {
    background-color: #1a1b26;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}
.summary-title {
    color: #8c92ac;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.summary-value {
    font-size: 28px;
    font-weight: bold;
}
.income { color: #4ade80; }
.expense { color: #f87171; }
.balance-positive { color: #4ade80; }
.balance-negative { color: #f87171; }
</style>
""", unsafe_allow_html=True)

st.title("💸 Personal Expense Tracker (GenAI)")

# File Uploader
uploaded_files = st.file_uploader("Upload Receipts or Statements", type=["png", "jpg", "jpeg", "pdf", "csv"], accept_multiple_files=True)

def process_pdf(file_bytes):
    """Convert PDF pages to images using PyMuPDF"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    # Limit to first 5 pages to avoid massive token usage for huge statements
    max_pages = min(len(doc), 5)
    for page_num in range(max_pages):
        page = doc.load_page(page_num)
        # 2x zoom for better OCR
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def analyze_with_gemini(document_content):
    """Send images or CSV text to Gemini to extract structured JSON data."""
    model = genai.GenerativeModel('gemini-flash-latest')
    
    prompt = """
    You are an expert accountant and data extractor. Analyze the provided image(s) or raw CSV data of a receipt or bank statement.
    Extract all transactions found.
    For each transaction, provide exactly:
    - "Date": The date of the transaction (string, format YYYY-MM-DD if possible)
    - "Merchant": The name of the store or entity (string)
    - "Amount": The cost or amount spent (number, do not include currency symbols)
    - "Category": A categorized label (Choose ONLY from: Food & Dining, Groceries, Transport & Auto, Utilities, Entertainment, Shopping, Health & Medical, Housing, Insurance, Education, Personal Care, Subscriptions, Debt & Loans, Travel, Income/Refunds, Other). Try your best to categorize the item specifically; ONLY use 'Other' if absolutely necessary. (string)
    - "Type": The type of transaction (Choose ONLY from: Debit, Credit). 'Debit' is money spent/going out. 'Credit' is money received/coming in. (string)
    
    Return the result STRICTLY as a JSON array of objects. Do not include markdown formatting or any other text.
    Example output format:
    [
      {"Date": "2023-10-25", "Merchant": "Starbucks", "Amount": 5.50, "Category": "Food & Dining", "Type": "Debit"},
      {"Date": "2023-10-26", "Merchant": "Salary Deposit", "Amount": 1500.00, "Category": "Income/Refunds", "Type": "Credit"}
    ]
    """
    
    # Pass prompt and document content to the model
    if isinstance(document_content, list):
        contents = [prompt] + document_content
    else:
        contents = [prompt, document_content]
    
    response = model.generate_content(contents)
    return response.text

def generate_financial_advice(summary_data_text):
    """Ask Gemini for financial advice based on the parsed data."""
    model = genai.GenerativeModel('gemini-flash-latest')
    prompt = f"""
    You are an expert financial advisor. Review the following summary of a user's expenses and income:
    {summary_data_text}
    
    Please provide:
    1. A brief, 2-3 sentence summary of what happened this month (e.g., where most money went).
    2. 3 highly actionable, specific tips to save money based on these exact spending categories.
    
    Keep the tone encouraging and professional. Do not use markdown headers, just bullet points and bold text.
    """
    response = model.generate_content(prompt)
    return response.text

if uploaded_files:
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        st.error("⚠️ Please set your actual GEMINI_API_KEY in the `.env` file to use the AI features.")
    else:
        with st.spinner("Processing files..."):
            document_content = []
            csv_dataframes = []
            
            for uploaded_file in uploaded_files:
                if uploaded_file.name.lower().endswith(".csv"):
                    csv_text = uploaded_file.read().decode("utf-8")
                    document_content.append(f"CSV Content from {uploaded_file.name}:\n{csv_text}")
                    csv_dataframes.append(pd.read_csv(io.StringIO(csv_text)))
                elif uploaded_file.name.lower().endswith(".pdf"):
                    # Read bytes and process PDF
                    file_bytes = uploaded_file.read()
                    images = process_pdf(file_bytes)
                    document_content.extend(images)
                else:
                    # Process Image
                    image = Image.open(uploaded_file)
                    document_content.append(image)
            
            # Show previews
            with st.expander("View Uploaded Documents"):
                for df in csv_dataframes:
                    st.dataframe(df)
                for item in document_content:
                    if isinstance(item, Image.Image):
                        st.image(item, use_column_width=True)
            
            with st.spinner("Analyzing with Gemini AI..."):
                try:
                    result_text = analyze_with_gemini(document_content)
                    
                    # Clean up response (sometimes Gemini still outputs markdown blocks)
                    if result_text.startswith("```json"):
                        result_text = result_text[7:]
                    if result_text.startswith("```"):
                        result_text = result_text[3:]
                    if result_text.endswith("```"):
                        result_text = result_text[:-3]
                        
                    data = json.loads(result_text.strip())
                    
                    if not data:
                        st.warning("No transactions found or couldn't parse the document.")
                    else:
                        
                        # Convert to DataFrame
                        df = pd.DataFrame(data)
                        
                        # Ensure Amount is numeric
                        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
                        
                        summary_placeholder = st.container()
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.subheader("Extracted Transactions")
                            search_query = st.text_input("🔍 Search transactions (e.g., 'Food', 'Starbucks')")
                            st.caption("Editing the table or searching will dynamically update the charts and summaries.")
                            
                            if search_query:
                                mask = df.apply(lambda x: x.astype(str).str.contains(search_query, case=False, na=False)).any(axis=1)
                                display_df = df[mask]
                            else:
                                display_df = df
                                
                            # Editable dataframe so user can correct AI mistakes
                            edited_df = st.data_editor(display_df, num_rows="dynamic", use_container_width=True)
                            
                        with col2:
                            st.subheader("Expense Breakdown")
                            
                            # Filter for debits and credits
                            if 'Type' in edited_df.columns:
                                debit_df = edited_df[edited_df['Type'].str.upper() == 'DEBIT']
                                credit_df = edited_df[edited_df['Type'].str.upper() == 'CREDIT']
                            else:
                                debit_df = edited_df
                                credit_df = pd.DataFrame({'Amount': [0]})
                            
                            total_expenses = debit_df['Amount'].sum()
                            total_income = credit_df['Amount'].sum()
                            net_balance = total_income - total_expenses
                            
                            # Group by category
                            if not debit_df.empty and 'Category' in debit_df.columns:
                                category_sum = debit_df.groupby('Category')['Amount'].sum().reset_index()
                                
                                fig = px.pie(category_sum, values='Amount', names='Category', hole=0.4,
                                             color_discrete_sequence=px.colors.qualitative.Pastel)
                                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                                st.plotly_chart(fig, use_container_width=True)
                                
                        # Populate the summary at the top
                        balance_class = "balance-positive" if net_balance >= 0 else "balance-negative"
                        with summary_placeholder:
                            st.markdown("### 📊 Financial Summary")
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.markdown(f'''
                                <div class="summary-card">
                                    <div class="summary-title">TOTAL INCOME</div>
                                    <div class="summary-value income">${total_income:,.2f}</div>
                                </div>
                                ''', unsafe_allow_html=True)
                            with col_b:
                                st.markdown(f'''
                                <div class="summary-card">
                                    <div class="summary-title">TOTAL EXPENSES</div>
                                    <div class="summary-value expense">${total_expenses:,.2f}</div>
                                </div>
                                ''', unsafe_allow_html=True)
                            with col_c:
                                st.markdown(f'''
                                <div class="summary-card">
                                    <div class="summary-title">NET BALANCE</div>
                                    <div class="summary-value {balance_class}">${net_balance:,.2f}</div>
                                </div>
                                ''', unsafe_allow_html=True)
                            st.write("<br>", unsafe_allow_html=True)

                        st.divider()
                        st.subheader("📈 Monthly Expense Trend")
                        
                        if not debit_df.empty and 'Date' in debit_df.columns:
                            trend_df = debit_df.copy()
                            trend_df['Date'] = pd.to_datetime(trend_df['Date'], errors='coerce')
                            trend_df = trend_df.dropna(subset=['Date'])
                            
                            if not trend_df.empty:
                                trend_df['Month'] = trend_df['Date'].dt.to_period('M').astype(str)
                                monthly_expenses = trend_df.groupby('Month')['Amount'].sum().reset_index()
                                monthly_expenses = monthly_expenses.sort_values('Month')
                                
                                if len(monthly_expenses) > 0:
                                    fig_line = px.line(monthly_expenses, x='Month', y='Amount', markers=True,
                                                       labels={'Amount': 'Total Spent ($)', 'Month': 'Month'},
                                                       color_discrete_sequence=["#f87171"])
                                    fig_line.update_traces(marker=dict(size=8, color="#f87171"), line=dict(width=3))
                                    fig_line.update_layout(xaxis_type='category')
                                    st.plotly_chart(fig_line, use_container_width=True)
                                else:
                                    st.info("Not enough dates to show a monthly trend.")
                            else:
                                st.info("Could not parse dates to show a monthly trend.")
                        
                        st.divider()
                        st.subheader("💡 AI Financial Advisor")
                        st.write("Want personalized tips to save money based on your spending?")
                        if st.button("Generate Summary & Tips"):
                            with st.spinner("Analyzing your financial habits..."):
                                summary_str = f"Total Income: ${total_income:.2f}\nTotal Expenses: ${total_expenses:.2f}\nNet Balance: ${net_balance:.2f}\n\n"
                                if not debit_df.empty and 'Category' in debit_df.columns:
                                    cat_sum = debit_df.groupby('Category')['Amount'].sum()
                                    summary_str += "Expenses by Category:\n" + cat_sum.to_string()
                                
                                try:
                                    advice = generate_financial_advice(summary_str)
                                    st.success(advice)
                                except Exception as e:
                                    st.error(f"Failed to generate advice: {e}")
                                
                except json.JSONDecodeError:
                    st.error("Failed to parse the AI response. It might not be perfectly formatted JSON.")
                    with st.expander("Show Raw AI Output"):
                        st.write(result_text)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

else:
    st.info("👆 Please upload a receipt or bank statement to get started.")


