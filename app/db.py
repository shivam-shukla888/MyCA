import sqlite3
import os
import json
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DB_PATH = os.path.join(DB_DIR, "myca.db")

def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT DEFAULT 'client',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed default user Aarav Sharma
    cursor.execute("""
    INSERT OR IGNORE INTO users (id, name, email, role)
    VALUES ('usr_aarav_01', 'Aarav Sharma', 'aarav.sharma@sovereign.in', 'client');
    """)

    # Seed second user for isolation testing
    cursor.execute("""
    INSERT OR IGNORE INTO users (id, name, email, role)
    VALUES ('usr_priya_02', 'Priya Patel', 'priya.patel@sovereign.in', 'client');
    """)

    # 2. Documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type TEXT NOT NULL,
        num_pages INTEGER DEFAULT 0,
        doc_type TEXT DEFAULT 'bank_statement',
        status TEXT NOT NULL, -- UPLOADED, PROCESSING, EXTRACTED, VALIDATING, READY, NEEDS_REVIEW, FAILED
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 3. Document pages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_pages (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        page_number INTEGER NOT NULL,
        raw_text TEXT,
        has_images INTEGER DEFAULT 0,
        is_scanned INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 4. Document Extractions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_extractions (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        extraction_type TEXT NOT NULL,
        raw_data_json TEXT,
        confidence REAL DEFAULT 1.0,
        status TEXT DEFAULT 'VERIFIED_FROM_DOCUMENT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 5. Financial Accounts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_accounts (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        institution TEXT NOT NULL,
        account_type TEXT NOT NULL,
        masked_account_number TEXT NOT NULL,
        opening_balance REAL DEFAULT 0.0,
        closing_balance REAL DEFAULT 0.0,
        currency TEXT DEFAULT 'INR',
        source_document_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (source_document_id) REFERENCES documents(id) ON DELETE SET NULL
    );
    """)

    # 6. Transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        account_id TEXT,
        date TEXT NOT NULL,
        date_iso TEXT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL, -- 'CREDIT' or 'DEBIT'
        direction TEXT DEFAULT 'DEBIT', -- CREDIT, DEBIT, REFUND, REVERSAL, TRANSFER, NEEDS_REVIEW
        category TEXT NOT NULL,
        balance REAL,
        source_document_id TEXT NOT NULL,
        source_page INTEGER NOT NULL,
        source_text TEXT,
        status TEXT DEFAULT 'VERIFIED_FROM_DOCUMENT', -- VERIFIED_FROM_DOCUMENT, CALCULATED, USER_CONFIRMED, NEEDS_REVIEW, UNSUPPORTED
        confidence REAL DEFAULT 1.0,
        fingerprint TEXT,
        duplicate_status TEXT DEFAULT 'UNIQUE', -- UNIQUE, DUPLICATE_CONFIRMED, POSSIBLE_DUPLICATE
        duplicate_of_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (account_id) REFERENCES financial_accounts(id) ON DELETE SET NULL,
        FOREIGN KEY (source_document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # Non-destructive column additions for existing installations
    for col, col_type in [
        ("date_iso", "TEXT"),
        ("direction", "TEXT DEFAULT 'DEBIT'"),
        ("fingerprint", "TEXT"),
        ("duplicate_status", "TEXT DEFAULT 'UNIQUE'"),
        ("duplicate_of_id", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col} {col_type};")
        except sqlite3.OperationalError:
            pass  # Already exists

    # 7. Income records table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS income_records (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        source TEXT NOT NULL,
        date TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT DEFAULT 'SALARY',
        source_document_id TEXT NOT NULL,
        source_page INTEGER NOT NULL,
        status TEXT DEFAULT 'VERIFIED_FROM_DOCUMENT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (source_document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 8. Expense records table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expense_records (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        merchant TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        source_document_id TEXT NOT NULL,
        source_page INTEGER NOT NULL,
        status TEXT DEFAULT 'VERIFIED_FROM_DOCUMENT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (source_document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 9. Loans table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        lender TEXT NOT NULL,
        loan_type TEXT NOT NULL,
        principal REAL DEFAULT 0.0,
        emi_amount REAL DEFAULT 0.0,
        source_document_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 10. Investments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS investments (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        entity_name TEXT NOT NULL,
        amount REAL DEFAULT 0.0,
        source_document_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 11. Insurance policies table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insurance_policies (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        policy_type TEXT NOT NULL,
        premium REAL DEFAULT 0.0,
        source_document_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 12. Tax documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tax_documents (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        doc_type TEXT NOT NULL,
        assessment_year TEXT NOT NULL,
        total_tax_paid REAL DEFAULT 0.0,
        source_document_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 13. Document Processing Jobs table (lifecycle tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_processing_jobs (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        step TEXT NOT NULL, -- UPLOADED, VALIDATING, EXTRACTING, NORMALIZING, RECONCILING, COMPLETED, FAILED
        status TEXT NOT NULL, -- RUNNING, SUCCESS, FAILED, NEEDS_REVIEW
        progress_percent INTEGER DEFAULT 0,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 14. Audit Events table (Security & Provenance Tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        resource_id TEXT,
        details_json TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 15. Statutory Rules table (Versioned Statutory Knowledge Model)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS statutory_rules (
        id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        official_source_reference TEXT NOT NULL,
        publication_date TEXT NOT NULL,
        effective_from TEXT NOT NULL,
        effective_to TEXT,
        financial_year TEXT NOT NULL,
        assessment_year TEXT NOT NULL,
        provision TEXT NOT NULL,
        jurisdiction TEXT DEFAULT 'IN_CBDT',
        status TEXT NOT NULL, -- CURRENT, FUTURE, SUPERSEDED, NOT_VERIFIED
        rule_data_json TEXT NOT NULL,
        supersedes TEXT,
        superseded_by TEXT,
        last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Non-destructive column additions for statutory_rules
    for col, col_type in [
        ("topic", "TEXT DEFAULT 'INCOME_TAX'"),
        ("title", "TEXT"),
        ("content", "TEXT"),
        ("version", "INTEGER DEFAULT 1")
    ]:
        try:
            cursor.execute(f"ALTER TABLE statutory_rules ADD COLUMN {col} {col_type};")
        except sqlite3.OperationalError:
            pass  # Already exists

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database schema initialized successfully.")
