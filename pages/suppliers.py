from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame,
    QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from styles import (btn, page_title, card_frame, search_box,
                    PRIMARY, SUCCESS, DANGER, FIELD_STYLE, TABLE_STYLE)


class SupplierDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Add Supplier" if data is None else "Edit Supplier")
        self.setMinimumWidth(380); self.setModal(True)
        layout = QVBoxLayout(self); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        layout.addWidget(QLabel(self.windowTitle(), styleSheet="font-size:16px;font-weight:700;color:#111827;"))
        form = QFormLayout(); form.setSpacing(10)
        self.name    = QLineEdit(); self.name.setPlaceholderText("Company name")
        self.contact = QLineEdit(); self.contact.setPlaceholderText("Contact person")
        self.phone   = QLineEdit(); self.phone.setPlaceholderText("+1 555 000 0000")
        self.email   = QLineEdit(); self.email.setPlaceholderText("email@example.com")
        self.address = QTextEdit(); self.address.setPlaceholderText("Address"); self.address.setMaximumHeight(60)
        for w in [self.name,self.contact,self.phone,self.email,self.address]:
            w.setStyleSheet(FIELD_STYLE)
        form.addRow("Name *",   self.name)
        form.addRow("Contact",  self.contact)
        form.addRow("Phone",    self.phone)
        form.addRow("Email",    self.email)
        form.addRow("Address",  self.address)
        layout.addLayout(form)
        if data:
            self.name.setText(data.get("name",""))
            self.contact.setText(data.get("contact","") or "")
            self.phone.setText(data.get("phone","") or "")
            self.email.setText(data.get("email","") or "")
            self.address.setText(data.get("address","") or "")
        btns = QHBoxLayout(); btns.setSpacing(8)
        c = btn("Cancel","#E5E7EB","#374151"); c.clicked.connect(self.reject)
        s = btn("Save"); s.clicked.connect(self._validate)
        btns.addWidget(c); btns.addWidget(s); layout.addLayout(btns)

    def _validate(self):
        if not self.name.text().strip(): QMessageBox.warning(self,"Validation","Name required."); return
        self.accept()

    def get_data(self):
        return dict(name=self.name.text().strip(), contact=self.contact.text().strip(),
                    phone=self.phone.text().strip(), email=self.email.text().strip(),
                    address=self.address.toPlainText().strip())


class SupplierDetailDialog(QDialog):
    def __init__(self, parent, db, supplier):
        super().__init__(parent)
        self.setWindowTitle(f"Statement: {supplier['name']}")
        self.setMinimumSize(700,450); self.setModal(True)
        layout = QVBoxLayout(self); layout.setContentsMargins(20,16,20,16); layout.setSpacing(10)
        sr = QHBoxLayout()
        f = QFrame(); f.setStyleSheet("background:#FEF2F2;border-radius:8px;")
        fl = QVBoxLayout(f); fl.setContentsMargins(12,8,12,8); fl.setSpacing(2)
        fl.addWidget(QLabel("Outstanding Payable", styleSheet="font-size:11px;color:#6B7280;"))
        fl.addWidget(QLabel(f"${supplier['balance']:.2f}",
            styleSheet=f"font-size:18px;font-weight:700;color:{DANGER if supplier['balance']>0 else SUCCESS};"))
        sr.addWidget(f); sr.addStretch(); layout.addLayout(sr)

        t = QTableWidget(); t.setColumnCount(7)
        t.setHorizontalHeaderLabels(["Ref","Date","Type","Total","Paid","Due","Status"])
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True); t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setStyleSheet(TABLE_STYLE); layout.addWidget(t)
        txs = db.get_supplier_transactions(supplier["id"])
        t.setRowCount(len(txs))
        SC = {"paid":"#059669","partial":"#D97706","unpaid":"#DC2626"}
        for r, row in enumerate(txs):
            vals = [row[0], row[1], row[6], f"${row[2]:.2f}", f"${row[3]:.2f}", f"${row[4]:.2f}", row[5]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 6: item.setForeground(QColor(SC.get(v,"#374151")))
                t.setItem(r, c, item)
        close = btn("Close","#E5E7EB","#374151"); close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)


class SuppliersPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db; self._rows = []
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(16)
        hr = QHBoxLayout()
        hr.addWidget(page_title("Suppliers")); hr.addStretch()
        self.search = search_box("  Search name, phone…")
        self.search.textChanged.connect(self.refresh); hr.addWidget(self.search)
        a = btn("+ Add Supplier"); a.clicked.connect(self.add_supplier); hr.addWidget(a)
        root.addLayout(hr)

        sf = QFrame(); sf.setStyleSheet("QFrame{background:#FEF3C7;border-radius:8px;}")
        sl = QHBoxLayout(sf); sl.setContentsMargins(16,8,16,8)
        self.lbl_total = QLabel(); self.lbl_payable = QLabel()
        for l in [self.lbl_total, self.lbl_payable]:
            l.setStyleSheet("font-size:13px;font-weight:600;color:#92400E;")
        sl.addWidget(self.lbl_total); sl.addWidget(QLabel("  |  ")); sl.addWidget(self.lbl_payable)
        sl.addStretch(); root.addWidget(sf)

        f = card_frame(); fl = QVBoxLayout(f); fl.setContentsMargins(0,0,0,0)
        HEADERS = ["#","Name","Contact","Phone","Email","Address","Balance","Joined"]
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
        e = btn("Edit", SUCCESS); e.clicked.connect(self.edit_supplier)
        d = btn("Delete", DANGER); d.clicked.connect(self.delete_supplier)
        ar.addWidget(stmt); ar.addWidget(e); ar.addWidget(d); root.addLayout(ar)

    def refresh(self):
        rows = self.db.get_all_suppliers(self.search.text().strip())
        self._rows = rows
        self.table.setRowCount(len(rows))
        total_pay = sum(r["balance"] for r in rows if r["balance"] > 0)
        self.lbl_total.setText(f"Total Suppliers: {len(rows)}")
        self.lbl_payable.setText(f"Total Payable: ${total_pay:,.2f}")
        for i, r in enumerate(rows):
            vals = [str(r["id"]), r["name"], r["contact"] or "—", r["phone"] or "—",
                    r["email"] or "—", (r["address"] or "—")[:30],
                    f"${r['balance']:.2f}", r["created_at"][:10]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 6 and r["balance"] > 0:
                    item.setForeground(QColor(DANGER)); item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.table.setItem(i, c, item)

    def _selected(self):
        r = self.table.currentRow()
        if r < 0: QMessageBox.information(self,"Select","Select a supplier first."); return None
        return self._rows[r]

    def view_statement(self):
        row = self._selected()
        if row: SupplierDetailDialog(self, self.db, row).exec()

    def add_supplier(self):
        dlg = SupplierDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try: self.db.add_supplier(**dlg.get_data()); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Error",str(e))

    def edit_supplier(self):
        row = self._selected()
        if not row: return
        dlg = SupplierDialog(self, dict(row))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try: self.db.update_supplier(row["id"], **dlg.get_data()); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Error",str(e))

    def delete_supplier(self):
        row = self._selected()
        if not row: return
        if QMessageBox.question(self,"Delete",f"Delete '{row['name']}'?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.delete_supplier(row["id"]); self.refresh()
