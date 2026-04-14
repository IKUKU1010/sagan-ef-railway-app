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
GREEN       = colors.HexColor('#4A7C3F')
LIGHT_GREEN = colors.HexColor('#6AAF5A')
DARK_GREEN  = colors.HexColor('#2D5A27')
RED         = colors.HexColor('#C0392B')
LIGHT_RED   = colors.HexColor('#E74C3C')
DARK_RED    = colors.HexColor('#96281B')
BLUE_CIRCLE = colors.HexColor('#2980B9')
DARK_BLUE_C = colors.HexColor('#1A5276')
ARROW_RED   = colors.HexColor('#C0392B')
WHITE       = colors.white
GRAY        = colors.HexColor('#666666')
LIGHT_GRAY  = colors.HexColor('#CCCCCC')

def fmt_money(v, show_cent=False):
    if v is None:
        return '$0'
    if show_cent:
        return f"${v:,.2f}"
    return f"${v:,.0f}"

def draw_circle(c, cx, cy, r, fill_color, stroke_color=None, stroke_width=2):
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(stroke_width)
    else:
        c.setStrokeColor(fill_color)
    c.circle(cx, cy, r, stroke=1 if stroke_color else 0, fill=1)

def draw_centered_text(c, text, cx, cy, font='Helvetica-Bold', size=14, color=WHITE):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(cx, cy, text)

def draw_rounded_rect(c, x, y, w, h, r, fill_color, stroke_color=None):
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(1)
    else:
        c.setStrokeColor(fill_color)
    c.roundRect(x, y, w, h, r, stroke=1 if stroke_color else 0, fill=1)

def draw_arrow_h(c, x1, y1, x2, color=ARROW_RED, label=None, label_above=True):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(2.5)
    c.line(x1, y1, x2, y1)
    # arrowhead
    ah = 8
    aw = 5
    p = c.beginPath()
    p.moveTo(x2, y1)
    p.lineTo(x2 - ah, y1 + aw)
    p.lineTo(x2 - ah, y1 - aw)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    if label:
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(color)
        ly = y1 + 8 if label_above else y1 - 16
        c.drawCentredString((x1 + x2) / 2, ly, label)

def draw_arrow_v(c, x1, y1, y2, color=ARROW_RED, label=None):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(2.5)
    c.line(x1, y1, x1, y2)
    # arrowhead points down
    ah = 8
    aw = 5
    p = c.beginPath()
    p.moveTo(x1, y2)
    p.lineTo(x1 - aw, y2 + ah)
    p.lineTo(x1 + aw, y2 + ah)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    if label:
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(color)
        c.drawCentredString(x1 + 35, (y1 + y2) / 2, label)

def draw_page_header(c, client, report_date, quarter, title, page_w, page_h):
    # Top bar
    c.setFillColor(DARK_BLUE)
    c.rect(0, page_h - 0.7*inch, page_w, 0.7*inch, fill=1, stroke=0)

    c.setFont('Helvetica-Bold', 18)
    c.setFillColor(WHITE)
    c.drawCentredString(page_w / 2, page_h - 0.45*inch, title)

    # Client info bar
    c.setFillColor(PALE_BLUE)
    c.rect(0, page_h - 1.15*inch, page_w, 0.45*inch, fill=1, stroke=0)

    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(DARK_BLUE)
    c.drawString(0.4*inch, page_h - 0.88*inch, f"Client: {client.display_name}")
    c.drawRightString(page_w - 0.4*inch, page_h - 0.88*inch, f"{quarter}  |  {report_date}")

