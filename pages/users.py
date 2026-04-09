from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QVBoxLayout as QVL, QLineEdit, QMessageBox, QFrame, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from styles import (PRIMARY, DANGER, SUCCESS, WARNING, TEXT_DARK, TEXT_MID, TEXT_LIGHT,
                    TABLE_STYLE, BG_CARD, BORDER, FIELD_STYLE)

_DIALOG_STYLE = """
    QDialog   { background: #1E293B; }
    QLabel    { color: #94A3B8; font-size: 11px; font-weight: 600;
                letter-spacing: 1px; background: transparent; }
    QLabel#title { color: white; font-size: 16px; font-weight: 700; }
    QLabel#err   { color: #F87171; font-size: 12px; }
    QLineEdit, QComboBox {
        background: #0F172A; color: white; border: 1px solid #334155;
        border-radius: 8px; padding: 0px 12px; font-size: 13px;
    }
    QLineEdit:focus, QComboBox:focus { border: 1px solid #4F46E5; }
    QComboBox QAbstractItemView {
        background: #0F172A; color: white; selection-background-color: #4F46E5;
    }
    QPushButton#ok {
        background: #4F46E5; color: white; border: none;
        border-radius: 8px; padding: 10px; font-size: 13px; font-weight: 700;
    }
    QPushButton#ok:hover { background: #4338CA; }
    QPushButton#cancel {
        background: transparent; color: #64748B; border: 1px solid #334155;
        border-radius: 8px; padding: 10px; font-size: 13px;
    }
    QPushButton#cancel:hover { color: #94A3B8; border-color: #475569; }
"""


