import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database import Database
from pages.dashboard    import DashboardPage
from pages.products     import ProductsPage
from pages.customers    import CustomersPage
from pages.suppliers    import SuppliersPage
from pages.sales        import SalesPage
from pages.purchases    import PurchasesPage
from pages.cash         import CashPage
from pages.stock        import StockPage
from pages.credit       import CreditPage
from pages.accounting      import AccountingPage
from pages.reports         import ReportsPage
from pages.categories      import CategoriesPage
from pages.sales_return    import SalesReturnPage
from pages.purchase_return import PurchaseReturnPage


APP_STYLE = """
    QMainWindow { background: #F1F5F9; }
    QWidget { font-family: 'Segoe UI', system-ui, sans-serif; }
    QScrollBar:vertical {
        background: #F1F5F9; width: 8px; border-radius: 4px; border: none;
    }
    QScrollBar::handle:vertical {
        background: #CBD5E1; border-radius: 4px; min-height: 30px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QToolTip {
        background: #1E293B; color: white; border: none;
        padding: 4px 8px; border-radius: 4px; font-size: 12px;
    }
"""

# (icon, label, section_separator_before)
NAV_ITEMS = [
    ("📊", "Dashboard",        None),
    (None, None,               "INVENTORY"),
    ("📦", "Products",         None),
    ("📈", "Stock",            None),
    (None, None,               "TRADING"),
    ("🛒", "Sales",            None),
    ("↩", "Sales Return",     None),
    ("📋", "Purchases",        None),
    ("↪", "Purchase Return",  None),
    ("💳", "Credit",           None),
    (None, None,               "PARTIES"),
    ("👥", "Customers",        None),
    ("🚚", "Suppliers",        None),
    (None, None,               "FINANCE"),
    ("💰", "Cash",             None),
    ("📒", "Accounting",       None),
    (None, None,               "ANALYTICS"),
    ("📄", "Reports",          None),
    (None, None,               "SETTINGS"),
    ("🏷", "Categories",       None),
]


class NavButton(QPushButton):
    BASE = """
        QPushButton {{
            background: transparent; color: #94A3B8; border: none;
            border-radius: 8px; text-align: left;
            padding: 9px 14px; font-size: 13px; font-weight: 500;
        }}
        QPushButton:hover {{ background: #334155; color: #F1F5F9; }}
    """
    ACTIVE = """
        QPushButton {{
            background: #4F46E5; color: white; border: none;
            border-radius: 8px; text-align: left;
            padding: 9px 14px; font-size: 13px; font-weight: 600;
        }}
    """

    def __init__(self, icon, label):
        super().__init__(f"  {icon}  {label}")
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_active(False)

    def set_active(self, active):
        self.setStyleSheet((self.ACTIVE if active else self.BASE).format())


class Sidebar(QFrame):
    def __init__(self, on_nav):
        super().__init__()
        self.setObjectName("sidebar")
        self.setStyleSheet("QFrame#sidebar { background: #1E293B; }")
        self.setFixedWidth(200)
        self._buttons = {}   # label → NavButton
        self._on_nav = on_nav

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Logo
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background: #0F172A;")
        logo_frame.setFixedHeight(60)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 0, 16, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        logo = QLabel("⬛  IMS")
        logo.setStyleSheet("color: white; font-size: 17px; font-weight: 800;")
        sub  = QLabel("Inventory Manager")
        sub.setStyleSheet("color: #64748B; font-size: 10px;")
        logo_layout.addWidget(logo)
        logo_layout.addWidget(sub)
        outer.addWidget(logo_frame)

        # Scrollable nav
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_widget = QWidget(); nav_widget.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(2)

        for icon, label, section in NAV_ITEMS:
            if section is not None:
                sep = QLabel(section)
                sep.setStyleSheet(
                    "color: #475569; font-size: 9px; font-weight: 700; "
                    "letter-spacing: 1px; padding: 10px 6px 4px 6px; background: transparent;"
                )
                nav_layout.addWidget(sep)
            elif icon and label:
                nav_btn = NavButton(icon, label)
                nav_btn.clicked.connect(lambda _, l=label: self._on_nav(l))
                nav_layout.addWidget(nav_btn)
                self._buttons[label] = nav_btn

        nav_layout.addStretch()
        scroll.setWidget(nav_widget)
        outer.addWidget(scroll)

        # Footer
        footer = QLabel("  v2.0  ·  SQLite3")
        footer.setStyleSheet(
            "color: #334155; font-size: 9px; padding: 8px 16px; background: #0F172A;"
        )
        outer.addWidget(footer)

    def set_active(self, label):
        for lbl, btn in self._buttons.items():
            btn.set_active(lbl == label)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory Management System")
        self.resize(1280, 780)
        self.setMinimumSize(960, 620)
        self.setStyleSheet(APP_STYLE)

        self.db = Database()

        root = QWidget(); self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar(self._navigate)
        root_layout.addWidget(self.sidebar)

        # Content area with scroll
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setStyleSheet("QScrollArea { border: none; background: #F1F5F9; }")

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: #F1F5F9; }")
        content_scroll.setWidget(self.stack)
        root_layout.addWidget(content_scroll)

        # Instantiate all pages
        self._pages = {
            "Dashboard":       DashboardPage(self.db),
            "Products":        ProductsPage(self.db),
            "Stock":           StockPage(self.db),
            "Sales":           SalesPage(self.db),
            "Sales Return":    SalesReturnPage(self.db),
            "Purchases":       PurchasesPage(self.db),
            "Purchase Return": PurchaseReturnPage(self.db),
            "Credit":          CreditPage(self.db),
            "Customers":       CustomersPage(self.db),
            "Suppliers":       SuppliersPage(self.db),
            "Cash":            CashPage(self.db),
            "Accounting":      AccountingPage(self.db),
            "Reports":         ReportsPage(self.db),
            "Categories":      CategoriesPage(self.db),
        }
        for page in self._pages.values():
            self.stack.addWidget(page)

        self._navigate("Dashboard")

    def _navigate(self, label):
        page = self._pages.get(label)
        if not page:
            return
        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(label)
        # After switching, reload category filter in products if categories changed
        if label == "Products" and hasattr(page, "_reload_cats"):
            page._reload_cats()
        if hasattr(page, "refresh"):
            page.refresh()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("IMS")
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
