import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'ef_portal.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_1 TEXT NOT NULL,
        name_2 TEXT,
        dob_1 TEXT,
        dob_2 TEXT,
        ssn_last4_1 TEXT,
        ssn_last4_2 TEXT,
        monthly_salary REAL DEFAULT 0,
        monthly_expense_budget REAL DEFAULT 0,
        deductibles_total REAL DEFAULT 0,
        floor_amount REAL DEFAULT 1000,
        trust_address TEXT,
        zillow_value REAL DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        owner TEXT DEFAULT 'joint',
        account_type TEXT,
        institution TEXT,
        acct_last4 TEXT,
        is_retirement INTEGER DEFAULT 0,
        is_trust INTEGER DEFAULT 0,
        is_fica INTEGER DEFAULT 0,
        is_private_reserve INTEGER DEFAULT 0,
        is_investment INTEGER DEFAULT 0,
        is_inflow INTEGER DEFAULT 0,
        is_outflow INTEGER DEFAULT 0,
        current_balance REAL DEFAULT 0,
        cash_balance REAL,
        stale_data INTEGER DEFAULT 0,
        last_updated TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS liabilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        name TEXT,
        balance REAL DEFAULT 0,
        interest_rate REAL
    );
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        report_date TEXT,
        quarter TEXT,
        sacs_pdf_path TEXT,
        tcc_pdf_path TEXT,
        snapshot_data TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()

def age_from_dob(dob_str):
    if not dob_str:
        return None
    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d')
        today = datetime.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except:
        return None

def enrich_client(c):
    c = dict(c)
    c['age_1'] = age_from_dob(c.get('dob_1'))
    c['age_2'] = age_from_dob(c.get('dob_2'))
    c['display_name'] = f"{c['name_1']} & {c['name_2']}" if c.get('name_2') else c['name_1']
    return c

def enrich_with_accounts(c, accounts, liabilities, reports):
    ret1 = [a for a in accounts if a['is_retirement'] and a['owner'] == 'client1']
    ret2 = [a for a in accounts if a['is_retirement'] and a['owner'] == 'client2']
    non_ret = [a for a in accounts if not a['is_retirement'] and not a['is_trust']]
    trust_acct = next((a for a in accounts if a['is_trust']), None)
    c['accounts'] = accounts
    c['liabilities'] = liabilities
    c['reports'] = reports
    c['retirement_total_1'] = sum(a['current_balance'] or 0 for a in ret1)
    c['retirement_total_2'] = sum(a['current_balance'] or 0 for a in ret2)
    c['non_retirement_total'] = sum(a['current_balance'] or 0 for a in non_ret)
    trust_val = (trust_acct['current_balance'] or 0) if trust_acct else (c.get('zillow_value') or 0)
    c['trust_total'] = trust_val
    c['grand_total'] = c['retirement_total_1'] + c['retirement_total_2'] + c['non_retirement_total'] + trust_val
    c['liabilities_total'] = sum(l['balance'] or 0 for l in liabilities)
    c['excess_cashflow'] = (c['monthly_salary'] or 0) - (c['monthly_expense_budget'] or 0)
    c['private_reserve_calc_target'] = 6 * (c['monthly_expense_budget'] or 0) + (c['deductibles_total'] or 0)
    c['fica_account'] = next((a for a in accounts if a['is_fica']), None)
    c['private_reserve_account'] = next((a for a in accounts if a['is_private_reserve']), None)
    c['last_report_date'] = reports[0]['created_at'] if reports else None
    c['trust_account'] = trust_acct
    return c

def get_full_client(client_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    if not row:
        conn.close()
        return None
    c = enrich_client(row)
    accounts = [dict(a) for a in conn.execute(
        "SELECT * FROM accounts WHERE client_id=? ORDER BY is_retirement DESC, owner, account_type",
        (client_id,)).fetchall()]
    liabilities = [dict(l) for l in conn.execute(
        "SELECT * FROM liabilities WHERE client_id=?", (client_id,)).fetchall()]
    reports = [dict(r) for r in conn.execute(
        "SELECT * FROM reports WHERE client_id=? ORDER BY created_at DESC", (client_id,)).fetchall()]
    conn.close()
    return enrich_with_accounts(c, accounts, liabilities, reports)

def get_all_clients():
    conn = get_db()
    rows = conn.execute("SELECT * FROM clients ORDER BY name_1").fetchall()
    result = []
    for row in rows:
        c = enrich_client(row)
        accounts = [dict(a) for a in conn.execute(
            "SELECT * FROM accounts WHERE client_id=?", (row['id'],)).fetchall()]
        liabilities = [dict(l) for l in conn.execute(
            "SELECT * FROM liabilities WHERE client_id=?", (row['id'],)).fetchall()]
        reports = [dict(r) for r in conn.execute(
            "SELECT * FROM reports WHERE client_id=? ORDER BY created_at DESC LIMIT 1",
            (row['id'],)).fetchall()]
        result.append(enrich_with_accounts(c, accounts, liabilities, reports))
    conn.close()
    return result
