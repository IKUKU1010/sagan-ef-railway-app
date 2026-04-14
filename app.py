from flask import Flask
from models.database import init_db, get_db
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ef-portal-secret-2024'

    from routes.clients import clients_bp
    from routes.reports import reports_bp
    app.register_blueprint(clients_bp)
    app.register_blueprint(reports_bp)

    init_db()
    seed_sample_data()
    return app


def seed_sample_data():
    conn = get_db()
    if conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0] > 0:
        conn.close()
        return

    conn.execute("""INSERT INTO clients
        (name_1,name_2,dob_1,dob_2,ssn_last4_1,ssn_last4_2,
         monthly_salary,monthly_expense_budget,deductibles_total,floor_amount,
         trust_address,zillow_value)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        ('John','Jane','1975-03-15','1978-07-22','4521','8834',
         15000,12000,3000,1000,'123 Peachtree St, Atlanta GA',450000))
    
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    accounts = [
        (cid,'client1','ROTH IRA','Charles Schwab','1234',1,0,0,0,0,0,0,11162.47,316),
        (cid,'client1','IRA','Charles Schwab','5678',1,0,0,0,0,0,0,0,None),
        (cid,'client2','IRA','Charles Schwab','9012',1,0,0,0,0,0,0,37232.46,914),
        (cid,'client2','ROTH IRA','Charles Schwab','3456',1,0,0,0,0,0,0,18885.92,508),
        (cid,'client2','401K','Employer','7890',1,0,0,0,0,0,0,70042,None),
        (cid,'joint','Main Checking','Wells Fargo','1111',0,0,0,0,0,1,0,448.26,None),
        (cid,'joint','Savings','Wells Fargo','2222',0,0,0,0,0,0,0,44024,None),
        (cid,'joint','FICA','StoneCastle','3333',0,0,1,0,0,0,0,44067.78,None),
        (cid,'joint','Joint TEN','Schwab','4444',0,0,0,0,1,0,0,0,None),
        (cid,'joint','Inflow','Pinnacle','5555',0,0,0,0,0,1,0,990,None),
        (cid,'joint','Outflow','Pinnacle','6666',0,0,0,0,0,0,1,12990,None),
        (cid,'joint','Private Reserve','Pinnacle','7777',0,0,0,1,0,0,0,86785,None),
        (cid,'joint','Family Trust','','8888',0,1,0,0,0,0,0,0,None),
    ]

    conn.executemany("""INSERT INTO accounts
        (client_id,owner,account_type,institution,acct_last4,
         is_retirement,is_trust,is_fica,is_private_reserve,is_investment,
         is_inflow,is_outflow,current_balance,cash_balance)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", accounts)

    liabilities = [
        (cid,'P Morg',224218.34,None),(cid,'S Morg',107987.31,None),
        (cid,'Mercedes',11152.00,None),(cid,'GMC Sierra',26950.00,None),
        (cid,'Escalade',31627.52,None),(cid,'PNC',14028.00,None),
        (cid,'Health',1447.00,None),
    ]

    conn.executemany(
        "INSERT INTO liabilities (client_id,name,balance,interest_rate) VALUES (?,?,?,?)",
        liabilities
    )

    conn.commit()
    conn.close()


# 🔥 THIS LINE IS CRITICAL FOR GUNICORN
app = create_app()


# 👇 ONLY for local development (not used by Railway)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)