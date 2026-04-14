from flask import Blueprint, render_template, request, redirect, url_for, send_file, abort
from models.database import get_db, get_full_client
from pdf_generators.sacs_pdf import generate_sacs_pdf
from pdf_generators.tcc_pdf import generate_tcc_pdf
import os, json
from datetime import datetime

reports_bp = Blueprint('reports', __name__)
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

def _now_labels():
    now = datetime.today()
    q = ((now.month - 1) // 3) + 1
    months = ['January','February','March','April','May','June',
              'July','August','September','October','November','December']
    return (f"{months[now.month-1]} {now.day}, {now.year}", f"Q{q} {now.year}")

@reports_bp.route('/clients/<int:client_id>/generate', methods=['GET','POST'])
def generate_report(client_id):
    client = get_full_client(client_id)
    if not client: abort(404)
    now_date, now_quarter = _now_labels()

    if request.method == 'POST':
        d = request.form
        report_date = d.get('report_date', now_date)
        quarter = d.get('quarter', now_quarter)

        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sacs_path = os.path.join(REPORTS_DIR, f"SACS_{client_id}_{stamp}.pdf")
        tcc_path  = os.path.join(REPORTS_DIR, f"TCC_{client_id}_{stamp}.pdf")

        generate_sacs_pdf(client, report_date, quarter, sacs_path)
        generate_tcc_pdf(client, report_date, quarter, tcc_path)

        snapshot = json.dumps({
            'monthly_salary': client['monthly_salary'],
            'monthly_expense_budget': client['monthly_expense_budget'],
            'grand_total': client['grand_total'],
        })
        conn = get_db()
        conn.execute("""INSERT INTO reports (client_id,report_date,quarter,sacs_pdf_path,tcc_pdf_path,snapshot_data)
            VALUES (?,?,?,?,?,?)""", (client_id, report_date, quarter, sacs_path, tcc_path, snapshot))
        rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit(); conn.close()
        return redirect(url_for('reports.report_done', report_id=rid))

    return render_template('generate_report.html', client=client,
                           now_date=now_date, now_quarter=now_quarter)

@reports_bp.route('/reports/<int:report_id>')
def report_done(report_id):
    conn = get_db()
    report = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    conn.close()
    if not report: abort(404)
    report = dict(report)
    client = get_full_client(report['client_id'])
    return render_template('report_done.html', report=report, client=client)

@reports_bp.route('/reports/<int:report_id>/download/<string:rtype>')
def download_report(report_id, rtype):
    conn = get_db()
    report = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    conn.close()
    if not report: abort(404)
    report = dict(report)
    client = get_full_client(report['client_id'])
    if rtype == 'sacs':
        path = report['sacs_pdf_path']
        name = f"SACS_{client['display_name']}_{report['quarter']}.pdf"
    else:
        path = report['tcc_pdf_path']
        name = f"TCC_{client['display_name']}_{report['quarter']}.pdf"
    return send_file(path, as_attachment=True, download_name=name)

@reports_bp.route('/reports/<int:report_id>/view/<string:rtype>')
def view_report(report_id, rtype):
    conn = get_db()
    report = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    conn.close()
    if not report: abort(404)
    report = dict(report)
    client = get_full_client(report['client_id'])
    if rtype == 'sacs':
        path = report['sacs_pdf_path']
        name = f"SACS_{client['display_name']}_{report['quarter']}.pdf"
    else:
        path = report['tcc_pdf_path']
        name = f"TCC_{client['display_name']}_{report['quarter']}.pdf"
    return send_file(path, as_attachment=False, download_name=name, mimetype='application/pdf')