"""
HTML template builders for A4 and POS (80 mm thermal) invoice/receipt layouts.
QTextDocument supports a rich subset of HTML4 + CSS2, so we use table-based layouts.
"""

from datetime import datetime


# ── Brand colours (sync with styles.py) ───────────────────────────────────────
_PRIMARY   = "#4F46E5"
_SUCCESS   = "#059669"
_DANGER    = "#DC2626"
_WARNING   = "#D97706"
_LIGHT     = "#F1F5F9"
_BORDER    = "#E2E8F0"
_TEXT_DARK = "#111827"
_TEXT_MID  = "#374151"
_TEXT_LIGHT= "#6B7280"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  A4  SALES INVOICE                                                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def build_a4_sales_invoice(sale: dict, items: list,
                            company: dict | None = None) -> str:
    """
    sale    – row from DB (invoice_no, customer, sale_date, subtotal,
              discount, tax_amount, total, paid_amount, due_amount,
              payment_type, status, note)
    items   – list of rows (product_name, unit, quantity, unit_price,
              discount, total)
    company – {name, address, phone, email, tax_id}  (optional)
    """
    company = company or {}
    c_name    = company.get("name",    "My Company")
    c_addr    = company.get("address", "")
    c_phone   = company.get("phone",   "")
    c_email   = company.get("email",   "")
    c_tax_id  = company.get("tax_id",  "")

    status_color = {"paid": _SUCCESS, "partial": _WARNING, "unpaid": _DANGER}
    st_color = status_color.get((sale.get("status") or "").lower(), _TEXT_MID)

    rows_html = ""
    for idx, item in enumerate(items, 1):
        disc_pct = item.get("discount", 0) or 0
        rows_html += f"""
        <tr style="background:{'#F8FAFC' if idx % 2 == 0 else 'white'};">
          <td style="text-align:center;">{idx}</td>
          <td>{item['product_name']}</td>
          <td style="text-align:center;">{item['unit']}</td>
          <td style="text-align:center;">{item['quantity']}</td>
          <td style="text-align:right;">${item['unit_price']:,.2f}</td>
          <td style="text-align:center;">{disc_pct:.1f}%</td>
          <td style="text-align:right; font-weight:bold;">${item['total']:,.2f}</td>
        </tr>"""

    subtotal    = sale.get("subtotal",    0) or 0
    discount    = sale.get("discount",    0) or 0
    tax_amount  = sale.get("tax_amount",  0) or 0
    total       = sale.get("total",       0) or 0
    paid        = sale.get("paid_amount", 0) or 0
    due         = sale.get("due_amount",  0) or 0
    note        = sale.get("note",        "") or ""

    due_row = ""
    if due > 0:
        due_row = f"""
        <tr>
          <td colspan="2" style="text-align:right; padding:4px 10px;
              color:{_DANGER}; font-weight:bold;">Due:</td>
          <td style="text-align:right; padding:4px 10px;
              color:{_DANGER}; font-weight:bold;">${due:,.2f}</td>
        </tr>"""

    note_row = ""
    if note:
        note_row = f"""
        <tr>
          <td colspan="3" style="padding:10px; color:{_TEXT_LIGHT};
              font-style:italic; border:none;">Note: {note}</td>
        </tr>"""

    addr_lines = c_addr.replace("\n", "<br/>") if c_addr else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: Arial, Helvetica, sans-serif;
          font-size: 11pt; color: {_TEXT_DARK}; margin: 0; padding: 24px; }}
  table {{ border-collapse: collapse; }}
  .w100 {{ width: 100%; }}
  .section {{ margin-bottom: 18px; }}
  .label {{ font-size: 9pt; color: {_TEXT_LIGHT}; text-transform: uppercase;
            letter-spacing: 0.5px; }}
  .value {{ font-size: 11pt; }}
  .divider {{ border: none; border-top: 2px solid {_BORDER}; margin: 14px 0; }}
  .items-table th {{
      background: {_PRIMARY}; color: white;
      padding: 8px 10px; text-align: left; font-size: 10pt;
  }}
  .items-table td {{
      padding: 7px 10px; border-bottom: 1px solid {_BORDER}; font-size: 10pt;
  }}
  .totals-table td {{ padding: 5px 10px; font-size: 11pt; }}
  .grand-total {{ font-size: 14pt; font-weight: bold; color: {_PRIMARY};
                  border-top: 2px solid {_PRIMARY}; border-bottom: 2px solid {_PRIMARY}; }}
  .status-badge {{
      display: inline-block; padding: 4px 14px;
      border-radius: 4px; font-weight: bold; font-size: 10pt;
      color: white; background: {st_color};
  }}
  .footer {{ margin-top: 28px; text-align: center; color: {_TEXT_LIGHT};
             font-size: 9pt; border-top: 1px solid {_BORDER}; padding-top: 10px; }}
