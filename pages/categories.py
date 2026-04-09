from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QDialog, QFormLayout, QTextEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt


def _btn(text, color="#4F46E5", text_color="white"):
    b = QPushButton(text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color}; color: {text_color};
            border: none; border-radius: 6px;
            padding: 7px 16px; font-size: 13px; font-weight: 600;
        }}
        QPushButton:hover {{ opacity: 0.85; }}
        QPushButton:pressed {{ opacity: 0.7; }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class CategoryDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Add Category" if data is None else "Edit Category")
        self.setMinimumWidth(360)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(self.windowTitle())
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Category name")
        self.name_input.setStyleSheet(self._field_style())
        form.addRow("Name *", self.name_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Description (optional)")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet(self._field_style())
        form.addRow("Description", self.desc_input)

        layout.addLayout(form)

        if data:
            self.name_input.setText(data["name"])
            self.desc_input.setText(data["description"] or "")

        btns = QHBoxLayout()
        btns.setSpacing(8)
        cancel = _btn("Cancel", "#E5E7EB", "#374151")
        cancel.clicked.connect(self.reject)
        save = _btn("Save")
        save.clicked.connect(self._validate)
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _field_style(self):
        return """
            QLineEdit, QTextEdit {
                border: 1.5px solid #E5E7EB; border-radius: 6px;
                padding: 6px 10px; font-size: 13px; color: #111827;
                background: #FAFAFA;
            }
            QLineEdit:focus, QTextEdit:focus { border-color: #4F46E5; background: white; }
        """

    def _validate(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation", "Category name is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
        }


class CategoriesPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Header row
        header_row = QHBoxLayout()
        title = QLabel("Categories")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #111827;")
        header_row.addWidget(title)
        header_row.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("  Search categories…")
        self.search.setFixedWidth(220)
        self.search.setStyleSheet("""
            QLineEdit { border: 1.5px solid #E5E7EB; border-radius: 6px;
                        padding: 6px 10px; font-size: 13px; background: white; }
            QLineEdit:focus { border-color: #4F46E5; }
        """)
        self.search.textChanged.connect(self.refresh)
        header_row.addWidget(self.search)

        add_btn = _btn("+ Add Category")
        add_btn.clicked.connect(self.add_category)
        header_row.addWidget(add_btn)
        root.addLayout(header_row)

        # Table
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: white; border-radius: 12px; }")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Name", "Description", "Created At"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
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
        frame_layout.addWidget(self.table)
        root.addWidget(frame)

        # Action buttons
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        action_row.addStretch()
        edit_btn = _btn("Edit", "#059669")
        edit_btn.clicked.connect(self.edit_category)
        del_btn = _btn("Delete", "#DC2626")
        del_btn.clicked.connect(self.delete_category)
        action_row.addWidget(edit_btn)
        action_row.addWidget(del_btn)
        root.addLayout(action_row)

    def refresh(self):
        search = self.search.text().strip()
        rows = self.db.get_all_categories()
        if search:
            rows = [r for r in rows if search.lower() in r["name"].lower()
                    or search.lower() in (r["description"] or "").lower()]
        self.table.setRowCount(len(rows))
        self._rows = rows
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(row["description"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(row["created_at"][:16]))

    def _selected_row(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a row first.")
            return None
        return self._rows[row]

    def add_category(self):
        dlg = CategoryDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                self.db.add_category(d["name"], d["description"])
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def edit_category(self):
        row = self._selected_row()
        if not row:
            return
        dlg = CategoryDialog(self, row)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            try:
                self.db.update_category(row["id"], d["name"], d["description"])
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_category(self):
        row = self._selected_row()
        if not row:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete category '{row['name']}'?\nProducts in this category will become uncategorized.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_category(row["id"])
            self.refresh()
