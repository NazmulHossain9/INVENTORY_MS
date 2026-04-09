from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QMessageBox, QFrame, QComboBox,
    QDoubleSpinBox, QSpinBox, QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from styles import (btn, page_title, card_frame, search_box,
                    PRIMARY, SUCCESS, DANGER, FIELD_STYLE, TABLE_STYLE, TEXT_LIGHT)


class ProductDialog(QDialog):
    def __init__(self, parent, db, data=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Add Product" if data is None else "Edit Product")
        self.setMinimumWidth(500)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.addWidget(QLabel(self.windowTitle(),
            styleSheet="font-size:16px;font-weight:700;color:#111827;"))

        form = QFormLayout(); form.setSpacing(10)
        self.name        = QLineEdit(); self.name.setPlaceholderText("Product name")
        self.sku         = QLineEdit(); self.sku.setPlaceholderText("Auto-generated if blank")
        self.category    = QComboBox()
        self.supplier    = QComboBox()
        self.unit        = QLineEdit(); self.unit.setPlaceholderText("pcs, kg, box…")
        self.cost_price  = QDoubleSpinBox(); self.cost_price.setRange(0,9999999); self.cost_price.setDecimals(2); self.cost_price.setPrefix("$ ")
        self.sale_price  = QDoubleSpinBox(); self.sale_price.setRange(0,9999999); self.sale_price.setDecimals(2); self.sale_price.setPrefix("$ ")
        self.quantity    = QSpinBox(); self.quantity.setRange(0,999999)
        self.min_stock   = QSpinBox(); self.min_stock.setRange(0,999999); self.min_stock.setValue(10)
        self.description = QTextEdit(); self.description.setPlaceholderText("Optional"); self.description.setMaximumHeight(60)
        for w in [self.name,self.sku,self.category,self.supplier,self.unit,
                  self.cost_price,self.sale_price,self.quantity,self.min_stock,self.description]:
            w.setStyleSheet(FIELD_STYLE)

        form.addRow("Name *",      self.name)
        form.addRow("SKU",         self.sku)
        form.addRow("Category",    self.category)
        form.addRow("Supplier",    self.supplier)
        form.addRow("Unit",        self.unit)
        pr = QHBoxLayout(); pr.addWidget(self.cost_price); pr.addWidget(QLabel("Sale:")); pr.addWidget(self.sale_price)
        form.addRow("Cost Price",  pr)
        qr = QHBoxLayout(); qr.addWidget(self.quantity); qr.addWidget(QLabel("Min:")); qr.addWidget(self.min_stock)
        form.addRow("Quantity",    qr)
        form.addRow("Description", self.description)
        layout.addLayout(form)

        self._cats = [{"id":None,"name":"— None —"}]+[dict(r) for r in db.get_all_categories()]
        self._sups = [{"id":None,"name":"— None —"}]+[dict(r) for r in db.get_all_suppliers()]
        for c in self._cats: self.category.addItem(c["name"], c["id"])
        for s in self._sups: self.supplier.addItem(s["name"], s["id"])

        if data:
            self.name.setText(data.get("name",""))
            self.sku.setText(data.get("sku","") or "")
            self.unit.setText(data.get("unit","pcs"))
            self.cost_price.setValue(data.get("cost_price",0) or 0)
            self.sale_price.setValue(data.get("sale_price",0) or 0)
            self.quantity.setValue(data.get("quantity",0) or 0)
            self.min_stock.setValue(data.get("min_stock",10) or 10)
            self.description.setText(data.get("description","") or "")
            for i,c in enumerate(self._cats):
                if c["id"] == data.get("category_id"): self.category.setCurrentIndex(i)
            for i,s in enumerate(self._sups):
                if s["id"] == data.get("supplier_id"): self.supplier.setCurrentIndex(i)

        btns = QHBoxLayout(); btns.setSpacing(8)
        c = btn("Cancel", "#E5E7EB", "#374151"); c.clicked.connect(self.reject)
        s = btn("Save"); s.clicked.connect(self._validate)
        btns.addWidget(c); btns.addWidget(s)
        layout.addLayout(btns)

    def _validate(self):
        if not self.name.text().strip():
            QMessageBox.warning(self,"Validation","Product name is required."); return
        self.accept()

    def get_data(self):
        return dict(
            name=self.name.text().strip(), sku=self.sku.text().strip() or None,
            category_id=self.category.currentData(), supplier_id=self.supplier.currentData(),
            unit=self.unit.text().strip() or "pcs",
            cost_price=self.cost_price.value(), sale_price=self.sale_price.value(),
            quantity=self.quantity.value(), min_stock=self.min_stock.value(),
            description=self.description.toPlainText().strip(),
        )


class ProductsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db; self._rows = []
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24,24,24,24); root.setSpacing(16)

        hr = QHBoxLayout()
        hr.addWidget(page_title("Products")); hr.addStretch()
        self.search = search_box("  Search name, SKU…")
        self.search.textChanged.connect(self.refresh)
        hr.addWidget(self.search)
        self.cat_filter = QComboBox(); self.cat_filter.setFixedWidth(160)
        self.cat_filter.setStyleSheet(FIELD_STYLE)
        self.cat_filter.currentIndexChanged.connect(self.refresh)
        hr.addWidget(self.cat_filter)
        a = btn("+ Add Product"); a.clicked.connect(self.add_product)
        hr.addWidget(a); root.addLayout(hr)

        f = card_frame(); fl = QVBoxLayout(f); fl.setContentsMargins(0,0,0,0)
        HEADERS = ["#","Name","SKU","Category","Supplier","Unit","Stock","Min","Cost","Sale Price","Updated"]
        self.table = QTableWidget()
        self.table.setColumnCount(len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(0,50)
        self.table.setStyleSheet(TABLE_STYLE)
        fl.addWidget(self.table); root.addWidget(f)

        ar = QHBoxLayout(); ar.setSpacing(8); ar.addStretch()
        inc = btn("＋  Add Stock",    SUCCESS); inc.clicked.connect(self.increment_stock)
        dec = btn("－  Remove Stock", DANGER);  dec.clicked.connect(self.decrement_stock)
        e   = btn("Edit",             "#6366F1"); e.clicked.connect(self.edit_product)
        d   = btn("Delete",           "#94A3B8", "#374151"); d.clicked.connect(self.delete_product)
        for w in [inc, dec, e, d]: ar.addWidget(w)
        root.addLayout(ar)

        self._reload_cats()

    def _reload_cats(self):
        self.cat_filter.blockSignals(True)
        self.cat_filter.clear()
        self.cat_filter.addItem("All Categories", None)
        for c in self.db.get_all_categories():
            self.cat_filter.addItem(c["name"], c["id"])
        self.cat_filter.blockSignals(False)

    def refresh(self):
        rows = self.db.get_all_products(self.search.text().strip(),
                                         self.cat_filter.currentData())
        self._rows = rows
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            low = r["quantity"] <= r["min_stock"]
            vals = [str(r["id"]), r["name"], r["sku"] or "—",
                    r["category"] or "—", r["supplier"] or "—",
                    r["unit"], str(r["quantity"]), str(r["min_stock"]),
                    f"${r['cost_price']:.2f}", f"${r['sale_price']:.2f}",
                    (r["updated_at"] or "")[:10]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 6 and low:
                    item.setForeground(QColor(DANGER))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.table.setItem(i, c, item)

    def _selected(self):
        r = self.table.currentRow()
        if r < 0: QMessageBox.information(self,"Select","Select a product first."); return None
        return self._rows[r]

    def increment_stock(self):
        self._adjust_stock("IN")

    def decrement_stock(self):
        self._adjust_stock("OUT")

    def _adjust_stock(self, direction):
        row = self._selected()
        if not row:
            return
        from PyQt6.QtWidgets import QInputDialog
        current = row["quantity"]
        label = (f"Add stock to  '{row['name']}'\n"
                 f"Current stock: {current} {row['unit']}\n\n"
                 f"Quantity to add:") if direction == "IN" else (
                f"Remove stock from  '{row['name']}'\n"
                f"Current stock: {current} {row['unit']}\n\n"
                f"Quantity to remove:")
        max_val = 999999 if direction == "IN" else current
        if direction == "OUT" and current == 0:
            QMessageBox.warning(self, "No Stock", f"'{row['name']}' has 0 units in stock.")
            return
        qty, ok = QInputDialog.getInt(self, "Adjust Stock", label, 1, 1, max_val)
        if not ok:
            return
        try:
            self.db.add_transaction(row["id"], direction, qty, 0,
                                    f"Manual {'addition' if direction == 'IN' else 'removal'}")
            new_qty = current + qty if direction == "IN" else current - qty
            QMessageBox.information(
                self, "Stock Updated",
                f"'{row['name']}'\n"
                f"{'Added' if direction == 'IN' else 'Removed'}:  {qty} {row['unit']}\n"
                f"New stock:  {new_qty} {row['unit']}"
            )
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def add_product(self):
        dlg = ProductDialog(self, self.db)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try: self.db.add_product(**d); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Error",str(e))

    def edit_product(self):
        row = self._selected()
        if not row: return
        full = dict(self.db.get_product_by_id(row["id"]))
        dlg = ProductDialog(self, self.db, full)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try: self.db.update_product(row["id"], **d); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Error",str(e))

    def delete_product(self):
        row = self._selected()
        if not row: return
        if QMessageBox.question(self,"Delete",f"Delete '{row['name']}'? All stock & transactions removed.",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.db.delete_product(row["id"]); self.refresh()
