from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QTabWidget, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from styles import (btn, page_title, card_frame, search_box,
                    PRIMARY, SUCCESS, DANGER, WARNING, FIELD_STYLE, TABLE_STYLE,
                    TEXT_MID)


class CreditPage(QWidget):
    """Shows all unpaid/partial sales and purchases for quick payment collection."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._sale_rows = []; self._pur_rows = []
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(16)
        root.addWidget(page_title("Credit Management"))

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab {
                background: #E5E7EB; color: #374151; border-radius: 6px;
                padding: 7px 24px; font-size: 13px; margin-right: 4px;
            }
            QTabBar::tab:selected { background: #4F46E5; color: white; font-weight: 600; }
        """)

        # ── Tab 1: Credit Sales (Receivable) ──────────────────────────────────
        st = QWidget()
        sl = QVBoxLayout(st); sl.setContentsMargins(0,12,0,0); sl.setSpacing(12)
        sr = QHBoxLayout()
        self.sale_search = search_box("  Search invoice, customer…")
        self.sale_search.textChanged.connect(self._refresh_sales)
        sr.addWidget(self.sale_search); sr.addStretch()
        collect_btn = btn("Collect Payment", SUCCESS)
        collect_btn.clicked.connect(self._collect_sale)
        sr.addWidget(collect_btn); sl.addLayout(sr)

        # Summary
        ssf = QFrame(); ssf.setStyleSheet("QFrame{background:#FEE2E2;border-radius:8px;}")
        ssl = QHBoxLayout(ssf); ssl.setContentsMargins(16,8,16,8)
        self.lbl_recv = QLabel(); self.lbl_recv.setStyleSheet(f"font-size:13px;font-weight:600;color:{DANGER};")
        ssl.addWidget(self.lbl_recv); ssl.addStretch(); sl.addWidget(ssf)

        sf = card_frame(); sfl = QVBoxLayout(sf); sfl.setContentsMargins(0,0,0,0)
        SHEADERS = ["#","Invoice","Customer","Phone","Sale Date","Total","Paid","Due","Status"]
        self.tbl_sales = QTableWidget(); self.tbl_sales.setColumnCount(len(SHEADERS))
        self.tbl_sales.setHorizontalHeaderLabels(SHEADERS)
        self.tbl_sales.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_sales.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_sales.setAlternatingRowColors(True); self.tbl_sales.verticalHeader().setVisible(False)
        hh = self.tbl_sales.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0,QHeaderView.ResizeMode.Fixed); self.tbl_sales.setColumnWidth(0,50)
        self.tbl_sales.setStyleSheet(TABLE_STYLE)
        sfl.addWidget(self.tbl_sales); sl.addWidget(sf)
        tabs.addTab(st, "Credit Sales (Receivable)")

        # ── Tab 2: Credit Purchases (Payable) ─────────────────────────────────
        pt = QWidget()
        pl = QVBoxLayout(pt); pl.setContentsMargins(0,12,0,0); pl.setSpacing(12)
        pr = QHBoxLayout()
        self.pur_search = search_box("  Search PO, supplier…")
        self.pur_search.textChanged.connect(self._refresh_purchases)
        pr.addWidget(self.pur_search); pr.addStretch()
        pay_btn = btn("Pay Supplier", WARNING)
        pay_btn.clicked.connect(self._pay_purchase)
        pr.addWidget(pay_btn); pl.addLayout(pr)

        psf = QFrame(); psf.setStyleSheet("QFrame{background:#FEF3C7;border-radius:8px;}")
        psl = QHBoxLayout(psf); psl.setContentsMargins(16,8,16,8)
        self.lbl_pay = QLabel(); self.lbl_pay.setStyleSheet(f"font-size:13px;font-weight:600;color:#92400E;")
        psl.addWidget(self.lbl_pay); psl.addStretch(); pl.addWidget(psf)

        pf = card_frame(); pfl = QVBoxLayout(pf); pfl.setContentsMargins(0,0,0,0)
        PHEADERS = ["#","PO Number","Supplier","Phone","Date","Total","Paid","Due","Status"]
        self.tbl_pur = QTableWidget(); self.tbl_pur.setColumnCount(len(PHEADERS))
        self.tbl_pur.setHorizontalHeaderLabels(PHEADERS)
        self.tbl_pur.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_pur.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_pur.setAlternatingRowColors(True); self.tbl_pur.verticalHeader().setVisible(False)
        hh2 = self.tbl_pur.horizontalHeader()
        hh2.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh2.setSectionResizeMode(0,QHeaderView.ResizeMode.Fixed); self.tbl_pur.setColumnWidth(0,50)
        self.tbl_pur.setStyleSheet(TABLE_STYLE)
        pfl.addWidget(self.tbl_pur); pl.addWidget(pf)
        tabs.addTab(pt, "Credit Purchases (Payable)")

        root.addWidget(tabs)

    def refresh(self):
        self._refresh_sales()
        self._refresh_purchases()

    def _refresh_sales(self):
        rows = self.db.get_credit_sales(
            self.sale_search.text().strip() if hasattr(self,"sale_search") else ""
        )
        self._sale_rows = rows
        total_due = sum(r["due_amount"] for r in rows)
        self.lbl_recv.setText(
            f"Outstanding Invoices: {len(rows)}  |  Total Receivable: ${total_due:,.2f}"
        )
        SC = {"paid":SUCCESS,"partial":WARNING,"unpaid":DANGER}
        self.tbl_sales.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [str(r["id"]), r["invoice_no"], r["customer"], r["phone"] or "—",
                    r["sale_date"], f"${r['total']:.2f}",
                    f"${r['paid_amount']:.2f}", f"${r['due_amount']:.2f}", r["status"]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 8:
                    item.setForeground(QColor(SC.get(v, TEXT_MID)))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                elif c == 7:
                    item.setForeground(QColor(DANGER))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.tbl_sales.setItem(i, c, item)

    def _refresh_purchases(self):
        rows = self.db.get_credit_purchases(
            self.pur_search.text().strip() if hasattr(self,"pur_search") else ""
        )
        self._pur_rows = rows
        total_due = sum(r["due_amount"] for r in rows)
        self.lbl_pay.setText(
            f"Outstanding POs: {len(rows)}  |  Total Payable: ${total_due:,.2f}"
        )
        SC = {"paid":SUCCESS,"partial":WARNING,"unpaid":DANGER}
        self.tbl_pur.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [str(r["id"]), r["po_number"], r["supplier"], r["phone"] or "—",
                    r["purchase_date"], f"${r['total']:.2f}",
                    f"${r['paid_amount']:.2f}", f"${r['due_amount']:.2f}", r["status"]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 8:
                    item.setForeground(QColor(SC.get(v, TEXT_MID)))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                elif c == 7:
                    item.setForeground(QColor(WARNING))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.tbl_pur.setItem(i, c, item)

    def _collect_sale(self):
        r = self.tbl_sales.currentRow()
        if r < 0: QMessageBox.information(self,"Select","Select an invoice first."); return
        sale = self._sale_rows[r]
        amount, ok = QInputDialog.getDouble(
            self,"Collect Payment",
            f"Invoice: {sale['invoice_no']}\nCustomer: {sale['customer']}\n"
            f"Due: ${sale['due_amount']:.2f}\n\nAmount to collect:",
            sale["due_amount"], 0.01, sale["due_amount"], 2
        )
        if ok:
            try:
                self.db.collect_sale_payment(sale["id"], amount)
                QMessageBox.information(self,"Success",f"${amount:.2f} collected.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self,"Error",str(e))

    def _pay_purchase(self):
        r = self.tbl_pur.currentRow()
        if r < 0: QMessageBox.information(self,"Select","Select a purchase first."); return
        pur = self._pur_rows[r]
        amount, ok = QInputDialog.getDouble(
            self,"Pay Supplier",
            f"PO: {pur['po_number']}\nSupplier: {pur['supplier']}\n"
            f"Due: ${pur['due_amount']:.2f}\n\nAmount to pay:",
            pur["due_amount"], 0.01, pur["due_amount"], 2
        )
        if ok:
            try:
                self.db.pay_supplier(pur["id"], amount)
                QMessageBox.information(self,"Success",f"${amount:.2f} paid.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self,"Error",str(e))
