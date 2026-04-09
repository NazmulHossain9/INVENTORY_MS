"""
InvoicePrinter — wraps QPrinter / QPrintPreviewDialog for A4 and POS formats.

A4  : standard Letter/A4 page, full-colour invoice layout
POS : 80 mm thermal-paper width, monospace receipt layout
"""

import os
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog
from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
from PyQt6.QtCore import QSizeF, Qt, QMarginsF
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QTabWidget, QSplitter, QTextBrowser, QFileDialog,
    QMessageBox, QFrame, QApplication
)


# ── Constants ─────────────────────────────────────────────────────────────────

# 80 mm thermal paper — width in mm; height set long enough for any receipt
_POS_PAGE_W_MM = 80.0
_POS_PAGE_H_MM = 297.0   # will be trimmed by content

_MARGIN_A4_MM  = 12.0    # page margins for A4
_MARGIN_POS_MM = 2.0     # narrower margins for POS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_a4_printer(output_path: str = "") -> QPrinter:
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageMargins(
        QMarginsF(_MARGIN_A4_MM, _MARGIN_A4_MM, _MARGIN_A4_MM, _MARGIN_A4_MM),
        QPageLayout.Unit.Millimeter
    )
    if output_path:
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
    return printer


def _make_pos_printer(output_path: str = "") -> QPrinter:
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    page_size = QPageSize(QSizeF(_POS_PAGE_W_MM, _POS_PAGE_H_MM),
                          QPageSize.Unit.Millimeter, "POS80")
    printer.setPageSize(page_size)
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageMargins(
        QMarginsF(_MARGIN_POS_MM, _MARGIN_POS_MM, _MARGIN_POS_MM, _MARGIN_POS_MM),
        QPageLayout.Unit.Millimeter
    )
    if output_path:
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
    return printer


def _render(html: str, printer: QPrinter):
    doc = QTextDocument()
    doc.setHtml(html)
    doc.setPageSize(
        QSizeF(printer.pageRect(QPrinter.Unit.Point).size())
    )
    doc.print(printer)


# ── Preview Dialog ─────────────────────────────────────────────────────────────

def preview_and_print(parent: QWidget, html: str, is_pos: bool = False,
                       title: str = "Print Preview"):
    """Show QPrintPreviewDialog; user can print or export PDF from there."""
    printer = _make_pos_printer() if is_pos else _make_a4_printer()

    dlg = QPrintPreviewDialog(printer, parent)
    dlg.setWindowTitle(title)
    dlg.paintRequested.connect(lambda p: _render(html, p))
    dlg.exec()


def save_pdf(parent: QWidget, html: str, is_pos: bool = False,
             default_name: str = "invoice") -> bool:
    """Save directly as PDF without showing a printer dialog."""
    path, _ = QFileDialog.getSaveFileName(
        parent, "Save PDF", f"{default_name}.pdf", "PDF Files (*.pdf)"
    )
    if not path:
        return False
    try:
        printer = _make_pos_printer(path) if is_pos else _make_a4_printer(path)
        _render(html, printer)
        QMessageBox.information(parent, "Saved", f"PDF saved to:\n{path}")
        return True
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Failed to save PDF:\n{e}")
        return False


