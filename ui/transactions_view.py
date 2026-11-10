"""
Transactions view for Expenses (Cargos), Income (Abonos), and Pending (Pendientes).
"""
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QDialog, QLineEdit, QDoubleSpinBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from db.database import SessionLocal
from models.models import User, Account, Transaction
from schemas.schemas import TransactionCreate, TransactionClassify
from services import transaction_service
from ui.dashboard_view import format_money


class TransactionDialog(QDialog):
    def __init__(self, user: User, accounts: list[Account], tx_type: str = "EXPENSE", parent=None):
        super().__init__(parent)
        self.user = user
        self.accounts = accounts
        self.tx_type = tx_type
        self.setWindowTitle("Nuevo Gasto / Cargo" if tx_type == "EXPENSE" else "Nuevo Ingreso / Abono")
        self.resize(380, 360)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Descripción:"))
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Ej. Supermercado, Sueldo, Uber...")
        layout.addWidget(self.txt_desc)

        layout.addWidget(QLabel("Monto:"))
        self.spn_amount = QDoubleSpinBox()
        self.spn_amount.setMaximum(100_000_000)
        layout.addWidget(self.spn_amount)

        layout.addWidget(QLabel("Cuenta:"))
        self.cb_acc = QComboBox()
        for a in self.accounts:
            self.cb_acc.addItem(f"{a.name} ({a.type})", a.id)
        layout.addWidget(self.cb_acc)

        layout.addWidget(QLabel("Fecha:"))
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        layout.addWidget(self.date_picker)

        # Dialog buttons
        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _save(self):
        if not self.txt_desc.text().strip():
            QMessageBox.warning(self, "Atención", "Ingresa una descripción.")
            return
        if self.spn_amount.value() <= 0:
            QMessageBox.warning(self, "Atención", "El monto debe ser mayor a 0.")
            return
        self.accept()

    def get_data(self) -> dict:
        qdate = self.date_picker.date()
        return {
            "account_id": self.cb_acc.currentData(),
            "type": self.tx_type,
            "amount": self.spn_amount.value(),
            "description": self.txt_desc.text().strip(),
            "transaction_date": date(qdate.year(), qdate.month(), qdate.day()),
        }


class TransactionsView(QWidget):
    def __init__(self, user: User, mode: str = "EXPENSE", parent=None):
        super().__init__(parent)
        self.user = user
        self.mode = mode  # "EXPENSE", "INCOME", or "PENDING"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        h_head = QHBoxLayout()
        titles = {
            "EXPENSE": "💸 Cargos y Gastos",
            "INCOME": "💰 Abonos e Ingresos",
            "PENDING": "📥 Movimientos Pendientes de Clasificar"
        }
        lbl_head = QLabel(titles.get(mode, "Transacciones"))
        lbl_head.setObjectName("title")
        h_head.addWidget(lbl_head)
        h_head.addStretch()

        if mode != "PENDING":
            btn_add = QPushButton("+ Registrar Movimiento")
            btn_add.setObjectName("btn_primary")
            btn_add.clicked.connect(self._handle_add)
            h_head.addWidget(btn_add)

        layout.addLayout(h_head)

        # Table
        self.table = QTableWidget()
        cols = ["Descripción", "Monto", "Cuenta", "Fecha", "Categoría / Estado"]
        if mode == "PENDING":
            cols.append("Clasificar")
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            code = self.user.currency_code or "USD"
            if self.mode == "PENDING":
                txs = transaction_service.get_pending_transactions(db, self.user.id)
            elif self.mode == "EXPENSE":
                txs = transaction_service.get_transactions(db, self.user.id, type_filter="EXPENSE")
            else:
                txs = transaction_service.get_transactions(db, self.user.id, type_filter="INCOME")

            self.table.setRowCount(len(txs))
            for row, tx in enumerate(txs):
                self.table.setItem(row, 0, QTableWidgetItem(tx.description))

                # Color formatting for amount
                amt_str = ("-" if tx.type == "EXPENSE" else "+") + format_money(tx.amount, code)
                item_amt = QTableWidgetItem(amt_str)
                item_amt.setForeground(Qt.GlobalColor.red if tx.type == "EXPENSE" else Qt.GlobalColor.green)
                self.table.setItem(row, 1, item_amt)

                self.table.setItem(row, 2, QTableWidgetItem(tx.account.name if tx.account else "-"))
                self.table.setItem(row, 3, QTableWidgetItem(str(tx.transaction_date)))

                cat_label = tx.category or tx.status
                self.table.setItem(row, 4, QTableWidgetItem(cat_label))

                if self.mode == "PENDING":
                    # Classification quick buttons
                    w_classify = QWidget()
                    h_btn = QHBoxLayout(w_classify)
                    h_btn.setContentsMargins(2, 2, 2, 2)
                    h_btn.setSpacing(4)

                    btn_fijo = QPushButton("📌 Fijo")
                    btn_fijo.clicked.connect(lambda _, t_id=tx.id: self._classify(t_id, "FIXED"))
                    btn_pers = QPushButton("🛍️ Personal")
                    btn_pers.clicked.connect(lambda _, t_id=tx.id: self._classify(t_id, "PERSONAL"))
                    btn_aho = QPushButton("🏦 Ahorro")
                    btn_aho.clicked.connect(lambda _, t_id=tx.id: self._classify(t_id, "SAVINGS"))
                    btn_dep = QPushButton("💵 Depósito")
                    btn_dep.clicked.connect(lambda _, t_id=tx.id: self._classify(t_id, "DEPOSIT"))

                    h_btn.addWidget(btn_fijo)
                    h_btn.addWidget(btn_pers)
                    h_btn.addWidget(btn_aho)
                    h_btn.addWidget(btn_dep)
                    self.table.setCellWidget(row, 5, w_classify)
        finally:
            db.close()

    def _classify(self, tx_id: int, category: str):
        db = SessionLocal()
        try:
            transaction_service.classify_transaction(db, self.user, tx_id, TransactionClassify(category=category))
        finally:
            db.close()
        self.refresh()

    def _handle_add(self):
        db = SessionLocal()
        try:
            accounts = db.query(Account).filter(Account.user_id == self.user.id).all()
        finally:
            db.close()

        if not accounts:
            QMessageBox.warning(self, "Sin Cuentas", "Primero debes crear una cuenta en el módulo de Cuentas.")
            return

        dlg = TransactionDialog(self.user, accounts, tx_type=self.mode, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db = SessionLocal()
            try:
                transaction_service.ingest_transaction(db, self.user, TransactionCreate(**data))
            finally:
                db.close()
            self.refresh()
