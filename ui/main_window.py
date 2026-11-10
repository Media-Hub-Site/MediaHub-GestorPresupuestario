"""
Main Window containing Sidebar navigation and stacked views.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from models.models import User
from ui.dashboard_view import DashboardView
from ui.transactions_view import TransactionsView
from ui.installments_view import InstallmentsView
from ui.accounts_view import AccountsView
from ui.styles import DARK_THEME_QSS


class MainWindow(QMainWindow):
    def __init__(self, current_user: User):
        super().__init__()
        self.user = current_user
        self.setWindowTitle(f"Gestor Presupuestario — {self.user.username} ({self.user.currency_code})")
        self.resize(1150, 720)
        self.setStyleSheet(DARK_THEME_QSS)

        # Central container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 20, 14, 20)
        side_layout.setSpacing(8)

        # Logo
        h_logo = QHBoxLayout()
        logo_icon = QLabel("💎")
        logo_icon.setStyleSheet("font-size: 24px;")
        logo_text = QLabel("Presupuesto")
        logo_text.setStyleSheet("font-size: 17px; font-weight: bold; color: #ffffff;")
        h_logo.addWidget(logo_icon)
        h_logo.addWidget(logo_text)
        h_logo.addStretch()
        side_layout.addLayout(h_logo)
        side_layout.addSpacing(16)

        # Navigation Buttons
        self.nav_buttons = []
        nav_items = [
            ("📊 Dashboard", 0),
            ("📥 Pendientes", 1),
            ("💸 Cargos / Gastos", 2),
            ("💰 Abonos / Ingresos", 3),
            ("💳 Cuotas y Créditos", 4),
            ("🏦 Cuentas y Saldos", 5),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=index: self._switch_page(idx))
            side_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        side_layout.addStretch()

        # User info footer
        user_frame = QFrame()
        user_frame.setObjectName("card")
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(10, 10, 10, 10)
        lbl_uname = QLabel(f"👤 {self.user.username}")
        lbl_uname.setStyleSheet("font-weight: 600;")
        lbl_email = QLabel(self.user.email)
        lbl_email.setObjectName("subtitle")
        user_layout.addWidget(lbl_uname)
        user_layout.addWidget(lbl_email)
        side_layout.addWidget(user_frame)

        main_layout.addWidget(sidebar)

        # 2. Main content stack
        self.stack = QStackedWidget()
        self.view_dashboard = DashboardView(self.user)
        self.view_pending = TransactionsView(self.user, mode="PENDING")
        self.view_expenses = TransactionsView(self.user, mode="EXPENSE")
        self.view_income = TransactionsView(self.user, mode="INCOME")
        self.view_installments = InstallmentsView(self.user)
        self.view_accounts = AccountsView(self.user)

        self.stack.addWidget(self.view_dashboard)
        self.stack.addWidget(self.view_pending)
        self.stack.addWidget(self.view_expenses)
        self.stack.addWidget(self.view_income)
        self.stack.addWidget(self.view_installments)
        self.stack.addWidget(self.view_accounts)

        main_layout.addWidget(self.stack)

        # Select first nav button
        self._switch_page(0)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

        # Refresh active view on switch
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, "refresh"):
            current_widget.refresh()
