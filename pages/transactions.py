from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QDialog, QFormLayout, QMessageBox, QFrame, QComboBox,
    QSpinBox, QDoubleSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


def _btn(text, color="#4F46E5", text_color="white"):
    b = QPushButton(text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color}; color: {text_color};
            border: none; border-radius: 6px;
            padding: 7px 16px; font-size: 13px; font-weight: 600;
        }}
        QPushButton:hover {{ opacity: 0.85; }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


FIELD_STYLE = """
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox {
        border: 1.5px solid #E5E7EB; border-radius: 6px;
        padding: 5px 10px; font-size: 13px; color: #111827; background: #FAFAFA;
        min-height: 28px;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
    QDoubleSpinBox:focus, QSpinBox:focus { border-color: #4F46E5; background: white; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { border: 1px solid #E5E7EB; selection-background-color: #EEF2FF; }
"""


class TransactionDialog(QDialog):
    def __init__(self, parent, db, tx_type="IN"):
        super().__init__(parent)
        self.db = db
        self.tx_type = tx_type
        self.setWindowTitle(f"Stock {'In' if tx_type == 'IN' else 'Out'}")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        color = "#16A34A" if tx_type == "IN" else "#DC2626"
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {color};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.product = QComboBox()
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 999999)
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 9999999)
        self.price.setDecimals(2)
        self.price.setPrefix("$ ")
        self.note = QTextEdit()
        self.note.setPlaceholderText("Optional note…")
        self.note.setMaximumHeight(70)

        for w in [self.product, self.quantity, self.price, self.note]:
            w.setStyleSheet(FIELD_STYLE)

        self._products = list(db.get_all_products())
        for p in self._products:
            label = f"{p['name']}  (Stock: {p['quantity']} {p['unit']})"
            self.product.addItem(label, p["id"])

        form.addRow("Product *",  self.product)
        form.addRow("Quantity *", self.quantity)
        form.addRow("Unit Price", self.price)
        form.addRow("Note",       self.note)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        cancel = _btn("Cancel", "#E5E7EB", "#374151")
        cancel.clicked.connect(self.reject)
        save = _btn(f"Confirm {'In' if tx_type == 'IN' else 'Out'}", color)
        save.clicked.connect(self._validate)
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _validate(self):
        if not self._products:
            QMessageBox.warning(self, "No Products", "Add products before recording transactions.")
            return
        self.accept()

    def get_data(self):
        return dict(
            product_id = self.product.currentData(),
            tx_type    = self.tx_type,
            quantity   = self.quantity.value(),
            price      = self.price.value(),
            note       = self.note.toPlainText().strip(),
        )


class TransactionsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Stock Transactions")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #111827;")
        header_row.addWidget(title)
        header_row.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("  Search product, note…")
        self.search.setFixedWidth(200)
        self.search.setStyleSheet("""
            QLineEdit { border: 1.5px solid #E5E7EB; border-radius: 6px;
                        padding: 6px 10px; font-size: 13px; background: white; }
            QLineEdit:focus { border-color: #4F46E5; }
        """)
        self.search.textChanged.connect(self.refresh)
        header_row.addWidget(self.search)

        self.type_filter = QComboBox()
        self.type_filter.setFixedWidth(120)
        self.type_filter.setStyleSheet(FIELD_STYLE)
        self.type_filter.addItem("All Types", None)
        self.type_filter.addItem("Stock In",  "IN")
        self.type_filter.addItem("Stock Out", "OUT")
        self.type_filter.currentIndexChanged.connect(self.refresh)
        header_row.addWidget(self.type_filter)

        in_btn  = _btn("+ Stock In",  "#16A34A")
        out_btn = _btn("- Stock Out", "#DC2626")
        in_btn.clicked.connect(lambda: self.record_transaction("IN"))
        out_btn.clicked.connect(lambda: self.record_transaction("OUT"))
        header_row.addWidget(in_btn)
        header_row.addWidget(out_btn)
        root.addLayout(header_row)

        # Summary strip
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        root.addWidget(self.summary_label)

        # Table
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: white; border-radius: 12px; }")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)

        HEADERS = ["#", "Product", "SKU", "Type", "Qty", "Unit Price", "Total", "Note", "Date/Time"]
        self.table = QTableWidget()
        self.table.setColumnCount(len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setStyleSheet("""
            QTableWidget { border: none; background: transparent; gridline-color: #F3F4F6; font-size: 13px; }
            QTableWidget::item { padding: 8px 6px; color: #374151; }
            QHeaderView::section { background: #F9FAFB; color: #6B7280; font-weight: 600;
                                   font-size: 12px; border: none; padding: 8px 6px;
                                   border-bottom: 1px solid #E5E7EB; }
            QTableWidget::item:alternate { background: #FAFAFA; }
            QTableWidget::item:selected { background: #EEF2FF; color: #4F46E5; }
        """)
        fl.addWidget(self.table)
        root.addWidget(frame)

    def refresh(self):
        search  = self.search.text().strip()
        tx_type = self.type_filter.currentData()
        rows = self.db.get_all_transactions(search, tx_type)
        self._rows = rows
        self.table.setRowCount(len(rows))

        total_in = total_out = 0
        for i, row in enumerate(rows):
            total = (row["price"] or 0) * row["quantity"]
            if row["type"] == "IN":
                total_in += row["quantity"]
            else:
                total_out += row["quantity"]

            vals = [
                str(row["id"]), row["product"], row["sku"] or "—",
                row["type"], str(row["quantity"]),
                f"${row['price']:.2f}" if row["price"] else "—",
                f"${total:.2f}", row["note"] or "—", row["created_at"][:16],
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 3:
                    item.setForeground(QColor("#16A34A") if v == "IN" else QColor("#DC2626"))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.table.setItem(i, c, item)

        self.summary_label.setText(
            f"Showing {len(rows)} records   |   "
            f"Total In: {total_in:,} units   |   Total Out: {total_out:,} units"
        )

    def record_transaction(self, tx_type):
        dlg = TransactionDialog(self, self.db, tx_type)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                self.db.add_transaction(
                    d["product_id"], d["tx_type"], d["quantity"], d["price"], d["note"]
                )
                self.refresh()
                QMessageBox.information(
                    self, "Success",
                    f"Stock {'In' if tx_type == 'IN' else 'Out'} recorded successfully."
                )
            except ValueError as e:
                QMessageBox.warning(self, "Cannot Complete", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