def _btn(text, color=PRIMARY):
    b = QPushButton(text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color}; color: white; border: none;
            border-radius: 6px; padding: 7px 18px;
            font-size: 13px; font-weight: 600;
        }}
        QPushButton:hover {{ opacity: 0.85; }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def _icon_btn(text, color):
    b = QPushButton(text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color}; color: white; border: none;
            border-radius: 5px; padding: 4px 10px;
            font-size: 11px; font-weight: 600;
        }}
        QPushButton:hover {{ opacity: 0.85; }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFixedHeight(26)
    return b


class AddUserDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Add New User")
        self.setFixedSize(360, 420)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setStyleSheet(_DIALOG_STYLE)
        self._build()

    def _build(self):
        lay = QVL(self)
        lay.setContentsMargins(32, 28, 32, 24)
        lay.setSpacing(0)

        title = QLabel("Add New User"); title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        lay.addSpacing(20)

        for attr, label, ph, echo in [
            ("_inp_user", "USERNAME",         "Enter username",        False),
            ("_inp_pass", "PASSWORD",         "At least 4 characters", True),
            ("_inp_conf", "CONFIRM PASSWORD", "Repeat password",       True),
        ]:
            lbl = QLabel(label)
            inp = QLineEdit(); inp.setPlaceholderText(ph); inp.setFixedHeight(40)
            if echo:
                inp.setEchoMode(QLineEdit.EchoMode.Password)
            lay.addWidget(lbl)
            lay.addSpacing(4)
            lay.addWidget(inp)
            lay.addSpacing(12)
            setattr(self, attr, inp)

        role_lbl = QLabel("ROLE")
        self._role = QComboBox(); self._role.setFixedHeight(40)
        for r in self.db.get_all_roles():
            self._role.addItem(r["name"], userData=r["id"])
        if self._role.count() == 0:
            self._role.addItems(["staff", "admin"])
        lay.addWidget(role_lbl)
        lay.addSpacing(4)
        lay.addWidget(self._role)
        lay.addSpacing(10)

        self._err = QLabel(""); self._err.setObjectName("err")
        self._err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err.setWordWrap(True)
        lay.addWidget(self._err)
        lay.addSpacing(12)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        cancel = QPushButton("Cancel"); cancel.setObjectName("cancel")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Create User"); ok.setObjectName("ok")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(self._submit)
        btn_row.addWidget(cancel); btn_row.addWidget(ok)
        lay.addLayout(btn_row)

        self._inp_conf.returnPressed.connect(self._submit)
        self._inp_pass.returnPressed.connect(self._inp_conf.setFocus)
        self._inp_user.returnPressed.connect(self._inp_pass.setFocus)

    def _submit(self):
        username = self._inp_user.text().strip()
        password = self._inp_pass.text()
        confirm  = self._inp_conf.text()
        role     = self._role.currentText()

        if not username or not password:
            self._err.setText("Username and password are required.")
            return
        if password != confirm:
            self._err.setText("Passwords do not match.")
            self._inp_conf.clear(); self._inp_conf.setFocus()
            return
        try:
            self.db.register_user(username, password, role)
            self.accept()
        except ValueError as e:
            self._err.setText(str(e))


class ChangePasswordDialog(QDialog):
    def __init__(self, db, user_id, username, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.setWindowTitle(f"Change Password — {username}")
        self.setFixedSize(360, 300)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setStyleSheet(_DIALOG_STYLE)
        self._build(username)

    def _build(self, username):
        lay = QVL(self)
        lay.setContentsMargins(32, 28, 32, 24)
        lay.setSpacing(0)

        title = QLabel(f"Change Password"); title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel(f"User: {username}")
        sub.setStyleSheet("color:#64748B;font-size:12px;background:transparent;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addSpacing(20)

        for attr, label, ph in [
            ("_inp_new",  "NEW PASSWORD",     "At least 4 characters"),
            ("_inp_conf", "CONFIRM PASSWORD", "Repeat new password"),
        ]:
            lbl = QLabel(label)
            inp = QLineEdit(); inp.setPlaceholderText(ph)
            inp.setFixedHeight(40)
            inp.setEchoMode(QLineEdit.EchoMode.Password)
            lay.addWidget(lbl)
            lay.addSpacing(4)
            lay.addWidget(inp)
            lay.addSpacing(12)
            setattr(self, attr, inp)

        self._err = QLabel(""); self._err.setObjectName("err")
        self._err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err.setWordWrap(True)
        lay.addWidget(self._err)
        lay.addSpacing(12)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        cancel = QPushButton("Cancel"); cancel.setObjectName("cancel")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Save Password"); ok.setObjectName("ok")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(self._submit)
        btn_row.addWidget(cancel); btn_row.addWidget(ok)
        lay.addLayout(btn_row)

        self._inp_conf.returnPressed.connect(self._submit)
        self._inp_new.returnPressed.connect(self._inp_conf.setFocus)

    def _submit(self):
        new_pw  = self._inp_new.text()
        confirm = self._inp_conf.text()
        if not new_pw:
            self._err.setText("Password cannot be empty.")
            return
        if new_pw != confirm:
            self._err.setText("Passwords do not match.")
            self._inp_conf.clear(); self._inp_conf.setFocus()
            return
        try:
            self.db.set_user_password(self.user_id, new_pw)
            self.accept()
        except ValueError as e:
            self._err.setText(str(e))


class UsersPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Users")
        title.setStyleSheet(f"font-size:22px;font-weight:700;color:{TEXT_DARK};")
        hdr.addWidget(title)
        hdr.addStretch()
        add_btn = _btn("+ Add User")
        add_btn.clicked.connect(self._add_user)
        hdr.addWidget(add_btn)
        root.addLayout(hdr)

        card = QFrame()
        card.setStyleSheet(f"QFrame{{background:{BG_CARD};border-radius:12px;}}")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(16, 14, 16, 14)
        card_lay.setSpacing(8)

        lbl = QLabel("Registered Users")
        lbl.setStyleSheet(f"font-size:14px;font-weight:600;color:{TEXT_MID};")
        card_lay.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["#", "Username", "Role", "Status", "Actions", "Created At"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 210)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setRowHeight(0, 40)
        card_lay.addWidget(self.table)
        root.addWidget(card)

    def refresh(self):
        users = self.db.get_all_users()
        self.table.setRowCount(len(users))
        ROLE_COLOR = {"admin": "#4F46E5", "staff": "#059669"}

        for r, u in enumerate(users):
            self.table.setRowHeight(r, 40)
            uid       = u["id"]
            uname     = u["username"]
            role_name = u["role_name"] or u["role"]
            created   = u["created_at"]
            is_active = bool(u["is_active"])

            # # col
            n_item = QTableWidgetItem(str(uid))
            n_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 0, n_item)

            # username
            self.table.setItem(r, 1, QTableWidgetItem(uname))

            # role
            role_item = QTableWidgetItem(role_name)
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            role_item.setForeground(QColor(ROLE_COLOR.get(role_name, "#374151")))
            role_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.table.setItem(r, 2, role_item)

            # status badge
            status_item = QTableWidgetItem("Active" if is_active else "Inactive")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor(SUCCESS if is_active else DANGER))
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.table.setItem(r, 3, status_item)

            # action buttons widget
            cell = QWidget()
            cell_lay = QHBoxLayout(cell)
            cell_lay.setContentsMargins(4, 4, 4, 4)
            cell_lay.setSpacing(6)

            pw_btn = _icon_btn("🔑 Password", "#4F46E5")
            pw_btn.setToolTip(f"Change password for {uname}")
            pw_btn.clicked.connect(lambda _, i=uid, n=uname: self._change_password(i, n))

            toggle_color = DANGER if is_active else SUCCESS
            toggle_text  = "⛔ Deactivate" if is_active else "✅ Activate"
            tog_btn = _icon_btn(toggle_text, toggle_color)
            tog_btn.setToolTip("Deactivate user" if is_active else "Activate user")
            tog_btn.clicked.connect(lambda _, i=uid, a=is_active: self._toggle_active(i, a))

            cell_lay.addWidget(pw_btn)
            cell_lay.addWidget(tog_btn)
            cell_lay.addStretch()
            self.table.setCellWidget(r, 4, cell)

            # created at
            created_item = QTableWidgetItem(created)
            created_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 5, created_item)

    def _add_user(self):
        dlg = AddUserDialog(self.db, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()
            QMessageBox.information(self, "Success", "User created successfully.")

    def _change_password(self, user_id, username):
        dlg = ChangePasswordDialog(self.db, user_id, username, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Success",
                                    f"Password for '{username}' updated successfully.")

    def _toggle_active(self, user_id, currently_active):
        action = "deactivate" if currently_active else "activate"
        reply = QMessageBox.question(
            self, "Confirm",
            f"Are you sure you want to {action} this user?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.set_user_active(user_id, not currently_active)
            self.refresh()
