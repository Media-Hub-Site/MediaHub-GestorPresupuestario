"""
Dashboard View (PyQt6) with KPI Metrics, Liquidity, and Budget Cards.
"""
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt
from db.database import SessionLocal
from models.models import User, Account, Transaction
from services.budget_service import get_budget_summary
from services.installment_service import get_installment_summary
from services.transaction_service import get_transaction_count
from core.currencies import get_currency
from sqlalchemy import func, extract


def format_money(amount: float, currency_code: str = "USD") -> str:
    symbol = "$"
    if currency_code == "EUR":
        symbol = "€"
    elif currency_code == "GBP":
        symbol = "£"

    if currency_code in ["CLP", "COP", "ARS"]:
        return f"{symbol}{int(amount):,}".replace(",", ".")
    return f"{symbol}{amount:,.2f}"


class MetricCard(QFrame):
    def __init__(self, icon: str, label: str, value: str, subtext: str, color: str = "#818cf8"):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        top_row = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 18px;")
        lbl_title = QLabel(label)
        lbl_title.setObjectName("metric_lbl")
        top_row.addWidget(lbl_icon)
        top_row.addWidget(lbl_title)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.val_lbl = QLabel(value)
        self.val_lbl.setObjectName("metric_val")
        self.val_lbl.setStyleSheet(f"color: {color};")
        layout.addWidget(self.val_lbl)

        self.sub_lbl = QLabel(subtext)
        self.sub_lbl.setObjectName("subtitle")
        layout.addWidget(self.sub_lbl)


class DashboardView(QWidget):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Scroll Area for clean layout on small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(24)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Header Title
        lbl_head = QLabel("📊 Panel Financiero y Liquidez")
        lbl_head.setObjectName("title")
        self.content_layout.addWidget(lbl_head)

        # Metrics Grid
        self.grid_metrics = QGridLayout()
        self.grid_metrics.setSpacing(16)
        self.content_layout.addLayout(self.grid_metrics)

        # Budget Progress Section
        self.budget_box = QVBoxLayout()
        self.budget_box.setSpacing(12)
        lbl_budget_sec = QLabel("📈 Cumplimiento del Presupuesto Mensual")
        lbl_budget_sec.setStyleSheet("font-size: 16px; font-weight: 600; color: #ffffff;")
        self.budget_box.addWidget(lbl_budget_sec)
        self.budget_cards_layout = QHBoxLayout()
        self.budget_cards_layout.setSpacing(16)
        self.budget_box.addLayout(self.budget_cards_layout)
        self.content_layout.addLayout(self.budget_box)

        self.content_layout.addStretch()
        self.refresh()

    def refresh(self):
        # Clear existing metric widgets
        for i in reversed(range(self.grid_metrics.count())):
            w = self.grid_metrics.itemAt(i).widget()
            if w:
                w.setParent(None)

        for i in reversed(range(self.budget_cards_layout.count())):
            w = self.budget_cards_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        db = SessionLocal()
        try:
            today = date.today()
            code = self.user.currency_code or "USD"

            # 1. Total balance
            total_balance = db.query(func.coalesce(func.sum(Account.current_balance), 0.0)).filter(
                Account.user_id == self.user.id
            ).scalar()

            # 2. Liquid balance
            liquid_balance = db.query(func.coalesce(func.sum(Account.current_balance), 0.0)).filter(
                Account.user_id == self.user.id,
                Account.type.in_(["checking", "vista", "rut", "wallet"])
            ).scalar()

            # 3. Income this month
            income_month = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).join(Account).filter(
                Account.user_id == self.user.id,
                Transaction.type == "INCOME",
                extract("year", Transaction.transaction_date) == today.year,
                extract("month", Transaction.transaction_date) == today.month,
            ).scalar()

            # 4. Expenses this month
            expenses_month = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).join(Account).filter(
                Account.user_id == self.user.id,
                Transaction.type == "EXPENSE",
                Transaction.status == "CLASSIFIED",
                extract("year", Transaction.transaction_date) == today.year,
                extract("month", Transaction.transaction_date) == today.month,
            ).scalar()

            pending_count = get_transaction_count(db, self.user.id, status_filter="PENDING")
            inst_summary = get_installment_summary(db, self.user.id)
            budgets = get_budget_summary(db, self.user.id, today.year, today.month)

            # Metric Cards
            card_liquidity = MetricCard(
                "💰", "Liquidez Disponible",
                format_money(float(liquid_balance), code),
                f"Patrimonio total: {format_money(float(total_balance), code)}",
                "#818cf8"
            )
            card_income = MetricCard(
                "📈", "Ingresos del Mes",
                format_money(float(income_month), code),
                "Entradas del mes en curso",
                "#4ade80"
            )
            card_expense = MetricCard(
                "💸", "Gastos del Mes",
                format_money(float(expenses_month), code),
                f"+ {format_money(inst_summary.monthly_commitment, code)}/mes en cuotas",
                "#f87171"
            )
            card_pending = MetricCard(
                "📥", "Pendientes",
                str(pending_count),
                "Movimientos por clasificar",
                "#fbbf24"
            )

            self.grid_metrics.addWidget(card_liquidity, 0, 0)
            self.grid_metrics.addWidget(card_income, 0, 1)
            self.grid_metrics.addWidget(card_expense, 1, 0)
            self.grid_metrics.addWidget(card_pending, 1, 1)

            # Budget progress cards
            cat_names = {"FIXED": "📌 Gasto Fijo", "PERSONAL": "🛍️ Gasto Personal", "SAVINGS": "🏦 Ahorro"}
            if not budgets:
                lbl_none = QLabel("No hay límites presupuestarios definidos para este mes.")
                lbl_none.setObjectName("subtitle")
                self.budget_cards_layout.addWidget(lbl_none)
            else:
                for b in budgets:
                    bcard = QFrame()
                    bcard.setObjectName("card")
                    bcard.setFixedHeight(115)
                    blayout = QVBoxLayout(bcard)

                    top = QHBoxLayout()
                    lbl_cat = QLabel(cat_names.get(b.category, b.category))
                    lbl_cat.setStyleSheet("font-weight: 600;")
                    pct = min(100, int(b.month_progress_pct))
                    lbl_pct = QLabel(f"{pct}%")
                    lbl_pct.setObjectName("subtitle")
                    top.addWidget(lbl_cat)
                    top.addStretch()
                    top.addWidget(lbl_pct)
                    blayout.addLayout(top)

                    pbar = QProgressBar()
                    pbar.setRange(0, 100)
                    pbar.setValue(pct)
                    if pct > 85:
                        pbar.setStyleSheet("QProgressBar::chunk { background: #ef4444; }")
                    blayout.addWidget(pbar)

                    bottom = QHBoxLayout()
                    lbl_spent = QLabel(f"Gastado: {format_money(b.spent_this_month, code)}")
                    lbl_spent.setStyleSheet("font-size: 11px; color: #94a3b8;")
                    lbl_limit = QLabel(f"Límite: {format_money(b.monthly_limit, code)}")
                    lbl_limit.setStyleSheet("font-size: 11px; color: #94a3b8;")
                    bottom.addWidget(lbl_spent)
                    bottom.addStretch()
                    bottom.addWidget(lbl_limit)
                    blayout.addLayout(bottom)

                    self.budget_cards_layout.addWidget(bcard)
        finally:
            db.close()