def draw_dollar_badge(c, cx, cy, amount, bg=WHITE, text_color=None):
    """White rounded rect badge with dollar amount inside a circle"""
    w, h = 110, 32
    draw_rounded_rect(c, cx - w//2, cy - h//2, w, h, 8, bg, None)
    if text_color is None:
        text_color = DARK_BLUE
    c.setFont('Helvetica-Bold', 13)
    c.setFillColor(text_color)
    c.drawCentredString(cx, cy - 5, fmt_money(amount))

def generate_sacs_pdf(client_dict, report_date, quarter, output_path):
    client = wrap(client_dict)
    c = canvas.Canvas(output_path, pagesize=letter)
    page_w, page_h = letter

    # ── PAGE 1: CASHFLOW DIAGRAM ──────────────────────────────────────
    draw_page_header(c, client, report_date, quarter,
                     "Simple Automated Cashflow System (SACS)", page_w, page_h)

    # Sub-title
    c.setFont('Helvetica-Bold', 13)
    c.setFillColor(DARK_BLUE)
    c.drawCentredString(page_w/2, page_h - 1.5*inch, "Monthly Cashflow Overview")

    # Inflow sources text (top-left)
    y_top = page_h - 2.0*inch
    c.setFont('Helvetica', 10)
    c.setFillColor(GRAY)

    # Salary sources
    sources = [(f.institution or f.account_type, f.current_balance)
               for f in client.accounts if f.is_inflow]
    if not sources:
        sources = [('Income', client.monthly_salary)]

    sx = 0.5 * inch
    sy = y_top
    for name, bal in sources:
        c.setFillColor(DARK_GREEN)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(sx, sy, f"${bal:,.0f} – {name}")
        sy -= 14

    # ── INFLOW CIRCLE (green, left) ──
    cx_in = 2.2 * inch
    cy_in = page_h - 3.4 * inch
    r_in = 0.95 * inch

    draw_circle(c, cx_in, cy_in, r_in, LIGHT_GREEN, DARK_GREEN, 3)
    # inner shine ring
    c.setStrokeColor(colors.HexColor('#FFFFFF40'))
    c.setLineWidth(1.5)
    c.circle(cx_in, cy_in, r_in - 8, stroke=1, fill=0)

    draw_centered_text(c, "INFLOW", cx_in, cy_in + 22, size=15)
    draw_dollar_badge(c, cx_in, cy_in - 8, client.monthly_salary)
    # Floor label
    c.setFont('Helvetica', 9)
    c.setFillColor(WHITE)
    c.drawCentredString(cx_in, cy_in - r_in + 14, f"${client.floor_amount:,.0f} Floor")

    # Arrow: inflow -> outflow
    ax1 = cx_in + r_in
    ax2_outflow = page_w - 2.2*inch - 0.95*inch
    arrow_y = cy_in
    # Arrow border (white outline for pop)
    c.setStrokeColor(WHITE)
    c.setLineWidth(4.5)
    c.line(ax1 + 2, arrow_y, ax2_outflow - 2, arrow_y)

    monthly_x_label = f"X = {fmt_money(client.monthly_expense_budget)}/month*"
    draw_arrow_h(c, ax1, arrow_y, ax2_outflow, ARROW_RED, monthly_x_label, label_above=True)

    # Sub-label for arrow
    c.setFont('Helvetica', 8)
    c.setFillColor(GRAY)
    c.drawCentredString((ax1 + ax2_outflow)/2, arrow_y - 15, "Automated transfer on the 28th")

    # ── OUTFLOW CIRCLE (red, right) ──
    cx_out = page_w - 2.2 * inch
    cy_out = cy_in

    draw_circle(c, cx_out, cy_out, r_in, LIGHT_RED, DARK_RED, 3)
    c.setStrokeColor(colors.HexColor('#FFFFFF40'))
    c.setLineWidth(1.5)
    c.circle(cx_out, cy_out, r_in - 8, stroke=1, fill=0)

    draw_centered_text(c, "OUTFLOW", cx_out, cy_out + 22, size=15)
    draw_dollar_badge(c, cx_out, cy_out - 8, client.monthly_expense_budget)
    c.setFont('Helvetica', 9)
    c.setFillColor(WHITE)
    c.drawCentredString(cx_out, cy_out - r_in + 14, f"${client.floor_amount:,.0f} Floor")

    # Monthly expenses label (right side)
    c.setFont('Helvetica', 9)
    c.setFillColor(GRAY)
    c.drawString(page_w - 1.35*inch, cy_out + 30, "X = Monthly")
    c.drawString(page_w - 1.35*inch, cy_out + 17, "Expenses")

    # Bracket lines to outflow
    c.setStrokeColor(GRAY)
    c.setLineWidth(1)
    c.line(page_w - 0.4*inch, cy_out + 10, page_w - 0.4*inch, cx_out - r_in + 10)
    c.line(page_w - 0.4*inch, cy_out + 10, cx_out + r_in, cy_out + 10)

    # ── PRIVATE RESERVE CIRCLE (blue, bottom center) ──
    cx_pr = page_w / 2
    cy_pr = page_h - 5.7 * inch

    draw_circle(c, cx_pr, cy_pr, r_in, BLUE_CIRCLE, DARK_BLUE_C, 3)
    c.setStrokeColor(colors.HexColor('#FFFFFF40'))
    c.setLineWidth(1.5)
    c.circle(cx_pr, cy_pr, r_in - 8, stroke=1, fill=0)

    draw_centered_text(c, "PRIVATE", cx_pr, cy_pr + 22, size=14)
    draw_centered_text(c, "RESERVE", cx_pr, cy_pr + 6, size=14)

    # piggy bank icon (simplified shape)
    _draw_piggy(c, cx_pr, cy_pr - 22)

    # Arrow: inflow down -> private reserve
    # L-shaped path: down from inflow, then right to private reserve
    lx = cx_in - 0.3*inch
    ly_top = cy_in - r_in
    ly_bot = cy_pr + r_in
    lx_end = cx_pr - 0.3*inch

    excess = client.excess_cashflow
    excess_label = f"${excess:,.0f}/mo*"

    c.setStrokeColor(MED_BLUE)
    c.setLineWidth(2.5)
    # vertical segment
    c.line(lx, ly_top, lx, ly_bot + 10)
    # horizontal segment
    c.line(lx, ly_bot + 10, lx_end, ly_bot + 10)
    # Arrowhead pointing right into PR
    c.setFillColor(MED_BLUE)
    p = c.beginPath()
    p.moveTo(lx_end, ly_bot + 10)
    p.lineTo(lx_end - 8, ly_bot + 15)
    p.lineTo(lx_end - 8, ly_bot + 5)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Label on arrow
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(MED_BLUE)
    c.drawString(lx + 5, (ly_top + ly_bot) / 2 + 5, excess_label)

    # Monthly cashflow label
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(DARK_BLUE)
    c.drawCentredString(cx_pr, cy_pr - r_in - 20, "MONTHLY CASHFLOW")

    # Footnote
    c.setFont('Helvetica', 8)
    c.setFillColor(GRAY)
    c.drawCentredString(page_w/2, 0.7*inch,
        "* Based on agreed monthly expense budget. Excess cashflow flows to Private Reserve.")

    # Footer
    _draw_footer(c, page_w, "Page 1 of 2")
    c.showPage()

    # ── PAGE 2: LONG-TERM CASHFLOW (FICA + INVESTMENT) ──────────────
    draw_page_header(c, client, report_date, quarter,
                     "Simple Automated Cashflow System (SACS)", page_w, page_h)

    c.setFont('Helvetica-Bold', 13)
    c.setFillColor(DARK_BLUE)
    c.drawCentredString(page_w/2, page_h - 1.5*inch, "Long-Term Cashflow")

    fica = client.fica_account
    pr = client.private_reserve_account
    pr_balance = pr.current_balance if pr else 0
    fica_balance = fica.current_balance if fica else 0
    invest_balance = max(0, pr_balance - fica_balance)

    # FICA circle (light blue)
    cx_f = page_w * 0.35
    cy_mid = page_h - 3.8 * inch
    r_lg = 1.15 * inch

    c.setFillColor(colors.HexColor('#B8D4EA'))
    c.setStrokeColor(colors.HexColor('#5A9ABF'))
    c.setLineWidth(2.5)
    c.circle(cx_f, cy_mid, r_lg, stroke=1, fill=1)

    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(DARK_BLUE)
    c.drawCentredString(cx_f, cy_mid + 20, "FICA")
    c.drawCentredString(cx_f, cy_mid + 4, "ACCOUNT")
    draw_dollar_badge(c, cx_f, cy_mid - 18, fica_balance,
                      bg=colors.HexColor('#D6E8F5'), text_color=DARK_BLUE)
    c.setFont('Helvetica', 9)
    c.setFillColor(GRAY)
    c.drawCentredString(cx_f, cy_mid - r_lg - 16,
        "6X Monthly Expenses + Deductibles")

    # Investment circle (dark blue)
    cx_i = page_w * 0.65
    c.setFillColor(DARK_BLUE)
    c.setStrokeColor(MED_BLUE)
    c.setLineWidth(2.5)
    c.circle(cx_i, cy_mid, r_lg, stroke=1, fill=1)

    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(WHITE)
    c.drawCentredString(cx_i, cy_mid + 20, "INVESTMENT")
    c.drawCentredString(cx_i, cy_mid + 4, "ACCOUNT")
    draw_dollar_badge(c, cx_i, cy_mid - 18, invest_balance,
                      bg=colors.HexColor('#1A3A5C'), text_color=WHITE)

    c.setFont('Helvetica', 9)
    c.setFillColor(GRAY)
    c.drawCentredString(cx_i, cy_mid - r_lg - 16, "Remainder")

    # Bidirectional arrow
    mid_x = (cx_f + r_lg + 0.1*inch + cx_i - r_lg - 0.1*inch) / 2
    ax1 = cx_f + r_lg + 0.1*inch
    ax2 = cx_i - r_lg - 0.1*inch

    c.setStrokeColor(MED_BLUE)
    c.setLineWidth(2.5)
    c.line(ax1, cy_mid, ax2, cy_mid)

    # Left arrowhead
    c.setFillColor(MED_BLUE)
    p = c.beginPath()
    p.moveTo(ax1, cy_mid)
    p.lineTo(ax1 + 9, cy_mid + 5)
    p.lineTo(ax1 + 9, cy_mid - 5)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Right arrowhead
    p = c.beginPath()
    p.moveTo(ax2, cy_mid)
    p.lineTo(ax2 - 9, cy_mid + 5)
    p.lineTo(ax2 - 9, cy_mid - 5)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Dashed vertical separator
    c.setStrokeColor(LIGHT_GRAY)
    c.setLineWidth(1)
    c.setDash([4, 4])
    c.line(page_w/2, page_h - 1.7*inch, page_w/2, cy_mid - r_lg - 0.3*inch)
    c.setDash([])

    # Labels
    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(DARK_BLUE)
    c.drawCentredString(page_w/2, cy_mid - r_lg - 50, "LONG TERM CASHFLOW")

    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(MED_BLUE)
    c.drawCentredString(page_w/2, cy_mid - r_lg - 70, "(Magnified Private Reserve Cashflow)")

    # Summary table
    sy_table = cy_mid - r_lg - 110
    _draw_summary_table(c, client, page_w, sy_table)

    _draw_footer(c, page_w, "Page 2 of 2")
    c.save()


def _draw_piggy(c, cx, cy):
    """Simple piggy bank shape"""
    c.setFillColor(colors.HexColor('#FFB3BA'))
    c.setStrokeColor(colors.HexColor('#FF6B7A'))
    c.setLineWidth(1)
    # body
    c.ellipse(cx - 14, cy - 10, cx + 14, cy + 10, stroke=1, fill=1)
    # head
    c.circle(cx + 12, cy + 5, 7, stroke=1, fill=1)
    # ear
    c.setFillColor(colors.HexColor('#FFD0D5'))
    c.ellipse(cx + 14, cy + 10, cx + 18, cy + 14, stroke=0, fill=1)
    # coin slot
    c.setStrokeColor(colors.HexColor('#CC5566'))
    c.setLineWidth(1.5)
    c.line(cx - 3, cy + 10, cx + 3, cy + 10)
    # legs
    c.setFillColor(colors.HexColor('#FFB3BA'))
    c.setStrokeColor(colors.HexColor('#FF6B7A'))
    c.setLineWidth(1)
    for lx in [cx - 8, cx - 2, cx + 4]:
        c.roundRect(lx, cy - 18, 4, 8, 2, stroke=1, fill=1)


def _draw_summary_table(c, client, page_w, y_start):
    rows = [
        ("Monthly Inflow", fmt_money(client.monthly_salary)),
        ("Monthly Outflow (Expenses)", fmt_money(client.monthly_expense_budget)),
        ("Monthly Excess to Private Reserve", fmt_money(client.excess_cashflow)),
        ("FICA Target", fmt_money(client.private_reserve_calc_target)),
    ]
    tw = 4 * inch
    tx = (page_w - tw) / 2
    row_h = 26
    y = y_start

    c.setFillColor(DARK_BLUE)
    c.rect(tx, y, tw, row_h, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(WHITE)
    c.drawCentredString(page_w/2, y + 8, "Cashflow Summary")
    y -= row_h

    for i, (label, val) in enumerate(rows):
        bg = colors.HexColor('#EBF4FA') if i % 2 == 0 else WHITE
        c.setFillColor(bg)
        c.rect(tx, y, tw, row_h, fill=1, stroke=0)
        c.setStrokeColor(LIGHT_GRAY)
        c.setLineWidth(0.5)
        c.line(tx, y, tx + tw, y)

        c.setFont('Helvetica', 10)
        c.setFillColor(DARK_BLUE)
        c.drawString(tx + 10, y + 8, label)
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(DARK_BLUE if label != rows[2][0] else GREEN)
        c.drawRightString(tx + tw - 10, y + 8, val)
        y -= row_h

    # Border
    c.setStrokeColor(MED_BLUE)
    c.setLineWidth(1)
    c.rect(tx, y, tw, y_start - y, stroke=1, fill=0)


def _draw_footer(c, page_w, page_label):
    c.setFillColor(DARK_BLUE)
    c.rect(0, 0, page_w, 0.4*inch, fill=1, stroke=0)
    c.setFont('Helvetica', 8)
    c.setFillColor(WHITE)
    c.drawCentredString(page_w/2, 0.15*inch, "Windbrook Solutions  |  Confidential  |  " + page_label)