</style>
</head>
<body>

<!-- ── HEADER ─────────────────────────────────────── -->
<table class="w100 section">
  <tr>
    <td width="55%" style="vertical-align:top;">
      <div style="font-size:20pt; font-weight:bold; color:{_PRIMARY};">{c_name}</div>
      {"<div style='color:" + _TEXT_MID + ";margin-top:4px;'>" + addr_lines + "</div>" if addr_lines else ""}
      {"<div style='color:" + _TEXT_MID + ";'>" + c_phone + "</div>" if c_phone else ""}
      {"<div style='color:" + _TEXT_MID + ";'>" + c_email + "</div>" if c_email else ""}
      {"<div style='color:" + _TEXT_LIGHT + ";font-size:9pt;'>Tax ID: " + c_tax_id + "</div>" if c_tax_id else ""}
    </td>
    <td width="45%" style="vertical-align:top; text-align:right;">
      <div style="font-size:26pt; font-weight:bold; color:{_PRIMARY}; letter-spacing:1px;">INVOICE</div>
      <div style="font-size:13pt; font-weight:bold; color:{_TEXT_DARK};">
          {sale.get('invoice_no','—')}
      </div>
      <div style="color:{_TEXT_LIGHT}; margin-top:6px;">
          Date: <b>{sale.get('sale_date','—')}</b>
      </div>
      <div style="margin-top:6px;">
          <span class="status-badge">{(sale.get('status','') or '').upper()}</span>
      </div>
    </td>
  </tr>
</table>

<hr class="divider"/>

<!-- ── BILL TO ────────────────────────────────────── -->
<table class="w100 section">
  <tr>
    <td width="50%" style="vertical-align:top;">
      <div class="label">Bill To</div>
      <div style="font-size:13pt; font-weight:bold; margin-top:4px;">
          {sale.get('customer','Walk-in Customer')}
      </div>
    </td>
    <td width="50%" style="vertical-align:top; text-align:right;">
      <div class="label">Payment Method</div>
      <div style="font-size:12pt; font-weight:bold; margin-top:4px;">
          {(sale.get('payment_type','') or 'Cash').title()}
      </div>
    </td>
  </tr>
</table>

<hr class="divider"/>

<!-- ── ITEMS ──────────────────────────────────────── -->
<table class="w100 items-table section">
  <thead>
    <tr>
      <th style="width:4%; text-align:center;">#</th>
      <th style="width:34%;">Product / Description</th>
      <th style="width:8%; text-align:center;">Unit</th>
      <th style="width:8%; text-align:center;">Qty</th>
      <th style="width:14%; text-align:right;">Unit Price</th>
      <th style="width:8%; text-align:center;">Disc%</th>
      <th style="width:14%; text-align:right;">Amount</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>

<!-- ── TOTALS ─────────────────────────────────────── -->
<table class="w100">
  <tr>
    <td width="55%" style="vertical-align:top; padding-right:20px;">
      {note_row and ('<div style="color:' + _TEXT_LIGHT + '; font-style:italic; font-size:10pt;">Note: ' + note + '</div>') or ''}
      <div style="margin-top:14px; color:{_TEXT_LIGHT}; font-size:9pt;">
          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
      </div>
    </td>
    <td width="45%">
      <table class="w100 totals-table">
        <tr>
          <td style="color:{_TEXT_LIGHT};">Subtotal:</td>
          <td style="text-align:right;">${subtotal:,.2f}</td>
        </tr>
        {"<tr><td style='color:" + _TEXT_LIGHT + ";'>Discount:</td><td style='text-align:right; color:" + _DANGER + ";'>-${discount:,.2f}</td></tr>" if discount > 0 else ""}
        {"<tr><td style='color:" + _TEXT_LIGHT + ";'>Tax:</td><td style='text-align:right;'>${tax_amount:,.2f}</td></tr>" if tax_amount > 0 else ""}
        <tr class="grand-total">
          <td style="padding:8px 10px;">TOTAL:</td>
          <td style="text-align:right; padding:8px 10px;">${total:,.2f}</td>
        </tr>
        <tr>
          <td style="color:{_SUCCESS}; font-weight:bold;">Paid:</td>
          <td style="text-align:right; color:{_SUCCESS}; font-weight:bold;">${paid:,.2f}</td>
        </tr>
        {"<tr><td style='color:" + _DANGER + "; font-weight:bold;'>Due:</td><td style='text-align:right; color:" + _DANGER + "; font-weight:bold;'>${due:,.2f}</td></tr>" if due > 0 else ""}
      </table>
    </td>
  </tr>