def print_to_printer(parent: QWidget, html: str, is_pos: bool = False):
    """Show native print dialog and print to selected printer."""
    printer = _make_pos_printer() if is_pos else _make_a4_printer()
    dlg = QPrintDialog(printer, parent)
    dlg.setWindowTitle("Select Printer")
    if dlg.exec() == QDialog.DialogCode.Accepted:
        _render(html, printer)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PrintInvoiceDialog — unified UI for A4 + POS printing                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class PrintInvoiceDialog(QDialog):
    """
    Shows a tabbed dialog with:
      Tab 1 — A4 Invoice   (preview pane + Print / Save PDF)
      Tab 2 — POS Receipt  (preview pane + Print / Save PDF)
    """

    BTN_STYLE = """
        QPushButton {{
            background: {bg}; color: white; border: none;
            border-radius: 6px; padding: 8px 20px;
            font-size: 13px; font-weight: 600;
        }}
        QPushButton:hover {{ background: {hover}; }}
    """

    def __init__(self, parent: QWidget,
                 a4_html: str, pos_html: str,
                 doc_number: str = "invoice",
                 title: str = "Print Invoice"):
        super().__init__(parent)
        self._a4_html  = a4_html
        self._pos_html = pos_html
        self._doc_no   = doc_number
        self.setWindowTitle(title)
        self.setMinimumSize(900, 680)
        self.setModal(True)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        # Title bar
        title_row = QHBoxLayout()
        title_lbl = QLabel(f"🖨  {self.windowTitle()}")
        title_lbl.setStyleSheet("font-size:16px;font-weight:700;color:#111827;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        doc_lbl = QLabel(self._doc_no)
        doc_lbl.setStyleSheet("font-size:13px;font-weight:600;color:#4F46E5;"
                               "background:#EEF2FF;border-radius:4px;padding:4px 10px;")
        title_row.addWidget(doc_lbl)
        root.addLayout(title_row)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E5E7EB; border-radius: 6px; }
            QTabBar::tab {
                background: #F1F5F9; color: #374151; border-radius: 6px 6px 0 0;
                padding: 8px 24px; font-size: 13px; margin-right: 3px;
            }
            QTabBar::tab:selected { background: #4F46E5; color: white; font-weight: 600; }
        """)

        tabs.addTab(self._make_tab(is_pos=False), "  📄  A4 Invoice  ")
        tabs.addTab(self._make_tab(is_pos=True),  "  🧾  POS Receipt (80 mm)  ")
        root.addWidget(tabs)

        # Close button
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(self.BTN_STYLE.format(bg="#6B7280", hover="#4B5563"))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        close_row.addWidget(close_btn)
        root.addLayout(close_row)

    def _make_tab(self, is_pos: bool) -> QWidget:
        html    = self._pos_html if is_pos else self._a4_html
        tab     = QWidget()
        layout  = QVBoxLayout(tab)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(10)

        # Button row
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)

        def _b(text, bg, hover, slot):
            b = QPushButton(text)
            b.setStyleSheet(self.BTN_STYLE.format(bg=bg, hover=hover))
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(slot)
            return b

        suffix = "POS" if is_pos else "A4"
        default_name = f"{self._doc_no}_{suffix}"

        btn_row.addWidget(_b("🔍  Preview & Print", "#4F46E5", "#4338CA",
                             lambda _, p=is_pos, h=html: preview_and_print(
                                 self, h, p, f"Preview — {self._doc_no}")))
        btn_row.addWidget(_b("🖨  Print to Printer", "#059669", "#047857",
                             lambda _, p=is_pos, h=html: print_to_printer(self, h, p)))
        btn_row.addWidget(_b("💾  Save as PDF", "#0891B2", "#0E7490",
                             lambda _, p=is_pos, h=html, n=default_name: save_pdf(
                                 self, h, p, n)))
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Info label
        if is_pos:
            info = QLabel("80 mm thermal paper · monospace receipt format")
        else:
            info = QLabel("A4 page · full-colour professional invoice layout")
        info.setStyleSheet("color:#6B7280;font-size:11px;")
        layout.addWidget(info)

        # Live preview
        preview = QTextBrowser()
        preview.setHtml(html)
        preview.setStyleSheet("""
            QTextBrowser {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
            }
        """)
        if is_pos:
            preview.setMaximumWidth(420)
            preview.setMinimumWidth(320)
            wrap = QHBoxLayout()
            wrap.addStretch()
            wrap.addWidget(preview)
            wrap.addStretch()
            container = QWidget()
            container.setLayout(wrap)
            layout.addWidget(container)
        else:
            layout.addWidget(preview)

        return tab
