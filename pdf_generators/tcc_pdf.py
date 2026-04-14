from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import math
from pdf_generators import wrap

# Brand colors
DARK_BLUE   = colors.HexColor('#1B3A5C')
MED_BLUE    = colors.HexColor('#2C5F8A')
LIGHT_BLUE  = colors.HexColor('#4A90C4')
PALE_BLUE   = colors.HexColor('#D6E8F5')
GREEN       = colors.HexColor('#4A8C3F')
LIGHT_GREEN = colors.HexColor('#6AAF5A')
DARK_GREEN  = colors.HexColor('#2D5A27')
GRAY_BOX    = colors.HexColor('#4A4A4A')
LIGHT_GRAY  = colors.HexColor('#CCCCCC')
PALE_GRAY   = colors.HexColor('#F5F5F5')
WHITE       = colors.white
GRAY        = colors.HexColor('#666666')
RED         = colors.HexColor('#C0392B')
AMBER       = colors.HexColor('#E67E22')

def fmt_money(v, show_cent=True):
    if v is None: return '$0.00'
    if show_cent:
        return f"${v:,.2f}"
    return f"${v:,.0f}"

def draw_header(c, client, report_date, quarter, page_w, page_h):
    # Header bar
    c.setFillColor(DARK_BLUE)
    c.rect(0, page_h - 0.7*inch, page_w, 0.7*inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 17)
    c.setFillColor(WHITE)
    c.drawCentredString(page_w/2, page_h - 0.45*inch, "Total Client Chart (TCC)")

    # Info bar
    c.setFillColor(PALE_BLUE)
    c.rect(0, page_h - 1.15*inch, page_w, 0.45*inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(DARK_BLUE)
    c.drawString(0.4*inch, page_h - 0.88*inch, f"NAME: {client.display_name}")
    c.drawString(0.4*inch, page_h - 1.02*inch + 2, f"DATE: {report_date}")
    c.drawRightString(page_w - 0.4*inch, page_h - 0.88*inch, f"GRAND TOTAL")
    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(DARK_BLUE)
    c.drawRightString(page_w - 0.4*inch, page_h - 1.02*inch + 2, fmt_money(client.grand_total))

def draw_oval(c, cx, cy, rx, ry, fill_color, stroke_color=None, lw=1.5):
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(lw)
    c.ellipse(cx-rx, cy-ry, cx+rx, cy+ry, stroke=1 if stroke_color else 0, fill=1)

def draw_account_bubble(c, cx, cy, rx, ry, acct, small=False):
    """Draw account info inside an oval bubble"""
    draw_oval(c, cx, cy, rx, ry, WHITE, DARK_BLUE, 1.5)

    fs_type = 8 if small else 9
    fs_bal  = 9 if small else 10
    fs_acct = 7 if small else 8

    lines = []
    if acct.acct_last4:
        lines.append(('Helvetica', fs_acct, f"ACCT #{acct.acct_last4}", GRAY))
    lines.append(('Helvetica-Bold', fs_type, acct.account_type, DARK_BLUE))
    if acct.institution:
        lines.append(('Helvetica', fs_acct, acct.institution, GRAY))
    lines.append(('Helvetica-Bold', fs_bal, fmt_money(acct.current_balance), DARK_BLUE))
    if acct.last_updated:
        try:
            from datetime import datetime as _dt
            lu = acct.last_updated
            if isinstance(lu, str):
                lu = _dt.strptime(lu[:10], '%Y-%m-%d')
            lines.append(('Helvetica', 7, f"a/o {lu.strftime('%m/%d/%y')}", GRAY))
        except:
            pass

    total_h = len(lines) * 12
    y = cy + total_h / 2 - 6

    for font, size, text, color in lines:
        c.setFont(font, size)
        c.setFillColor(color)
        c.drawCentredString(cx, y, text)
        y -= 12

    # Cash badge inside if present
    if acct.cash_balance is not None:
        bw, bh = 55, 22
        c.setFillColor(PALE_BLUE)
        c.roundRect(cx - bw//2, cy - ry + 6, bw, bh, 4, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(DARK_BLUE)
        c.drawCentredString(cx, cy - ry + 18, fmt_money(acct.cash_balance, False))
        c.setFont('Helvetica', 7)
        c.drawCentredString(cx, cy - ry + 9, "Cash")

def draw_gray_box(c, cx, cy, w, h, label, value):
    c.setFillColor(GRAY_BOX)
    c.roundRect(cx - w//2, cy - h//2, w, h, 5, fill=1, stroke=0)
    c.setFont('Helvetica', 8)
    c.setFillColor(LIGHT_GRAY)
    c.drawCentredString(cx, cy + h//2 - 14, label)
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(WHITE)
    c.drawCentredString(cx, cy - h//2 + 6, value)

def draw_client_bubble(c, cx, cy, r, client, which=1):
    draw_oval(c, cx, cy, r, r, LIGHT_GREEN, DARK_GREEN, 2.5)
    name = client.name_1 if which == 1 else (client.name_2 or '')
    age = client.age_1 if which == 1 else client.age_2
    ssn = client.ssn_last4_1 if which == 1 else client.ssn_last4_2
    dob = client.dob_1 if which == 1 else client.dob_2

    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(WHITE)
    c.drawCentredString(cx, cy + 16, f"Client {which}")
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(cx, cy + 2, name)
    c.setFont('Helvetica', 9)
    c.setFillColor(colors.HexColor('#D0FFD0'))
    if age:
        c.drawCentredString(cx, cy - 12, f"Age {age}")
    if dob:
        c.drawCentredString(cx, cy - 24, dob)
    if ssn:
        c.drawCentredString(cx, cy - 36, f"SSN: ***-**-{ssn}")


def generate_tcc_pdf(client_dict, report_date, quarter, output_path):
    client = wrap(client_dict)
    c = canvas.Canvas(output_path, pagesize=letter)
    page_w, page_h = letter

    draw_header(c, client, report_date, quarter, page_w, page_h)

    # ── LAYOUT CONSTANTS ──
    y_retire_top = page_h - 1.3*inch  # top of retirement section
    retire_h = 2.5 * inch
    y_retire_center = y_retire_top - retire_h / 2

    y_nonretire_top = y_retire_top - retire_h - 0.05*inch
    nonretire_h = 2.5 * inch
    y_nonretire_center = y_nonretire_top - nonretire_h / 2

    # Section dividers
    c.setFillColor(colors.HexColor('#EBF4FA'))
    c.rect(0, y_retire_top - retire_h, page_w, retire_h, fill=1, stroke=0)
    c.setFillColor(PALE_GRAY)
    c.rect(0, y_nonretire_top - nonretire_h, page_w, nonretire_h, fill=1, stroke=0)

    # Section labels
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(GRAY)
    c.drawString(0.2*inch, y_retire_top - 14, "RETIREMENT")
    c.drawRightString(page_w - 0.2*inch, y_retire_top - 14, "RETIREMENT")
    c.drawString(0.2*inch, y_nonretire_top - 14, "NON RETIREMENT")
    c.drawRightString(page_w - 0.2*inch, y_nonretire_top - 14, "NON RETIREMENT")

    # ── CLIENT BUBBLES (centered top area) ──
    cx_c1 = page_w * 0.28
    cx_c2 = page_w * 0.72
    cy_clients = y_retire_top - retire_h * 0.38
    r_client = 0.48 * inch

    draw_client_bubble(c, cx_c1, cy_clients, r_client, client, 1)
    draw_client_bubble(c, cx_c2, cy_clients, r_client, client, 2)

    # ── LIABILITIES BOX (center top) ──
    cx_liab_top = page_w / 2
    cy_liab_top = cy_clients
    c.setFillColor(LIGHT_GRAY)
    c.roundRect(cx_liab_top - 0.7*inch, cy_liab_top - 0.28*inch,
                1.4*inch, 0.55*inch, 4, fill=1, stroke=0)
    c.setFont('Helvetica', 8)
    c.setFillColor(DARK_BLUE)
    c.drawCentredString(cx_liab_top, cy_liab_top + 10, "Liabilities:")
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(RED)
    c.drawCentredString(cx_liab_top, cy_liab_top - 3, fmt_money(client.liabilities_total))
    c.setFont('Helvetica', 7)
    c.setFillColor(GRAY)
    c.drawCentredString(cx_liab_top, cy_liab_top - 14,
        f"a/o {__import__('datetime').datetime.today().strftime('%m/%d/%Y')}")

    # ── RETIREMENT TOTALS BOXES ──
    draw_gray_box(c, cx_c1 - r_client - 0.85*inch, cy_clients, 1.3*inch, 0.55*inch,
                  "Client 1 Retirement Only", fmt_money(client.retirement_total_1))
    draw_gray_box(c, cx_c2 + r_client + 0.85*inch, cy_clients, 1.3*inch, 0.55*inch,
                  "Client 2 Retirement Only", fmt_money(client.retirement_total_2))

    # ── RETIREMENT ACCOUNT BUBBLES ──
    ret1 = [a for a in client.accounts if a.is_retirement and a.owner == 'client1']
    ret2 = [a for a in client.accounts if a.is_retirement and a.owner == 'client2']

    cy_ret_acct = y_retire_top - retire_h + 0.65*inch
    _place_account_row(c, ret1, cx_c1, cy_ret_acct, 0.55*inch, 0.48*inch, max_per_row=3)
    _place_account_row(c, ret2, cx_c2, cy_ret_acct, 0.55*inch, 0.48*inch, max_per_row=3)

    # ── TRUST (center) ──
    cx_trust = page_w / 2
    cy_trust = y_nonretire_top - nonretire_h * 0.48

    trust_acct = next((a for a in client.accounts if a.is_trust), None)
    trust_val = trust_acct.current_balance if trust_acct else client.zillow_value or 0

    draw_oval(c, cx_trust, cy_trust, 0.72*inch, 0.58*inch, WHITE, DARK_BLUE, 1.5)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(DARK_BLUE)
    c.drawCentredString(cx_trust, cy_trust + 20, trust_acct.account_type if trust_acct else "Family Trust")
    c.setFont('Helvetica', 8)
    c.setFillColor(GRAY)
    if trust_acct and trust_acct.acct_last4:
        c.drawCentredString(cx_trust, cy_trust + 8, f"ACCT #{trust_acct.acct_last4}")
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(DARK_BLUE)
    c.drawCentredString(cx_trust, cy_trust - 4, fmt_money(trust_val))
    if trust_acct and trust_acct.last_updated:
        try:
            from datetime import datetime as _dt
            lu = trust_acct.last_updated
            if isinstance(lu, str): lu = _dt.strptime(lu[:10], '%Y-%m-%d')
            c.setFont('Helvetica', 7)
            c.setFillColor(GRAY)
            c.drawCentredString(cx_trust, cy_trust - 16, f"a/o {lu.strftime('%m/%d/%y')}")
        except:
            pass

    if client.trust_address:
        c.setFont('Helvetica', 7)
        c.setFillColor(GRAY)
        c.drawCentredString(cx_trust, cy_trust - 26, f"Zillow: {client.trust_address[:30]}")

    # ── NON-RETIREMENT ACCOUNTS ──
    non_ret = [a for a in client.accounts if not a.is_retirement and not a.is_trust]
    cx_left_nr  = page_w * 0.22
    cx_right_nr = page_w * 0.78

    nr_left  = [a for a in non_ret if a.owner in ('client1', 'joint') and not a.is_private_reserve][:4]
    nr_right = [a for a in non_ret if a.is_private_reserve or a.owner == 'client2'][:4]
    cy_nr = y_nonretire_top - nonretire_h * 0.4

    _place_account_col(c, nr_left,  cx_left_nr,  cy_nr, 0.55*inch, 0.45*inch)
    _place_account_col(c, nr_right, cx_right_nr, cy_nr, 0.55*inch, 0.45*inch)

    # ── NON-RETIREMENT TOTAL ──
    y_nr_total = y_nonretire_top - nonretire_h + 0.15*inch
    draw_gray_box(c, page_w/2, y_nr_total + 0.18*inch, 2.0*inch, 0.45*inch,
                  "NON-RETIREMENT TOTAL", fmt_money(client.non_retirement_total))

    # ── LIABILITIES DETAIL TABLE ──
    if client.liabilities:
        y_liab = y_nr_total - 0.3*inch
        _draw_liabilities_table(c, client, page_w/2, y_liab)

    # ── FOOTER ──
    c.setFillColor(DARK_BLUE)
    c.rect(0, 0, page_w, 0.4*inch, fill=1, stroke=0)
    c.setFont('Helvetica', 8)
    c.setFillColor(WHITE)
    c.drawCentredString(page_w/2, 0.15*inch,
        "Windbrook Solutions  |  Confidential  |  * Indicates we do not have up to date information")
    c.save()


def _place_account_row(c, accounts, cx, cy, rx, ry, max_per_row=3):
    if not accounts:
        return
    n = min(len(accounts), max_per_row)
    gap = rx * 2.4
    total_w = (n - 1) * gap
    x_start = cx - total_w / 2
    for i, acct in enumerate(accounts[:n]):
        x = x_start + i * gap
        draw_account_bubble(c, x, cy, rx, ry, acct, small=(n > 2))


def _place_account_col(c, accounts, cx, cy_start, rx, ry):
    gap = ry * 2.4
    for i, acct in enumerate(accounts):
        draw_account_bubble(c, cx, cy_start - i * gap, rx, ry, acct, small=True)


def _draw_liabilities_table(c, client, cx, y_top):
    liabs = client.liabilities
    if not liabs:
        return

    col_w = 2.5 * inch
    row_h = 16
    tx = cx - col_w / 2

    c.setFillColor(GRAY_BOX)
    c.roundRect(tx, y_top - row_h, col_w, row_h, 3, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(WHITE)
    c.drawCentredString(cx, y_top - row_h + 4, "Liabilities")
    y = y_top - row_h

    for i, l in enumerate(liabs):
        bg = colors.HexColor('#FDECEA') if i % 2 == 0 else WHITE
        c.setFillColor(bg)
        c.rect(tx, y - row_h, col_w, row_h, fill=1, stroke=0)
        c.setFont('Helvetica', 8)
        c.setFillColor(DARK_BLUE)
        c.drawString(tx + 5, y - row_h + 4, l.name or '')
        rate_str = f"{l.interest_rate:.1f}%" if l.interest_rate else ""
        c.drawCentredString(cx, y - row_h + 4, rate_str)
        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(RED)
        c.drawRightString(tx + col_w - 5, y - row_h + 4, fmt_money(l.balance))
        y -= row_h

    c.setStrokeColor(GRAY)
    c.setLineWidth(0.5)
    c.rect(tx, y, col_w, y_top - y, stroke=1, fill=0)
