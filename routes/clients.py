from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort
from models.database import get_db, get_full_client, get_all_clients

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/')
def index():
    clients = get_all_clients()
    return render_template('index.html', clients=clients)

@clients_bp.route('/clients/new', methods=['GET','POST'])
def new_client():
    if request.method == 'POST':
        d = request.form
        conn = get_db()
        conn.execute("""INSERT INTO clients
            (name_1,name_2,dob_1,dob_2,ssn_last4_1,ssn_last4_2,
             monthly_salary,monthly_expense_budget,deductibles_total,
             floor_amount,trust_address,zillow_value)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
            d['name_1'], d.get('name_2',''), d.get('dob_1',''), d.get('dob_2',''),
            d.get('ssn_last4_1',''), d.get('ssn_last4_2',''),
            float(d.get('monthly_salary') or 0), float(d.get('monthly_expense_budget') or 0),
            float(d.get('deductibles_total') or 0), float(d.get('floor_amount') or 1000),
            d.get('trust_address',''), float(d.get('zillow_value') or 0),
        ))
        cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit(); conn.close()
        return redirect(url_for('clients.client_detail', client_id=cid))
    return render_template('client_form.html', client=None)

@clients_bp.route('/clients/<int:client_id>')
def client_detail(client_id):
    client = get_full_client(client_id)
    if not client: abort(404)
    return render_template('client_detail.html', client=client)

@clients_bp.route('/clients/<int:client_id>/edit', methods=['GET','POST'])
def edit_client(client_id):
    client = get_full_client(client_id)
    if not client: abort(404)
    if request.method == 'POST':
        d = request.form
        conn = get_db()
        conn.execute("""UPDATE clients SET
            name_1=?,name_2=?,dob_1=?,dob_2=?,ssn_last4_1=?,ssn_last4_2=?,
            monthly_salary=?,monthly_expense_budget=?,deductibles_total=?,
            floor_amount=?,trust_address=?,zillow_value=?,
            updated_at=datetime('now') WHERE id=?""", (
            d['name_1'], d.get('name_2',''), d.get('dob_1',''), d.get('dob_2',''),
            d.get('ssn_last4_1',''), d.get('ssn_last4_2',''),
            float(d.get('monthly_salary') or 0), float(d.get('monthly_expense_budget') or 0),
            float(d.get('deductibles_total') or 0), float(d.get('floor_amount') or 1000),
            d.get('trust_address',''), float(d.get('zillow_value') or 0), client_id,
        ))
        conn.commit(); conn.close()
        return redirect(url_for('clients.client_detail', client_id=client_id))
    return render_template('client_form.html', client=client)

@clients_bp.route('/clients/<int:client_id>/accounts', methods=['POST'])
def add_account(client_id):
    d = request.form
    flags = lambda f: 1 if f in d else 0
    conn = get_db()
    conn.execute("""INSERT INTO accounts
        (client_id,owner,account_type,institution,acct_last4,
         is_retirement,is_trust,is_fica,is_private_reserve,is_investment,
         is_inflow,is_outflow,current_balance,cash_balance)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        client_id, d.get('owner','joint'), d.get('account_type',''),
        d.get('institution',''), d.get('acct_last4',''),
        flags('is_retirement'), flags('is_trust'), flags('is_fica'),
        flags('is_private_reserve'), flags('is_investment'),
        flags('is_inflow'), flags('is_outflow'),
        float(d.get('current_balance') or 0),
        float(d['cash_balance']) if d.get('cash_balance') else None,
    ))
    conn.commit(); conn.close()
    return redirect(url_for('clients.client_detail', client_id=client_id))

@clients_bp.route('/clients/<int:client_id>/accounts/<int:acct_id>', methods=['POST'])
def update_account(client_id, acct_id):
    d = request.form
    conn = get_db()
    if d.get('_action') == 'delete':
        conn.execute("DELETE FROM accounts WHERE id=?", (acct_id,))
    else:
        cb = float(d['cash_balance']) if d.get('cash_balance') else None
        conn.execute("UPDATE accounts SET current_balance=?,cash_balance=?,last_updated=datetime('now') WHERE id=?",
                     (float(d.get('current_balance') or 0), cb, acct_id))
    conn.commit(); conn.close()
    return redirect(url_for('clients.client_detail', client_id=client_id))

@clients_bp.route('/clients/<int:client_id>/liabilities', methods=['POST'])
def add_liability(client_id):
    d = request.form
    conn = get_db()
    if d.get('_action') == 'delete':
        conn.execute("DELETE FROM liabilities WHERE id=?", (d.get('liability_id'),))
    else:
        conn.execute("INSERT INTO liabilities (client_id,name,balance,interest_rate) VALUES (?,?,?,?)", (
            client_id, d.get('name',''),
            float(d.get('balance') or 0),
            float(d['interest_rate']) if d.get('interest_rate') else None,
        ))
    conn.commit(); conn.close()
    return redirect(url_for('clients.client_detail', client_id=client_id))

@clients_bp.route('/api/clients/<int:client_id>/summary')
def client_summary(client_id):
    c = get_full_client(client_id)
    if not c: abort(404)
    return jsonify({
        'monthly_salary': c['monthly_salary'],
        'monthly_expense_budget': c['monthly_expense_budget'],
        'excess_cashflow': c['excess_cashflow'],
        'private_reserve_target': c['private_reserve_calc_target'],
        'retirement_total_1': c['retirement_total_1'],
        'retirement_total_2': c['retirement_total_2'],
        'non_retirement_total': c['non_retirement_total'],
        'trust_total': c['trust_total'],
        'grand_total': c['grand_total'],
        'liabilities_total': c['liabilities_total'],
    })
