from PyQt6.QtWidgets import QPushButton, QFrame, QLabel, QLineEdit, QComboBox
from PyQt6.QtCore import Qt

# ── Colour Palette ────────────────────────────────────────────────────────────
PRIMARY   = "#4F46E5"
SUCCESS   = "#059669"
DANGER    = "#DC2626"
WARNING   = "#D97706"
INFO      = "#0891B2"
PURPLE    = "#7C3AED"
ORANGE    = "#EA580C"
SECONDARY = "#E5E7EB"
TEXT_DARK = "#111827"
TEXT_MID  = "#374151"
TEXT_LIGHT= "#6B7280"
BG_PAGE   = "#F1F5F9"
BG_CARD   = "#FFFFFF"
BORDER    = "#E5E7EB"

# ── Shared Field Style ────────────────────────────────────────────────────────
FIELD_STYLE = f"""
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox, QDateEdit {{
        border: 1.5px solid {BORDER};
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 13px;
        color: {TEXT_DARK};
        background: #FAFAFA;
        min-height: 28px;
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
    QDoubleSpinBox:focus, QSpinBox:focus, QDateEdit:focus {{
        border-color: {PRIMARY};
        background: white;
    }}
    QComboBox::drop-down {{ border: none; padding-right: 6px; }}
    QComboBox QAbstractItemView {{
        border: 1px solid {BORDER};
        selection-background-color: #EEF2FF;
        selection-color: {PRIMARY};
    }}
    QDateEdit::drop-down {{ border: none; }}
"""

TABLE_STYLE = f"""
    QTableWidget {{
        border: none;
        background: transparent;
        gridline-color: #F3F4F6;
        font-size: 13px;
    }}
    QTableWidget::item {{
        padding: 8px 6px;
        color: {TEXT_MID};
    }}
    QHeaderView::section {{
        background: #F9FAFB;
        color: {TEXT_LIGHT};
        font-weight: 600;
        font-size: 12px;
        border: none;
        padding: 8px 6px;
        border-bottom: 1px solid {BORDER};
    }}
    QTableWidget::item:alternate {{ background: #FAFAFA; }}
    QTableWidget::item:selected {{ background: #EEF2FF; color: {PRIMARY}; }}
"""

SEARCH_STYLE = f"""
    QLineEdit {{
        border: 1.5px solid {BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 13px;
        background: white;
    }}
    QLineEdit:focus {{ border-color: {PRIMARY}; }}
"""

CARD_STYLE = f"""
    QFrame#card {{
        background: {BG_CARD};
        border-radius: 12px;
    }}
"""

# ── Helper Widgets ────────────────────────────────────────────────────────────

def btn(text, color=PRIMARY, text_color="white", icon=""):
    b = QPushButton(f"{icon}  {text}".strip() if icon else text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color}; color: {text_color};
            border: none; border-radius: 6px;
            padding: 7px 18px; font-size: 13px; font-weight: 600;
        }}
        QPushButton:hover {{ background: {_darken(color)}; }}
        QPushButton:pressed {{ background: {_darken(color, 20)}; }}
    """)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def _darken(hex_color, amount=15):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(
        max(0, r - amount), max(0, g - amount), max(0, b - amount)
    )


def page_title(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {TEXT_DARK};")
    return lbl


def section_label(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {TEXT_MID};")
    return lbl


def card_frame():
    f = QFrame()
    f.setObjectName("card")
    f.setStyleSheet(CARD_STYLE)
    return f


def search_box(placeholder="  Search…", width=220):
    le = QLineEdit()
    le.setPlaceholderText(placeholder)
    le.setFixedWidth(width)
    le.setStyleSheet(SEARCH_STYLE)
    return le


def status_badge(status: str) -> str:
    """Return HTML badge for a status string."""
    colours = {
        "paid":    ("#D1FAE5", "#065F46"),
        "partial": ("#FEF3C7", "#92400E"),
        "unpaid":  ("#FEE2E2", "#991B1B"),
        "credit":  ("#FEE2E2", "#991B1B"),
    }
    bg, fg = colours.get(status.lower(), ("#F3F4F6", "#374151"))
    return f'<span style="background:{bg};color:{fg};border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600;">{status.upper()}</span>'
