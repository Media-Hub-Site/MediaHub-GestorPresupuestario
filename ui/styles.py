"""
Modern dark theme stylesheet and styling tokens for Gestor Presupuestario.
"""

DARK_THEME_QSS = """
/* ═══════════════════════════════════════════════════════════════════════════
   Gestor Presupuestario - Dark Theme (PyQt6)
   ═══════════════════════════════════════════════════════════════════════════ */

QWidget {
    background-color: #0d0e15;
    color: #f1f1f5;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

/* ── Windows & Panels ─────────────────────────────────────────────────── */
QMainWindow, QDialog {
    background-color: #0a0a0f;
}

QFrame#sidebar {
    background-color: #12121a;
    border-right: 1px solid rgba(255, 255, 255, 0.07);
}

QFrame#topbar {
    background-color: #12121a;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

QFrame#card, QFrame.card {
    background-color: #161622;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}

/* ── Typography & Labels ──────────────────────────────────────────────── */
QLabel {
    color: #f1f1f5;
}

QLabel#title {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#subtitle {
    font-size: 13px;
    color: #8b8b9e;
}

QLabel#metric_val {
    font-size: 24px;
    font-weight: bold;
    color: #818cf8;
}

QLabel#metric_lbl {
    font-size: 12px;
    text-transform: uppercase;
    color: #8b8b9e;
    font-weight: 600;
}

/* ── Buttons ──────────────────────────────────────────────────────────── */
QPushButton {
    background-color: #20202e;
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2b2b3d;
    border-color: rgba(99, 102, 241, 0.5);
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #1c1c28;
}

QPushButton:disabled {
    background-color: #161620;
    color: #555566;
    border-color: rgba(255, 255, 255, 0.03);
}

QPushButton#btn_primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #06b6d4);
    color: #ffffff;
    border: none;
    font-weight: bold;
}

QPushButton#btn_primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7578ff, stop:1 #22d3ee);
}

QPushButton#btn_success {
    background-color: rgba(34, 197, 94, 0.2);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.4);
}

QPushButton#btn_success:hover {
    background-color: rgba(34, 197, 94, 0.35);
}

QPushButton#btn_danger {
    background-color: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.35);
}

QPushButton#btn_danger:hover {
    background-color: rgba(239, 68, 68, 0.3);
}

/* Sidebar navigation buttons */
QPushButton#nav_btn {
    text-align: left;
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#nav_btn:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #ffffff;
}

QPushButton#nav_btn:checked, QPushButton#nav_btn[active="true"] {
    background-color: rgba(99, 102, 241, 0.15);
    color: #818cf8;
    font-weight: 600;
    border-left: 3px solid #6366f1;
}

/* ── Form Controls (Inputs, Selects, Spinners) ────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {
    background-color: #161622;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 7px 12px;
    color: #f1f1f5;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {
    border: 1px solid #6366f1;
    background-color: #1a1a28;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #161622;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    selection-background-color: #6366f1;
    color: #f1f1f5;
    padding: 4px;
}

/* ── Tables & Views ───────────────────────────────────────────────────── */
QTableWidget, QTableView {
    background-color: #12121a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    gridline-color: rgba(255, 255, 255, 0.05);
    color: #e2e8f0;
}

QHeaderView::section {
    background-color: #181824;
    color: #94a3b8;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

QTableWidget::item:selected {
    background-color: rgba(99, 102, 241, 0.25);
    color: #ffffff;
}

/* ── Progress Bars ────────────────────────────────────────────────────── */
QProgressBar {
    background-color: #20202e;
    border: none;
    border-radius: 6px;
    text-align: right;
    font-size: 11px;
    color: #ffffff;
    height: 12px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #06b6d4);
    border-radius: 6px;
}

/* ── Scrollbars ───────────────────────────────────────────────────────── */
QScrollBar:vertical {
    border: none;
    background: #0d0e15;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2b2b3d;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #6366f1;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QTabWidget::pane {
    border: none;
}
"""
