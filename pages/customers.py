from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, QDoubleSpinBox,
    QLineEdit, QTextEdit, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from styles import (btn, page_title, card_frame, search_box,
                    PRIMARY, SUCCESS, DANGER, WARNING, FIELD_STYLE, TABLE_STYLE, TEXT_MID)


class CustomerDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Add Customer" if data is None else "Edit Customer")
        self.setMinimumWidth(380); self.setModal(True)
        layout = QVBoxLayout(self); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        layout.addWidget(QLabel(self.windowTitle(), styleSheet="font-size:16px;font-weight:700;color:#111827;"))
        form = QFormLayout(); form.setSpacing(10)
        self.name         = QLineEdit(); self.name.setPlaceholderText("Full name")
        self.phone        = QLineEdit(); self.phone.setPlaceholderText("+1 555 000 0000")
        self.email        = QLineEdit(); self.email.setPlaceholderText("email@example.com")
        self.address      = QTextEdit(); self.address.setPlaceholderText("Address"); self.address.setMaximumHeight(60)
        self.credit_limit = QDoubleSpinBox(); self.credit_limit.setRange(0,9999999); self.credit_limit.setDecimals(2); self.credit_limit.setPrefix("$ ")
        for w in [self.name,self.phone,self.email,self.address,self.credit_limit]:
            w.setStyleSheet(FIELD_STYLE)
        form.addRow("Name *",        self.name)
        form.addRow("Phone",         self.phone)
        form.addRow("Email",         self.email)
        form.addRow("Address",       self.address)
        form.addRow("Credit Limit",  self.credit_limit)
        layout.addLayout(form)
        if data:
            self.name.setText(data.get("name",""))
            self.phone.setText(data.get("phone","") or "")
            self.email.setText(data.get("email","") or "")
            self.address.setText(data.get("address","") or "")
            self.credit_limit.setValue(data.get("credit_limit",0) or 0)
        btns = QHBoxLayout(); btns.setSpacing(8)
        c = btn("Cancel","#E5E7EB","#374151"); c.clicked.connect(self.reject)
        s = btn("Save"); s.clicked.connect(self._validate)
        btns.addWidget(c); btns.addWidget(s); layout.addLayout(btns)

    def _validate(self):
        if not self.name.text().strip(): QMessageBox.warning(self,"Validation","Name required."); return
        self.accept()

    def get_data(self):
        return dict(name=self.name.text().strip(), phone=self.phone.text().strip(),
                    email=self.email.text().strip(), address=self.address.toPlainText().strip(),
                    credit_limit=self.credit_limit.value())


class CustomerDetailDialog(QDialog):
    def __init__(self, parent, db, customer):
        super().__init__(parent)
        self.setWindowTitle(f"Statement: {customer['name']}")
        self.setMinimumSize(700, 450); self.setModal(True)
        layout = QVBoxLayout(self); layout.setContentsMargins(20,16,20,16); layout.setSpacing(10)

        # Summary row
        sr = QHBoxLayout()
        for label, val, color in [
            ("Outstanding Balance", f"${customer['balance']:.2f}", DANGER if customer['balance'] > 0 else SUCCESS),
            ("Credit Limit", f"${customer['credit_limit']:.2f}", PRIMARY),
        ]:
            f = QFrame(); f.setStyleSheet(f"background:#F9FAFB;border-radius:8px;")
            fl = QVBoxLayout(f); fl.setContentsMargins(12,8,12,8); fl.setSpacing(2)
            fl.addWidget(QLabel(label, styleSheet=f"font-size:11px;color:#6B7280;"))
            fl.addWidget(QLabel(val, styleSheet=f"font-size:18px;font-weight:700;color:{color};"))
            sr.addWidget(f)
        sr.addStretch(); layout.addLayout(sr)

        t = QTableWidget(); t.setColumnCount(7)
        t.setHorizontalHeaderLabels(["Ref","Date","Type","Total","Paid","Due","Status"])
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True); t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setStyleSheet(TABLE_STYLE)
        layout.addWidget(t)
        txs = db.get_customer_transactions(customer["id"])
        t.setRowCount(len(txs))
        SC = {"paid":"#059669","partial":"#D97706","unpaid":"#DC2626"}
        for r, row in enumerate(txs):
            vals = [row[0], row[1], row[6], f"${row[2]:.2f}", f"${row[3]:.2f}",
                    f"${row[4]:.2f}", row[5]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 6: item.setForeground(QColor(SC.get(v,"#374151")))
                t.setItem(r, c, item)
        close = btn("Close","#E5E7EB","#374151"); close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)


class CustomersPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db; self._rows = []
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(16)
        hr = QHBoxLayout()
        hr.addWidget(page_title("Customers")); hr.addStretch()
        self.search = search_box("  Search name, phone…")
        self.search.textChanged.connect(self.refresh); hr.addWidget(self.search)
        a = btn("+ Add Customer"); a.clicked.connect(self.add_customer); hr.addWidget(a)
        root.addLayout(hr)

        # Summary strip
        sf = QFrame(); sf.setStyleSheet("QFrame{background:#EEF2FF;border-radius:8px;}")
        sl = QHBoxLayout(sf); sl.setContentsMargins(16,8,16,8)
        self.lbl_total = QLabel(); self.lbl_recv = QLabel()
        for l in [self.lbl_total, self.lbl_recv]:
            l.setStyleSheet("font-size:13px;font-weight:600;color:#4F46E5;")
        sl.addWidget(self.lbl_total); sl.addWidget(QLabel("  |  ")); sl.addWidget(self.lbl_recv)
        sl.addStretch(); root.addWidget(sf)

        f = card_frame(); fl = QVBoxLayout(f); fl.setContentsMargins(0,0,0,0)
        HEADERS = ["#","Name","Phone","Email","Address","Credit Limit","Balance","Joined"]
        self.table = QTableWidget(); self.table.setColumnCount(len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True); self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0,QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(0,50)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.doubleClicked.connect(self.view_statement)
        fl.addWidget(self.table); root.addWidget(f)

        ar = QHBoxLayout(); ar.setSpacing(8); ar.addStretch()
        stmt = btn("Statement", PRIMARY); stmt.clicked.connect(self.view_statement)
        e = btn("Edit", SUCCESS); e.clicked.connect(self.edit_customer)
        d = btn("Delete", DANGER); d.clicked.connect(self.delete_customer)
        ar.addWidget(stmt); ar.addWidget(e); ar.addWidget(d); root.addLayout(ar)

    def refresh(self):
        rows = self.db.get_all_customers(self.search.text().strip())
        self._rows = rows
        self.table.setRowCount(len(rows))
        total_bal = sum(r["balance"] for r in rows if r["balance"] > 0)
        self.lbl_total.setText(f"Total Customers: {len(rows)}")
        self.lbl_recv.setText(f"Total Receivable: ${total_bal:,.2f}")
        for i, r in enumerate(rows):
            vals = [str(r["id"]), r["name"], r["phone"] or "—", r["email"] or "—",
                    (r["address"] or "—")[:30], f"${r['credit_limit']:.2f}",
                    f"${r['balance']:.2f}", r["created_at"][:10]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 6 and r["balance"] > 0:
                    item.setForeground(QColor(DANGER)); item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.table.setItem(i, c, item)

    def _selected(self):
        r = self.table.currentRow()
        if r < 0: QMessageBox.information(self,"Select","Select a customer first."); return None
        return self._rows[r]

    def view_statement(self):
        row = self._selected()
        if row: CustomerDetailDialog(self, self.db, row).exec()

    def add_customer(self):
        dlg = CustomerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try: self.db.add_customer(**dlg.get_data()); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Error",str(e))

    def edit_customer(self):
        row = self._selected()
        if not row: return
        dlg = CustomerDialog(self, dict(row))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try: self.db.update_customer(row["id"], **dlg.get_data()); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Error",str(e))

    def delete_customer(self):
        row = self._selected()
        if not row: return
        if QMessageBox.question(self,"Delete",f"Delete '{row['name']}'?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.delete_customer(row["id"]); self.refresh()
