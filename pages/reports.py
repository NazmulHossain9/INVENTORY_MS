import csv
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QTabWidget, QDateEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from styles import (btn, page_title, card_frame, search_box,
                    PRIMARY, SUCCESS, DANGER, WARNING, INFO, PURPLE, ORANGE,
                    FIELD_STYLE, TABLE_STYLE, TEXT_DARK, TEXT_MID, TEXT_LIGHT)


def _date_filter_row(df_attr, dt_attr, on_change):
    """Helper: returns a QHBoxLayout with From/To date pickers."""
    layout = QHBoxLayout(); layout.setSpacing(8)
    df = QDateEdit(QDate.currentDate().addMonths(-1))
    dt = QDateEdit(QDate.currentDate())
    for d in [df, dt]:
        d.setStyleSheet(FIELD_STYLE); d.setCalendarPopup(True); d.setFixedWidth(115)
        d.dateChanged.connect(on_change)
    layout.addWidget(QLabel("From:")); layout.addWidget(df)
    layout.addWidget(QLabel("To:"));   layout.addWidget(dt)
    layout.addStretch()
    return layout, df, dt


class ReportsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(16)
        root.addWidget(page_title("Reports"))

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab {
                background: #E5E7EB; color: #374151; border-radius: 6px;
                padding: 7px 18px; font-size: 12px; margin-right: 3px;
            }
            QTabBar::tab:selected { background: #4F46E5; color: white; font-weight: 600; }
        """)

        # ── Sales Report ───────────────────────────────────────────────────────
        self._sales_tab = self._make_report_tab(
            tabs, "Sales Report",
            ["Invoice","Customer","Date","Subtotal","Discount","Tax","Total","Paid","Due","Status"],
            "_tbl_sales", "_sr_df", "_sr_dt", self._load_sales,
            summary_attr="_sr_sum"
        )

        # ── Purchase Report ────────────────────────────────────────────────────
        self._pur_tab = self._make_report_tab(
            tabs, "Purchase Report",
            ["PO Number","Supplier","Date","Subtotal","Discount","Tax","Total","Paid","Due","Status"],
            "_tbl_pur", "_pr_df", "_pr_dt", self._load_purchases,
            summary_attr="_pr_sum"
        )

        # ── Profit & Loss ──────────────────────────────────────────────────────
        pl_tab = QWidget()
        pll = QVBoxLayout(pl_tab); pll.setContentsMargins(0,12,0,0); pll.setSpacing(16)
        dr, self._pl_df, self._pl_dt = _date_filter_row("_pl_df","_pl_dt", self._load_pl)
        refresh_btn = btn("Refresh", PRIMARY); refresh_btn.clicked.connect(self._load_pl)
        dr.addWidget(refresh_btn); pll.addLayout(dr)

        # P&L cards
        pl_cards = QHBoxLayout(); pl_cards.setSpacing(16)
        for attr, title, color in [
            ("_pl_rev",  "Total Revenue",     SUCCESS),
            ("_pl_pur",  "Total Purchases",   WARNING),
            ("_pl_prof", "Gross Profit",      PRIMARY),
            ("_pl_marg", "Profit Margin",     INFO),
        ]:
            f = QFrame(); f.setStyleSheet(f"QFrame{{background:white;border-radius:12px;border-left:5px solid {color};}}")
            fl = QVBoxLayout(f); fl.setContentsMargins(16,12,16,12); fl.setSpacing(4)
            fl.addWidget(QLabel(title, styleSheet=f"font-size:11px;color:{TEXT_LIGHT};font-weight:600;background:transparent;border:none;"))
            v = QLabel("—"); v.setStyleSheet(f"font-size:24px;font-weight:700;color:{color};background:transparent;border:none;")
            fl.addWidget(v); pl_cards.addWidget(f); setattr(self, attr, v)
        pll.addLayout(pl_cards)

        # Breakdown table
        pl_f = card_frame(); pl_fl = QVBoxLayout(pl_f); pl_fl.setContentsMargins(16,14,16,14)
        self.tbl_pl = QTableWidget(5, 3)
        self.tbl_pl.setHorizontalHeaderLabels(["Description","Amount","% of Revenue"])
        self.tbl_pl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_pl.verticalHeader().setVisible(False)
        self.tbl_pl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_pl.setStyleSheet(TABLE_STYLE); self.tbl_pl.setAlternatingRowColors(True)
        pl_fl.addWidget(self.tbl_pl); pll.addWidget(pl_f)
        tabs.addTab(pl_tab, "Profit & Loss")

        # ── Stock Report ───────────────────────────────────────────────────────
        stk_tab = QWidget()
        stl = QVBoxLayout(stk_tab); stl.setContentsMargins(0,12,0,0); stl.setSpacing(12)
        stk_hr = QHBoxLayout()
        stk_refresh = btn("Refresh", PRIMARY); stk_refresh.clicked.connect(self._load_stock)
        stk_export  = btn("Export CSV", INFO);  stk_export.clicked.connect(lambda: self._export(self.tbl_stock, "stock_report"))
        stk_hr.addStretch(); stk_hr.addWidget(stk_refresh); stk_hr.addWidget(stk_export)
        stl.addLayout(stk_hr)

        sksf = QFrame(); sksf.setStyleSheet("QFrame{background:#EEF2FF;border-radius:8px;}")
        sksl = QHBoxLayout(sksf); sksl.setContentsMargins(16,8,16,8)
        self._stk_sum = QLabel(); self._stk_sum.setStyleSheet(f"font-size:13px;font-weight:600;color:{PRIMARY};")
        sksl.addWidget(self._stk_sum); sksl.addStretch(); stl.addWidget(sksf)

        stk_f = card_frame(); stk_fl = QVBoxLayout(stk_f); stk_fl.setContentsMargins(0,0,0,0)
        STK_HEADERS = ["Product","SKU","Category","Unit","Stock","Min","Cost","Sale","Value","Status"]
        self.tbl_stock = QTableWidget(); self.tbl_stock.setColumnCount(len(STK_HEADERS))
        self.tbl_stock.setHorizontalHeaderLabels(STK_HEADERS)
        self.tbl_stock.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_stock.setAlternatingRowColors(True); self.tbl_stock.verticalHeader().setVisible(False)
        self.tbl_stock.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_stock.setStyleSheet(TABLE_STYLE)
        stk_fl.addWidget(self.tbl_stock); stl.addWidget(stk_f)
        tabs.addTab(stk_tab, "Stock Report")

        # ── Cash Flow ─────────────────────────────────────────────────────────
        cf_tab = QWidget()
        cfl = QVBoxLayout(cf_tab); cfl.setContentsMargins(0,12,0,0); cfl.setSpacing(12)
        cfr, self._cf_df, self._cf_dt = _date_filter_row("_cf_df","_cf_dt", self._load_cashflow)
        cf_export = btn("Export CSV", INFO); cf_export.clicked.connect(lambda: self._export(self.tbl_cf,"cashflow"))
        cfr.addWidget(cf_export); cfl.addLayout(cfr)

        cfsf = QFrame(); cfsf.setStyleSheet("QFrame{background:#F0FDF4;border-radius:8px;}")
        cfsl = QHBoxLayout(cfsf); cfsl.setContentsMargins(16,8,16,8)
        self._cf_sum = QLabel(); self._cf_sum.setStyleSheet(f"font-size:13px;font-weight:600;color:{SUCCESS};")
        cfsl.addWidget(self._cf_sum); cfsl.addStretch(); cfl.addWidget(cfsf)

        cf_f = card_frame(); cf_fl = QVBoxLayout(cf_f); cf_fl.setContentsMargins(0,0,0,0)
        CF_HEADERS = ["#","Type","Party","Amount","Description","Date"]
        self.tbl_cf = QTableWidget(); self.tbl_cf.setColumnCount(len(CF_HEADERS))
        self.tbl_cf.setHorizontalHeaderLabels(CF_HEADERS)
        self.tbl_cf.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_cf.setAlternatingRowColors(True); self.tbl_cf.verticalHeader().setVisible(False)
        self.tbl_cf.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_cf.setStyleSheet(TABLE_STYLE)
        cf_fl.addWidget(self.tbl_cf); cfl.addWidget(cf_f)
        tabs.addTab(cf_tab, "Cash Flow")

        root.addWidget(tabs)

    def _make_report_tab(self, tabs, tab_title, headers, tbl_attr, df_attr, dt_attr,
                          load_fn, summary_attr=None):
        tab = QWidget()
        layout = QVBoxLayout(tab); layout.setContentsMargins(0,12,0,0); layout.setSpacing(12)
        dr, df, dt = _date_filter_row(df_attr, dt_attr, load_fn)
        setattr(self, df_attr, df); setattr(self, dt_attr, dt)
        refresh = btn("Refresh", PRIMARY); refresh.clicked.connect(load_fn)
        export  = btn("Export CSV", INFO)
        tbl_ref = [None]
        export.clicked.connect(lambda: self._export(tbl_ref[0], tab_title.lower().replace(" ","_")))
        dr.addWidget(refresh); dr.addWidget(export); layout.addLayout(dr)

        if summary_attr:
            sf = QFrame(); sf.setStyleSheet("QFrame{background:#EEF2FF;border-radius:8px;}")
            sl = QHBoxLayout(sf); sl.setContentsMargins(16,8,16,8)
            sum_lbl = QLabel(); sum_lbl.setStyleSheet(f"font-size:13px;font-weight:600;color:{PRIMARY};")
            sl.addWidget(sum_lbl); sl.addStretch(); layout.addWidget(sf)
            setattr(self, summary_attr, sum_lbl)

        f = card_frame(); fl = QVBoxLayout(f); fl.setContentsMargins(0,0,0,0)
        t = QTableWidget(); t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True); t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setStyleSheet(TABLE_STYLE)
        setattr(self, tbl_attr, t); tbl_ref[0] = t
        fl.addWidget(t); layout.addWidget(f)
        tabs.addTab(tab, tab_title)
        return tab

    def refresh(self):
        self._load_sales(); self._load_purchases(); self._load_pl()
        self._load_stock(); self._load_cashflow()

    def _load_sales(self):
        df = self._sr_df.date().toString("yyyy-MM-dd")
        dt = self._sr_dt.date().toString("yyyy-MM-dd")
        rows = self.db.get_sales_report(df, dt)
        self._tbl_sales.setRowCount(len(rows))
        total = sum(r["total"] for r in rows)
        paid  = sum(r["paid_amount"] for r in rows)
        due   = sum(r["due_amount"] for r in rows)
        self._sr_sum.setText(f"Records: {len(rows)}  |  Revenue: ${total:,.2f}  |  Collected: ${paid:,.2f}  |  Due: ${due:,.2f}")
        SC = {"paid":SUCCESS,"partial":WARNING,"unpaid":DANGER}
        for i, r in enumerate(rows):
            vals = [r["invoice_no"], r["customer"], r["sale_date"],
                    f"${r['subtotal']:.2f}", f"${r['discount']:.2f}", f"${r['tax_amount']:.2f}",
                    f"${r['total']:.2f}", f"${r['paid_amount']:.2f}", f"${r['due_amount']:.2f}", r["status"]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 9: item.setForeground(QColor(SC.get(v, TEXT_MID)))
                self._tbl_sales.setItem(i, c, item)

    def _load_purchases(self):
        df = self._pr_df.date().toString("yyyy-MM-dd")
        dt = self._pr_dt.date().toString("yyyy-MM-dd")
        rows = self.db.get_purchase_report(df, dt)
        self._tbl_pur.setRowCount(len(rows))
        total = sum(r["total"] for r in rows)
        paid  = sum(r["paid_amount"] for r in rows)
        due   = sum(r["due_amount"] for r in rows)
        self._pr_sum.setText(f"Records: {len(rows)}  |  Total: ${total:,.2f}  |  Paid: ${paid:,.2f}  |  Due: ${due:,.2f}")
        SC = {"paid":SUCCESS,"partial":WARNING,"unpaid":DANGER}
        for i, r in enumerate(rows):
            vals = [r["po_number"], r["supplier"], r["purchase_date"],
                    f"${r['subtotal']:.2f}", f"${r['discount']:.2f}", f"${r['tax_amount']:.2f}",
                    f"${r['total']:.2f}", f"${r['paid_amount']:.2f}", f"${r['due_amount']:.2f}", r["status"]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 9: item.setForeground(QColor(SC.get(v, TEXT_MID)))
                self._tbl_pur.setItem(i, c, item)

    def _load_pl(self):
        df = self._pl_df.date().toString("yyyy-MM-dd")
        dt = self._pl_dt.date().toString("yyyy-MM-dd")
        pl = self.db.get_profit_loss(df, dt)
        rev = pl["revenue"]; pur = pl["purchases"]; profit = pl["profit"]
        margin = (profit / rev * 100) if rev > 0 else 0
        self._pl_rev.setText(f"${rev:,.2f}")
        self._pl_pur.setText(f"${pur:,.2f}")
        self._pl_prof.setText(f"${profit:,.2f}")
        self._pl_prof.setStyleSheet(f"font-size:24px;font-weight:700;color:{SUCCESS if profit>=0 else DANGER};background:transparent;border:none;")
        self._pl_marg.setText(f"{margin:.1f}%")
        rows = [
            ("Revenue", rev, 100.0),
            ("Cost of Purchases", pur, (pur/rev*100) if rev > 0 else 0),
            ("Gross Profit", profit, margin),
            ("", "", ""),
            ("Cash Balance", self.db.get_cash_balance(), ""),
        ]
        for i, (desc, amt, pct) in enumerate(rows):
            self.tbl_pl.setItem(i, 0, QTableWidgetItem(str(desc)))
            self.tbl_pl.setItem(i, 1, QTableWidgetItem(f"${amt:,.2f}" if isinstance(amt, float) else ""))
            self.tbl_pl.setItem(i, 2, QTableWidgetItem(f"{pct:.1f}%" if isinstance(pct, float) else ""))

    def _load_stock(self):
        rows = self.db.get_stock_summary()
        self.tbl_stock.setRowCount(len(rows))
        total_val = sum(r["stock_value"] for r in rows)
        low = sum(1 for r in rows if r["stock_status"] == "Low Stock")
        out = sum(1 for r in rows if r["stock_status"] == "Out of Stock")
        self._stk_sum.setText(f"Products: {len(rows)}  |  Low Stock: {low}  |  Out of Stock: {out}  |  Total Value: ${total_val:,.2f}")
        SC = {"In Stock": SUCCESS, "Low Stock": WARNING, "Out of Stock": DANGER}
        for i, r in enumerate(rows):
            vals = [r["name"], r["sku"] or "—", r["category"] or "—", r["unit"],
                    str(r["quantity"]), str(r["min_stock"]),
                    f"${r['cost_price']:.2f}", f"${r['sale_price']:.2f}",
                    f"${r['stock_value']:.2f}", r["stock_status"]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 9:
                    item.setForeground(QColor(SC.get(v, TEXT_MID)))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.tbl_stock.setItem(i, c, item)

    def _load_cashflow(self):
        df = self._cf_df.date().toString("yyyy-MM-dd")
        dt = self._cf_dt.date().toString("yyyy-MM-dd")
        rows = self.db.get_cash_transactions(date_from=df, date_to=dt)
        self.tbl_cf.setRowCount(len(rows))
        in_amt  = sum(r["amount"] for r in rows if r["type"] in ("COLLECTION","INCOME"))
        out_amt = sum(r["amount"] for r in rows if r["type"] in ("DELIVERY","EXPENSE"))
        self._cf_sum.setText(
            f"Records: {len(rows)}  |  Cash In: ${in_amt:,.2f}  |  Cash Out: ${out_amt:,.2f}  |  Net Flow: ${in_amt-out_amt:,.2f}"
        )
        TC = {"COLLECTION":SUCCESS,"INCOME":SUCCESS,"DELIVERY":DANGER,"EXPENSE":DANGER}
        for i, r in enumerate(rows):
            vals = [str(r["id"]), r["type"], r["party_name"] or "—",
                    f"${r['amount']:,.2f}", r["description"] or "—", r["created_at"][:16]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 1: item.setForeground(QColor(TC.get(v, TEXT_MID)))
                if c == 3: item.setForeground(QColor(TC.get(r["type"], TEXT_MID)))
                self.tbl_cf.setItem(i, c, item)

    def _export(self, table, filename):
        if not table: return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", f"{filename}.csv", "CSV Files (*.csv)"
        )
        if not path: return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                headers = [table.horizontalHeaderItem(c).text()
                           for c in range(table.columnCount())]
                writer.writerow(headers)
                for r in range(table.rowCount()):
                    row = []
                    for c in range(table.columnCount()):
                        item = table.item(r, c)
                        row.append(item.text() if item else "")
                    writer.writerow(row)
            QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
