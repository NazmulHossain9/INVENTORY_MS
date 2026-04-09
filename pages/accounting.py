from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QTabWidget, QDialog, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from styles import (btn, page_title, card_frame, search_box,
                    PRIMARY, SUCCESS, DANGER, WARNING, INFO, PURPLE, ORANGE,
                    FIELD_STYLE, TABLE_STYLE, TEXT_DARK, TEXT_MID, TEXT_LIGHT, BG_CARD)


ACCOUNT_TYPE_COLOR = {
    "ASSET":    PRIMARY,
    "LIABILITY": DANGER,
    "EQUITY":   PURPLE,
    "REVENUE":  SUCCESS,
    "EXPENSE":  WARNING,
}


class JournalDetailDialog(QDialog):
    def __init__(self, parent, db, entry):
        super().__init__(parent)
        self.setWindowTitle(f"Journal Entry: {entry['entry_no']}")
        self.setMinimumSize(580, 360); self.setModal(True)
        layout = QVBoxLayout(self); layout.setContentsMargins(20,16,20,16); layout.setSpacing(10)

        hr = QHBoxLayout()
        hr.addWidget(QLabel(entry["entry_no"], styleSheet=f"font-size:15px;font-weight:700;color:{PRIMARY};"))
        hr.addWidget(QLabel(entry["description"], styleSheet=f"color:{TEXT_MID};font-size:13px;"))
        hr.addStretch(); layout.addLayout(hr)
        layout.addWidget(QLabel(f"Date: {entry['entry_date']}  |  Ref: {entry['reference_type'] or '—'}",
                                 styleSheet=f"color:{TEXT_LIGHT};font-size:12px;"))

        lines = db.get_journal_lines(entry["id"])
        t = QTableWidget(len(lines), 4)
        t.setHorizontalHeaderLabels(["Account Code","Account Name","Debit","Credit"])
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True); t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setStyleSheet(TABLE_STYLE)
        total_dr = total_cr = 0
        for r, line in enumerate(lines):
            total_dr += line["debit"]; total_cr += line["credit"]
            for c, v in enumerate([line["code"], line["account_name"],
                                   f"${line['debit']:.2f}" if line["debit"] else "—",
                                   f"${line['credit']:.2f}" if line["credit"] else "—"]):
                item = QTableWidgetItem(v)
                if c == 2 and line["debit"]: item.setForeground(QColor(SUCCESS))
                if c == 3 and line["credit"]: item.setForeground(QColor(DANGER))
                t.setItem(r, c, item)
        layout.addWidget(t)

        sf = QFrame(); sf.setStyleSheet("background:#F9FAFB;border-radius:6px;")
        sl = QHBoxLayout(sf); sl.setContentsMargins(16,8,16,8)
        sl.addWidget(QLabel(f"Total Debit: ${total_dr:.2f}",
            styleSheet=f"font-weight:600;color:{SUCCESS};"))
        sl.addSpacing(30)
        sl.addWidget(QLabel(f"Total Credit: ${total_cr:.2f}",
            styleSheet=f"font-weight:600;color:{DANGER};"))
        sl.addStretch(); layout.addWidget(sf)

        c = btn("Close","#E5E7EB","#374151"); c.clicked.connect(self.accept)
        layout.addWidget(c, alignment=Qt.AlignmentFlag.AlignRight)


class AccountingPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._journal_rows = []
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(16)
        root.addWidget(page_title("Accounting & Ledger"))

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab {
                background: #E5E7EB; color: #374151; border-radius: 6px;
                padding: 7px 22px; font-size: 13px; margin-right: 4px;
            }
            QTabBar::tab:selected { background: #4F46E5; color: white; font-weight: 600; }
        """)

        # ── Tab 1: Chart of Accounts ───────────────────────────────────────────
        coa_tab = QWidget()
        cl = QVBoxLayout(coa_tab); cl.setContentsMargins(0,12,0,0); cl.setSpacing(12)

        # Account type summary cards
        cards_row = QHBoxLayout(); cards_row.setSpacing(12)
        self._type_cards = {}
        for acct_type in ["ASSET","LIABILITY","EQUITY","REVENUE","EXPENSE"]:
            f = QFrame(); f.setStyleSheet(f"""
                QFrame{{background:{BG_CARD};border-radius:10px;
                        border-left:4px solid {ACCOUNT_TYPE_COLOR[acct_type]};}}
            """)
            fl = QVBoxLayout(f); fl.setContentsMargins(12,10,12,10); fl.setSpacing(2)
            fl.addWidget(QLabel(acct_type, styleSheet=f"font-size:10px;font-weight:600;color:{TEXT_LIGHT};background:transparent;border:none;"))
            v = QLabel("$0.00"); v.setStyleSheet(f"font-size:16px;font-weight:700;color:{ACCOUNT_TYPE_COLOR[acct_type]};background:transparent;border:none;")
            fl.addWidget(v); cards_row.addWidget(f)
            self._type_cards[acct_type] = v
        cl.addLayout(cards_row)

        cf = card_frame(); cfl = QVBoxLayout(cf); cfl.setContentsMargins(0,0,0,0)
        HEADERS = ["Code","Account","Type","Normal Bal","Debit Total","Credit Total","Balance"]
        self.tbl_coa = QTableWidget(); self.tbl_coa.setColumnCount(len(HEADERS))
        self.tbl_coa.setHorizontalHeaderLabels(HEADERS)
        self.tbl_coa.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_coa.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_coa.setAlternatingRowColors(True); self.tbl_coa.verticalHeader().setVisible(False)
        self.tbl_coa.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_coa.setStyleSheet(TABLE_STYLE)
        cfl.addWidget(self.tbl_coa); cl.addWidget(cf)
        tabs.addTab(coa_tab, "Chart of Accounts")

        # ── Tab 2: Trial Balance ───────────────────────────────────────────────
        tb_tab = QWidget()
        tbl = QVBoxLayout(tb_tab); tbl.setContentsMargins(0,12,0,0); tbl.setSpacing(12)

        tsf = QFrame(); tsf.setStyleSheet("QFrame{background:#EEF2FF;border-radius:8px;}")
        tsl = QHBoxLayout(tsf); tsl.setContentsMargins(16,8,16,8)
        self.lbl_tb_totals = QLabel()
        self.lbl_tb_totals.setStyleSheet(f"font-size:13px;font-weight:600;color:{PRIMARY};")
        tsl.addWidget(self.lbl_tb_totals); tsl.addStretch(); tbl.addWidget(tsf)

        tbf = card_frame(); tbfl = QVBoxLayout(tbf); tbfl.setContentsMargins(0,0,0,0)
        TB_HEADERS = ["Code","Account","Type","Debit","Credit"]
        self.tbl_tb = QTableWidget(); self.tbl_tb.setColumnCount(len(TB_HEADERS))
        self.tbl_tb.setHorizontalHeaderLabels(TB_HEADERS)
        self.tbl_tb.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_tb.setAlternatingRowColors(True); self.tbl_tb.verticalHeader().setVisible(False)
        self.tbl_tb.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_tb.setStyleSheet(TABLE_STYLE)
        tbfl.addWidget(self.tbl_tb); tbl.addWidget(tbf)
        tabs.addTab(tb_tab, "Trial Balance")

        # ── Tab 3: Journal Entries ─────────────────────────────────────────────
        je_tab = QWidget()
        jl = QVBoxLayout(je_tab); jl.setContentsMargins(0,12,0,0); jl.setSpacing(12)
        jr = QHBoxLayout()
        self.je_search = search_box("  Search entry no, description…")
        self.je_search.textChanged.connect(self._refresh_journal)
        jr.addWidget(self.je_search)
        self.je_df = QDateEdit(QDate.currentDate().addMonths(-1))
        self.je_dt = QDateEdit(QDate.currentDate())
        for d in [self.je_df, self.je_dt]:
            d.setStyleSheet(FIELD_STYLE); d.setCalendarPopup(True); d.setFixedWidth(115)
            d.dateChanged.connect(self._refresh_journal)
        jr.addWidget(QLabel("From:")); jr.addWidget(self.je_df)
        jr.addWidget(QLabel("To:")); jr.addWidget(self.je_dt)
        jr.addStretch()
        view_btn = btn("View Lines", INFO); view_btn.clicked.connect(self._view_journal)
        jr.addWidget(view_btn); jl.addLayout(jr)

        jf = card_frame(); jfl = QVBoxLayout(jf); jfl.setContentsMargins(0,0,0,0)
        JE_HEADERS = ["#","Entry No","Date","Description","Reference","Total DR","Total CR"]
        self.tbl_je = QTableWidget(); self.tbl_je.setColumnCount(len(JE_HEADERS))
        self.tbl_je.setHorizontalHeaderLabels(JE_HEADERS)
        self.tbl_je.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_je.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_je.setAlternatingRowColors(True); self.tbl_je.verticalHeader().setVisible(False)
        hh = self.tbl_je.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0,QHeaderView.ResizeMode.Fixed); self.tbl_je.setColumnWidth(0,50)
        self.tbl_je.setStyleSheet(TABLE_STYLE)
        self.tbl_je.doubleClicked.connect(self._view_journal)
        jfl.addWidget(self.tbl_je); jl.addWidget(jf)
        tabs.addTab(je_tab, "Journal Entries")

        root.addWidget(tabs)

    def refresh(self):
        self._refresh_coa()
        self._refresh_trial_balance()
        self._refresh_journal()

    def _refresh_coa(self):
        accounts = self.db.get_all_accounts()
        type_totals = {t: 0.0 for t in ACCOUNT_TYPE_COLOR}
        self.tbl_coa.setRowCount(len(accounts))
        for i, acct in enumerate(accounts):
            dr, cr = self.db.get_account_balance(acct["id"])
            if acct["normal_balance"] == "DR":
                balance = dr - cr
            else:
                balance = cr - dr
            type_totals[acct["account_type"]] = type_totals.get(acct["account_type"], 0) + balance
            color = ACCOUNT_TYPE_COLOR.get(acct["account_type"], TEXT_MID)
            vals = [acct["code"], acct["name"], acct["account_type"],
                    acct["normal_balance"], f"${dr:.2f}", f"${cr:.2f}", f"${balance:.2f}"]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 2: item.setForeground(QColor(color))
                if c == 6:
                    item.setForeground(QColor(SUCCESS if balance >= 0 else DANGER))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.tbl_coa.setItem(i, c, item)
        for t, v in type_totals.items():
            if t in self._type_cards:
                self._type_cards[t].setText(f"${v:,.2f}")

    def _refresh_trial_balance(self):
        rows = self.db.get_trial_balance()
        self.tbl_tb.setRowCount(len(rows))
        total_dr = total_cr = 0
        for i, r in enumerate(rows):
            total_dr += r["total_dr"]; total_cr += r["total_cr"]
            color = ACCOUNT_TYPE_COLOR.get(r["account_type"], TEXT_MID)
            for c, v in enumerate([r["code"], r["name"], r["account_type"],
                                    f"${r['total_dr']:.2f}", f"${r['total_cr']:.2f}"]):
                item = QTableWidgetItem(v)
                if c == 2: item.setForeground(QColor(color))
                if c == 3 and r["total_dr"]: item.setForeground(QColor(SUCCESS))
                if c == 4 and r["total_cr"]: item.setForeground(QColor(DANGER))
                self.tbl_tb.setItem(i, c, item)
        balanced = abs(total_dr - total_cr) < 0.01
        self.lbl_tb_totals.setText(
            f"Total Debit: ${total_dr:,.2f}  |  Total Credit: ${total_cr:,.2f}  |  "
            f"{'✓ BALANCED' if balanced else '⚠ NOT BALANCED'}"
        )
        self.lbl_tb_totals.setStyleSheet(
            f"font-size:13px;font-weight:600;color:{SUCCESS if balanced else DANGER};"
        )

    def _refresh_journal(self):
        search = self.je_search.text().strip() if hasattr(self,"je_search") else ""
        df = self.je_df.date().toString("yyyy-MM-dd") if hasattr(self,"je_df") else None
        dt = self.je_dt.date().toString("yyyy-MM-dd") if hasattr(self,"je_dt") else None
        rows = self.db.get_journal_entries(search, df, dt)
        self._journal_rows = rows
        self.tbl_je.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for c, v in enumerate([str(r["id"]), r["entry_no"], r["entry_date"],
                                    r["description"], r["reference_type"] or "—",
                                    f"${r['total_dr']:.2f}", f"${r['total_cr']:.2f}"]):
                item = QTableWidgetItem(v)
                if c == 5: item.setForeground(QColor(SUCCESS))
                if c == 6: item.setForeground(QColor(DANGER))
                self.tbl_je.setItem(i, c, item)

    def _view_journal(self):
        r = self.tbl_je.currentRow()
        if r < 0: return
        entry = self._journal_rows[r]
        JournalDetailDialog(self, self.db, entry).exec()
