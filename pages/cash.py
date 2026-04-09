from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, QComboBox,
    QDoubleSpinBox, QTextEdit, QTabWidget, QDateEdit, QLineEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from styles import (btn, page_title, card_frame, search_box,
                    PRIMARY, SUCCESS, DANGER, WARNING, INFO, ORANGE,
                    FIELD_STYLE, TABLE_STYLE, TEXT_DARK, TEXT_MID, TEXT_LIGHT)


class ManualTxDialog(QDialog):
    """Add income or expense manually."""
    def __init__(self, parent, tx_type="INCOME"):
        super().__init__(parent)
        self.tx_type = tx_type
        color = SUCCESS if tx_type == "INCOME" else DANGER
        self.setWindowTitle("Add Income" if tx_type == "INCOME" else "Add Expense")
        self.setMinimumWidth(360); self.setModal(True)
        layout = QVBoxLayout(self); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        layout.addWidget(QLabel(self.windowTitle(), styleSheet=f"font-size:16px;font-weight:700;color:{color};"))
        form = QFormLayout(); form.setSpacing(10)
        self.amount = QDoubleSpinBox(); self.amount.setRange(0.01,9999999)
        self.amount.setDecimals(2); self.amount.setPrefix("$ ")
        self.amount.setStyleSheet(FIELD_STYLE)
        self.desc = QTextEdit(); self.desc.setPlaceholderText("Description")
        self.desc.setMaximumHeight(70); self.desc.setStyleSheet(FIELD_STYLE)
        form.addRow("Amount *",      self.amount)
        form.addRow("Description *", self.desc)
        layout.addLayout(form)
        btns = QHBoxLayout(); btns.setSpacing(8)
        c = btn("Cancel","#E5E7EB","#374151"); c.clicked.connect(self.reject)
        s = btn("Save", color); s.clicked.connect(self._validate)
        btns.addWidget(c); btns.addWidget(s); layout.addLayout(btns)

    def _validate(self):
        if not self.desc.toPlainText().strip():
            QMessageBox.warning(self,"Validation","Description required."); return
        self.accept()

    def get_data(self):
        return dict(tx_type=self.tx_type, amount=self.amount.value(),
                    description=self.desc.toPlainText().strip())


class CashPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db; self._rows = []
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(16)

        # Title + cash balance
        hr = QHBoxLayout()
        hr.addWidget(page_title("Cash Management")); hr.addStretch()
        self.lbl_balance = QLabel()
        self.lbl_balance.setStyleSheet(f"font-size:18px;font-weight:700;color:{SUCCESS};")
        hr.addWidget(self.lbl_balance); root.addLayout(hr)

        # Quick-action buttons
        qa = QHBoxLayout(); qa.setSpacing(10)
        inc = btn("+ Add Income",  SUCCESS); inc.clicked.connect(lambda: self._manual("INCOME"))
        exp = btn("- Add Expense", DANGER);  exp.clicked.connect(lambda: self._manual("EXPENSE"))
        qa.addWidget(inc); qa.addWidget(exp); qa.addStretch(); root.addLayout(qa)

        # Filters
        fr = QHBoxLayout(); fr.setSpacing(8)
        self.search = search_box("  Search…", 180)
        self.search.textChanged.connect(self.refresh)
        fr.addWidget(self.search)

        self.type_filter = QComboBox(); self.type_filter.setFixedWidth(140)
        self.type_filter.setStyleSheet(FIELD_STYLE)
        self.type_filter.addItem("All Types", None)
        for t in ["COLLECTION","DELIVERY","INCOME","EXPENSE"]:
            self.type_filter.addItem(t.title(), t)
        self.type_filter.currentIndexChanged.connect(self.refresh)
        fr.addWidget(self.type_filter)

        self.df = QDateEdit(QDate.currentDate().addMonths(-1))
        self.dt = QDateEdit(QDate.currentDate())
        for d in [self.df, self.dt]:
            d.setStyleSheet(FIELD_STYLE); d.setCalendarPopup(True); d.setFixedWidth(115)
            d.dateChanged.connect(self.refresh)
        fr.addWidget(QLabel("From:")); fr.addWidget(self.df)
        fr.addWidget(QLabel("To:")); fr.addWidget(self.dt)
        fr.addStretch(); root.addLayout(fr)

        # Summary strip
        sf = QFrame(); sf.setStyleSheet("QFrame{background:#F0FDF4;border-radius:8px;}")
        sl = QHBoxLayout(sf); sl.setContentsMargins(16,8,16,8)
        self.lbl_sum = QLabel(); self.lbl_sum.setStyleSheet(f"font-size:13px;font-weight:600;color:{SUCCESS};")
        sl.addWidget(self.lbl_sum); sl.addStretch(); root.addWidget(sf)

        # Table
        f = card_frame(); fl = QVBoxLayout(f); fl.setContentsMargins(0,0,0,0)
        HEADERS = ["#","Type","Party","Amount","Description","Date/Time"]
        self.table = QTableWidget(); self.table.setColumnCount(len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True); self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0,QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(0,50)
        self.table.setStyleSheet(TABLE_STYLE)
        fl.addWidget(self.table); root.addWidget(f)

    def refresh(self):
        df = self.df.date().toString("yyyy-MM-dd")
        dt = self.dt.date().toString("yyyy-MM-dd")
        rows = self.db.get_cash_transactions(
            self.search.text().strip(), self.type_filter.currentData(), df, dt
        )
        self._rows = rows
        self.table.setRowCount(len(rows))

        in_amt  = sum(r["amount"] for r in rows if r["type"] in ("COLLECTION","INCOME"))
        out_amt = sum(r["amount"] for r in rows if r["type"] in ("DELIVERY","EXPENSE"))
        self.lbl_sum.setText(
            f"Records: {len(rows)}  |  Cash In: ${in_amt:,.2f}  |  Cash Out: ${out_amt:,.2f}  |  Net: ${in_amt-out_amt:,.2f}"
        )
        bal = self.db.get_cash_balance()
        self.lbl_balance.setText(f"Cash Balance: ${bal:,.2f}")

        TYPE_COLOR = {
            "COLLECTION": SUCCESS, "INCOME": SUCCESS,
            "DELIVERY": DANGER,    "EXPENSE": DANGER,
        }
        for i, r in enumerate(rows):
            color = TYPE_COLOR.get(r["type"], TEXT_MID)
            vals = [str(r["id"]), r["type"], r["party_name"] or "—",
                    f"${r['amount']:,.2f}", r["description"] or "—", r["created_at"][:16]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c in (1, 3):
                    item.setForeground(QColor(color))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.table.setItem(i, c, item)

    def _manual(self, tx_type):
        dlg = ManualTxDialog(self, tx_type)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                self.db.add_manual_cash_transaction(**d)
                self.refresh()
                QMessageBox.information(self,"Done",f"${d['amount']:.2f} recorded.")
            except Exception as e:
                QMessageBox.critical(self,"Error",str(e))