</table>

<!-- ── FOOTER ─────────────────────────────────────── -->
<div class="footer">
  Thank you for your business!&nbsp;&nbsp;|&nbsp;&nbsp;{c_name}
  {"&nbsp;&nbsp;|&nbsp;&nbsp;" + c_phone if c_phone else ""}
</div>

</body>
</html>"""


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  A4  PURCHASE INVOICE / BILL                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def build_a4_purchase_invoice(purchase: dict, items: list,
                               company: dict | None = None) -> str:
    company = company or {}
    c_name   = company.get("name",    "My Company")
    c_addr   = company.get("address", "")
    c_phone  = company.get("phone",   "")
    c_email  = company.get("email",   "")
    c_tax_id = company.get("tax_id",  "")

    status_color = {"paid": _SUCCESS, "partial": _WARNING, "unpaid": _DANGER}
    st_color = status_color.get((purchase.get("status") or "").lower(), _TEXT_MID)

    rows_html = ""
    for idx, item in enumerate(items, 1):
        rows_html += f"""
        <tr style="background:{'#F8FAFC' if idx % 2 == 0 else 'white'};">
          <td style="text-align:center;">{idx}</td>
          <td>{item['product_name']}</td>
          <td style="text-align:center;">{item['unit']}</td>
          <td style="text-align:center;">{item['quantity']}</td>
          <td style="text-align:right;">${item['unit_price']:,.2f}</td>
          <td style="text-align:right; font-weight:bold;">${item['total']:,.2f}</td>
        </tr>"""

    subtotal   = purchase.get("subtotal",    0) or 0
    discount   = purchase.get("discount",    0) or 0
    tax_amount = purchase.get("tax_amount",  0) or 0
    total      = purchase.get("total",       0) or 0
    paid       = purchase.get("paid_amount", 0) or 0
    due        = purchase.get("due_amount",  0) or 0
    note       = purchase.get("note",        "") or ""
    addr_lines = c_addr.replace("\n", "<br/>") if c_addr else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: Arial, Helvetica, sans-serif;
          font-size: 11pt; color: {_TEXT_DARK}; margin: 0; padding: 24px; }}
  table {{ border-collapse: collapse; }}
  .w100 {{ width: 100%; }}
  .section {{ margin-bottom: 18px; }}
  .label {{ font-size: 9pt; color: {_TEXT_LIGHT}; text-transform: uppercase;
            letter-spacing: 0.5px; }}
  .divider {{ border: none; border-top: 2px solid {_BORDER}; margin: 14px 0; }}
  .items-table th {{
      background: {_WARNING}; color: white;
      padding: 8px 10px; text-align: left; font-size: 10pt;
  }}
  .items-table td {{
      padding: 7px 10px; border-bottom: 1px solid {_BORDER}; font-size: 10pt;
  }}
  .totals-table td {{ padding: 5px 10px; font-size: 11pt; }}
  .grand-total {{ font-size: 14pt; font-weight: bold; color: {_WARNING};
                  border-top: 2px solid {_WARNING}; border-bottom: 2px solid {_WARNING}; }}
  .status-badge {{
      display: inline-block; padding: 4px 14px; border-radius: 4px;
      font-weight: bold; font-size: 10pt; color: white; background: {st_color};
  }}
  .footer {{ margin-top: 28px; text-align: center; color: {_TEXT_LIGHT};
             font-size: 9pt; border-top: 1px solid {_BORDER}; padding-top: 10px; }}
</style>
</head>
<body>

<!-- ── HEADER ─────────────────────────────────────── -->
<table class="w100 section">
  <tr>
    <td width="55%" style="vertical-align:top;">
      <div style="font-size:20pt; font-weight:bold; color:{_WARNING};">{c_name}</div>
      {"<div style='color:" + _TEXT_MID + ";margin-top:4px;'>" + addr_lines + "</div>" if addr_lines else ""}
      {"<div style='color:" + _TEXT_MID + ";'>" + c_phone + "</div>" if c_phone else ""}
      {"<div style='color:" + _TEXT_MID + ";'>" + c_email + "</div>" if c_email else ""}
      {"<div style='color:" + _TEXT_LIGHT + ";font-size:9pt;'>Tax ID: " + c_tax_id + "</div>" if c_tax_id else ""}
    </td>
    <td width="45%" style="vertical-align:top; text-align:right;">
      <div style="font-size:22pt; font-weight:bold; color:{_WARNING}; letter-spacing:1px;">PURCHASE ORDER</div>
      <div style="font-size:13pt; font-weight:bold; color:{_TEXT_DARK};">
          {purchase.get('po_number','—')}
      </div>
      <div style="color:{_TEXT_LIGHT}; margin-top:6px;">
          Date: <b>{purchase.get('purchase_date','—')}</b>
      </div>
      <div style="margin-top:6px;">
          <span class="status-badge">{(purchase.get('status','') or '').upper()}</span>
      </div>
    </td>
  </tr>
</table>

<hr class="divider"/>

<!-- ── SUPPLIER INFO ──────────────────────────────── -->
<table class="w100 section">
  <tr>
    <td width="50%" style="vertical-align:top;">
      <div class="label">Supplier</div>
      <div style="font-size:13pt; font-weight:bold; margin-top:4px;">
          {purchase.get('supplier','—')}
      </div>
    </td>
    <td width="50%" style="vertical-align:top; text-align:right;">
      <div class="label">Payment Method</div>
      <div style="font-size:12pt; font-weight:bold; margin-top:4px;">
          {(purchase.get('payment_type','') or 'Cash').title()}
      </div>
    </td>
  </tr>
</table>

<hr class="divider"/>

<!-- ── ITEMS ──────────────────────────────────────── -->
<table class="w100 items-table section">
  <thead>
    <tr>
      <th style="width:5%; text-align:center;">#</th>
      <th style="width:38%;">Product / Description</th>
      <th style="width:9%; text-align:center;">Unit</th>
      <th style="width:8%; text-align:center;">Qty</th>
      <th style="width:18%; text-align:right;">Unit Cost</th>
      <th style="width:18%; text-align:right;">Amount</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>

<!-- ── TOTALS ─────────────────────────────────────── -->
<table class="w100">
  <tr>
    <td width="55%" style="vertical-align:top; padding-right:20px;">
      {("<div style='color:" + _TEXT_LIGHT + "; font-style:italic; font-size:10pt;'>Note: " + note + "</div>") if note else ""}
      <div style="margin-top:14px; color:{_TEXT_LIGHT}; font-size:9pt;">
          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
      </div>
    </td>
    <td width="45%">
      <table class="w100 totals-table">
        <tr>
          <td style="color:{_TEXT_LIGHT};">Subtotal:</td>
          <td style="text-align:right;">${subtotal:,.2f}</td>
        </tr>
        {"<tr><td style='color:" + _TEXT_LIGHT + ";'>Discount:</td><td style='text-align:right; color:" + _DANGER + ";'>-${discount:,.2f}</td></tr>" if discount > 0 else ""}
        {"<tr><td style='color:" + _TEXT_LIGHT + ";'>Tax:</td><td style='text-align:right;'>${tax_amount:,.2f}</td></tr>" if tax_amount > 0 else ""}
        <tr class="grand-total">
          <td style="padding:8px 10px;">TOTAL:</td>
          <td style="text-align:right; padding:8px 10px;">${total:,.2f}</td>
        </tr>
        <tr>
          <td style="color:{_SUCCESS}; font-weight:bold;">Paid:</td>
          <td style="text-align:right; color:{_SUCCESS}; font-weight:bold;">${paid:,.2f}</td>
        </tr>
        {"<tr><td style='color:" + _DANGER + "; font-weight:bold;'>Due:</td><td style='text-align:right; color:" + _DANGER + "; font-weight:bold;'>${due:,.2f}</td></tr>" if due > 0 else ""}
      </table>
    </td>
  </tr>
</table>

<div class="footer">
  {c_name}&nbsp;&nbsp;|&nbsp;&nbsp;Purchase Record
  {"&nbsp;&nbsp;|&nbsp;&nbsp;" + c_phone if c_phone else ""}
  &nbsp;&nbsp;|&nbsp;&nbsp;Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
</div>

</body>
</html>"""


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  POS (80 mm thermal) SALES RECEIPT                                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

