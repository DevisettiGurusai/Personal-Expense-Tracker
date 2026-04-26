import sqlite3
import pandas as pd

DB_PATH = "expenses.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_name TEXT,
            date TEXT,
            merchant TEXT,
            amount REAL,
            currency TEXT DEFAULT '$',
            category TEXT,
            type TEXT
        )
    ''')
    
    # Check if currency column exists (for migration)
    c.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in c.fetchall()]
    if 'currency' not in columns:
        c.execute("ALTER TABLE transactions ADD COLUMN currency TEXT DEFAULT '$'")
        
    conn.commit()
    conn.close()

def save_transactions(df, statement_name):
    conn = sqlite3.connect(DB_PATH)
    # Add statement_name column
    df_to_save = df.copy()
    df_to_save['statement_name'] = statement_name
    
    # ensure columns match DB
    cols = ['statement_name', 'Date', 'Merchant', 'Amount', 'Currency', 'Category', 'Type']
    # Check if all exist, if not, skip or fillna
    for col in cols:
        if col not in df_to_save.columns:
            df_to_save[col] = "$" if col == 'Currency' else None
            
    df_to_save = df_to_save[cols]
    # Rename for sqlite
    df_to_save.columns = ['statement_name', 'date', 'merchant', 'amount', 'currency', 'category', 'type']
    
    df_to_save.to_sql('transactions', conn, if_exists='append', index=False)
    conn.close()

def load_all_statements():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT DISTINCT statement_name FROM transactions", conn)
        statements = df['statement_name'].tolist()
    except:
        statements = []
    conn.close()
    return statements

def load_transactions(statement_names=None):
    conn = sqlite3.connect(DB_PATH)
    if not statement_names:
        df = pd.read_sql_query("SELECT * FROM transactions", conn)
    else:
        # Secure parameter binding for IN clause
        placeholders = ','.join(['?'] * len(statement_names))
        query = f"SELECT * FROM transactions WHERE statement_name IN ({placeholders})"
        df = pd.read_sql_query(query, conn, params=statement_names)
    conn.close()
    
    if not df.empty:
        # Capitalize for UI
        df.rename(columns={
            'statement_name': 'Statement Name',
            'date': 'Date',
            'merchant': 'Merchant',
            'amount': 'Amount',
            'currency': 'Currency',
            'category': 'Category',
            'type': 'Type'
        }, inplace=True)
    return df