_POS_W = 42   # characters per line for 80 mm paper at ~12 pt monospace


def _divider(ch="="):
    return ch * _POS_W


def _center(text, width=_POS_W):
    return text.center(width)


def _right_align(label, value, width=_POS_W):
    space = width - len(label) - len(value)
    if space < 1:
        space = 1
    return label + " " * space + value


def _wrap(text, width=_POS_W):
    """Simple word wrap."""
    words = text.split()
    lines = []
    line = ""
    for word in words:
        if len(line) + len(word) + 1 <= width:
            line = (line + " " + word).strip()
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _pos_to_html(lines: list[str], bold_rows: set[int] = None,
                 large_rows: set[int] = None, center_rows: set[int] = None) -> str:
    """Convert list of text lines to styled HTML for POS preview."""
    bold_rows   = bold_rows   or set()
    large_rows  = large_rows  or set()
    center_rows = center_rows or set()

    html_lines = []
    for i, line in enumerate(lines):
        style_parts = ["white-space:pre; font-family:'Courier New',Courier,monospace; font-size:10pt;"]
        if i in bold_rows:
            style_parts.append("font-weight:bold;")
        if i in large_rows:
            style_parts.append("font-size:13pt;")
        if i in center_rows:
            style_parts.append("text-align:center;")
        escaped = (line.replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;").replace(" ", "&nbsp;"))
        html_lines.append(f'<div style="{" ".join(style_parts)}">{escaped}</div>')

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  body {{ background: white; margin: 0; padding: 10px 6px;
          font-family: 'Courier New', Courier, monospace; font-size:10pt; }}
</style>
</head>
<body>
{''.join(html_lines)}
</body>
</html>"""


def build_pos_sales_receipt(sale: dict, items: list,
                             company: dict | None = None) -> str:
    company  = company or {}
    c_name   = company.get("name",  "My Company")
    c_phone  = company.get("phone", "")
    c_email  = company.get("email", "")

    lines      : list[str] = []
    bold_rows  : set[int]  = set()
    large_rows : set[int]  = set()
    center_rows: set[int]  = set()

    def add(text="", bold=False, large=False, center=False):
        idx = len(lines)
        lines.append(text)
        if bold:   bold_rows.add(idx)
        if large:  large_rows.add(idx)
        if center: center_rows.add(idx)

    add(_center(c_name), bold=True, large=True, center=True)
    if c_phone: add(_center(c_phone), center=True)
    if c_email: add(_center(c_email), center=True)
    add(_divider("="))
    add(_center("SALES RECEIPT"), bold=True, center=True)
    add(_divider("="))
    add(_right_align("Invoice:", sale.get("invoice_no", "—")))
    add(_right_align("Date:",    sale.get("sale_date", "—")))
    add(_right_align("Customer:", (sale.get("customer") or "Walk-in")[:20]))
    add(_right_align("Payment:", (sale.get("payment_type") or "Cash").title()))
    add(_divider("-"))
    add("ITEMS", bold=True)
    add(_divider("-"))

    for item in items:
        product = item["product_name"]
        for ln in _wrap(product, _POS_W):
            add(f"  {ln}")
        qty_line = f"  {item['quantity']} x ${item['unit_price']:,.2f}"
        total_str = f"${item['total']:,.2f}"
        pad = _POS_W - len(qty_line) - len(total_str)
        add(qty_line + " " * max(1, pad) + total_str)

    add(_divider("-"))
    subtotal   = sale.get("subtotal",    0) or 0
    discount   = sale.get("discount",    0) or 0
    tax_amount = sale.get("tax_amount",  0) or 0
    total      = sale.get("total",       0) or 0
    paid       = sale.get("paid_amount", 0) or 0
    due        = sale.get("due_amount",  0) or 0

    add(_right_align("Subtotal:", f"${subtotal:,.2f}"))
    if discount > 0:
        add(_right_align("Discount:", f"-${discount:,.2f}"))
    if tax_amount > 0:
        add(_right_align("Tax:", f"${tax_amount:,.2f}"))
    add(_divider("="))
    total_line = len(lines)
    add(_right_align("TOTAL:", f"${total:,.2f}"), bold=True)
    add(_right_align("Paid:",  f"${paid:,.2f}"))
    if due > 0:
        add(_right_align("Due:", f"${due:,.2f}"), bold=True)
    add(_divider("="))
    status_line = len(lines)
    add(_center(f"** {(sale.get('status') or 'PAID').upper()} **"), bold=True, center=True)
    add("")

    note = sale.get("note", "") or ""
    if note:
        add("Note:", bold=True)
        for ln in _wrap(note, _POS_W):
            add(f"  {ln}")
        add("")

    add(_divider("="))
    add(_center("Thank you for your business!"), center=True)
    add(_center(datetime.now().strftime("%Y-%m-%d %H:%M")), center=True)
    add(_divider("="))
    add("")
    add("")

    return _pos_to_html(lines, bold_rows, large_rows, center_rows)


def build_pos_purchase_receipt(purchase: dict, items: list,
                                company: dict | None = None) -> str:
    company  = company or {}
    c_name   = company.get("name",  "My Company")
    c_phone  = company.get("phone", "")

    lines      : list[str] = []
    bold_rows  : set[int]  = set()
    large_rows : set[int]  = set()
    center_rows: set[int]  = set()

    def add(text="", bold=False, large=False, center=False):
        idx = len(lines)
        lines.append(text)
        if bold:   bold_rows.add(idx)
        if large:  large_rows.add(idx)
        if center: center_rows.add(idx)

    add(_center(c_name), bold=True, large=True, center=True)
    if c_phone: add(_center(c_phone), center=True)
    add(_divider("="))
    add(_center("PURCHASE RECEIPT"), bold=True, center=True)
    add(_divider("="))
    add(_right_align("PO Number:", purchase.get("po_number", "—")))
    add(_right_align("Date:",      purchase.get("purchase_date", "—")))
    add(_right_align("Supplier:",  (purchase.get("supplier") or "—")[:20]))
    add(_right_align("Payment:",   (purchase.get("payment_type") or "Cash").title()))
    add(_divider("-"))
    add("ITEMS", bold=True)
    add(_divider("-"))

    for item in items:
        product = item["product_name"]
        for ln in _wrap(product, _POS_W):
            add(f"  {ln}")
        qty_line = f"  {item['quantity']} x ${item['unit_price']:,.2f}"
        total_str = f"${item['total']:,.2f}"
        pad = _POS_W - len(qty_line) - len(total_str)
        add(qty_line + " " * max(1, pad) + total_str)

    add(_divider("-"))
    subtotal   = purchase.get("subtotal",    0) or 0
    discount   = purchase.get("discount",    0) or 0
    tax_amount = purchase.get("tax_amount",  0) or 0
    total      = purchase.get("total",       0) or 0
    paid       = purchase.get("paid_amount", 0) or 0
    due        = purchase.get("due_amount",  0) or 0

    add(_right_align("Subtotal:", f"${subtotal:,.2f}"))
    if discount > 0:
        add(_right_align("Discount:", f"-${discount:,.2f}"))
    if tax_amount > 0:
        add(_right_align("Tax:", f"${tax_amount:,.2f}"))
    add(_divider("="))
    add(_right_align("TOTAL:", f"${total:,.2f}"), bold=True)
    add(_right_align("Paid:",  f"${paid:,.2f}"))
    if due > 0:
        add(_right_align("Due:", f"${due:,.2f}"), bold=True)
    add(_divider("="))
    add(_center(f"** {(purchase.get('status') or 'PAID').upper()} **"), bold=True, center=True)
    add("")

    note = purchase.get("note", "") or ""
    if note:
        add("Note:", bold=True)
        for ln in _wrap(note, _POS_W):
            add(f"  {ln}")
        add("")

    add(_divider("="))
    add(_center("Purchase Recorded"), center=True)
    add(_center(datetime.now().strftime("%Y-%m-%d %H:%M")), center=True)
    add(_divider("="))
    add("")
    add("")

    return _pos_to_html(lines, bold_rows, large_rows, center_rows)


# ── Return receipts (compact POS format) ──────────────────────────────────────

def build_pos_sales_return_receipt(ret: dict, items: list,
                                   company: dict | None = None) -> str:
    company = company or {}
    c_name  = company.get("name", "My Company")

    lines: list[str] = []
    bold_rows: set[int] = set()
    large_rows: set[int] = set()
    center_rows: set[int] = set()

    def add(text="", bold=False, large=False, center=False):
        idx = len(lines)
        lines.append(text)
        if bold:   bold_rows.add(idx)
        if large:  large_rows.add(idx)
        if center: center_rows.add(idx)

    add(_center(c_name), bold=True, large=True, center=True)
    add(_divider("="))
    add(_center("SALES RETURN"), bold=True, center=True)
    add(_divider("="))
    add(_right_align("Return No:",  ret.get("return_no", "—")))
    add(_right_align("Invoice:",    ret.get("invoice_no", "—")))
    add(_right_align("Customer:",   (ret.get("customer") or "—")[:20]))
    add(_right_align("Date:",       ret.get("return_date", "—")))
    add(_right_align("Refund:",     (ret.get("refund_type") or "").title()))
    add(_divider("-"))
    add("RETURNED ITEMS", bold=True)
    add(_divider("-"))
    for item in items:
        for ln in _wrap(item["product_name"], _POS_W):
            add(f"  {ln}")
        qty_line  = f"  {item['quantity']} x ${item['unit_price']:,.2f}"
        total_str = f"${item['total']:,.2f}"
        pad = _POS_W - len(qty_line) - len(total_str)
        add(qty_line + " " * max(1, pad) + total_str)
    add(_divider("="))
    add(_right_align("RETURN TOTAL:", f"${ret.get('total', 0):,.2f}"), bold=True)
    add(_divider("="))
    if ret.get("reason"):
        add(f"Reason: {ret['reason']}")
    add(_center(datetime.now().strftime("%Y-%m-%d %H:%M")), center=True)
    add("")
    add("")

    return _pos_to_html(lines, bold_rows, large_rows, center_rows)


def build_pos_purchase_return_receipt(ret: dict, items: list,
                                      company: dict | None = None) -> str:
    company = company or {}
    c_name  = company.get("name", "My Company")

    lines: list[str] = []
    bold_rows: set[int] = set()
    large_rows: set[int] = set()
    center_rows: set[int] = set()

    def add(text="", bold=False, large=False, center=False):
        idx = len(lines)
        lines.append(text)
        if bold:   bold_rows.add(idx)
        if large:  large_rows.add(idx)
        if center: center_rows.add(idx)

    add(_center(c_name), bold=True, large=True, center=True)
    add(_divider("="))
    add(_center("PURCHASE RETURN"), bold=True, center=True)
    add(_divider("="))
    add(_right_align("Return No:", ret.get("return_no", "—")))
    add(_right_align("PO No:",     ret.get("po_number",  "—")))
    add(_right_align("Supplier:",  (ret.get("supplier") or "—")[:20]))
    add(_right_align("Date:",      ret.get("return_date", "—")))
    add(_right_align("Refund:",    (ret.get("refund_type") or "").title()))
    add(_divider("-"))
    add("RETURNED ITEMS", bold=True)
    add(_divider("-"))
    for item in items:
        for ln in _wrap(item["product_name"], _POS_W):
            add(f"  {ln}")
        qty_line  = f"  {item['quantity']} x ${item['unit_price']:,.2f}"
        total_str = f"${item['total']:,.2f}"
        pad = _POS_W - len(qty_line) - len(total_str)
        add(qty_line + " " * max(1, pad) + total_str)
    add(_divider("="))
    add(_right_align("RETURN TOTAL:", f"${ret.get('total', 0):,.2f}"), bold=True)
    add(_divider("="))
    if ret.get("reason"):
        add(f"Reason: {ret['reason']}")
    add(_center(datetime.now().strftime("%Y-%m-%d %H:%M")), center=True)
    add("")
    add("")

    return _pos_to_html(lines, bold_rows, large_rows, center_rows)
