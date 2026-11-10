"""
Accounts and Balances Management View (PyQt6).
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QLineEdit, QDoubleSpinBox, QComboBox
)
from PyQt6.QtCore import Qt
from db.database import SessionLocal
from models.models import User, Account
from schemas.schemas import AccountCreate, AccountUpdate
from services import account_service
from ui.dashboard_view import format_money


class AccountDialog(QDialog):
    def __init__(self, acc: Account | None = None, parent=None):
        super().__init__(parent)
        self.acc = acc
        self.setWindowTitle("Editar Cuenta" if acc else "Nueva Cuenta")
        self.resize(360, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Nombre de la Cuenta:"))
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Ej. BancoEstado RUT, Bci Corriente...")
        if acc:
            self.txt_name.setText(acc.name)
        layout.addWidget(self.txt_name)

        layout.addWidget(QLabel("Tipo de Cuenta:"))
        self.cb_type = QComboBox()
        types = [
            ("Cuenta Corriente", "checking"),
            ("Cuenta Vista", "vista"),
            ("Cuenta RUT", "rut"),
            ("Cuenta de Ahorro", "savings"),
            ("Billetera Digital", "wallet"),
            ("Tarjeta de Crédito", "credit"),
        ]
        for name, val in types:
            self.cb_type.addItem(name, val)
        if acc:
            idx = self.cb_type.findData(acc.type)
            if idx >= 0:
                self.cb_type.setCurrentIndex(idx)
        layout.addWidget(self.cb_type)

        layout.addWidget(QLabel("Saldo Inicial:"))
        self.spn_initial = QDoubleSpinBox()
        self.spn_initial.setMinimum(-100_000_000)
        self.spn_initial.setMaximum(100_000_000)
        if acc:
            self.spn_initial.setValue(acc.initial_balance)
        layout.addWidget(self.spn_initial)

        # Buttons
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
        if not self.txt_name.text().strip():
            QMessageBox.warning(self, "Atención", "El nombre es obligatorio.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.txt_name.text().strip(),
            "type": self.cb_type.currentData(),
            "initial_balance": self.spn_initial.value(),
        }


class AccountsView(QWidget):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        h_head = QHBoxLayout()
        lbl_head = QLabel("🏦 Cuentas Bancarias y Saldos")
        lbl_head.setObjectName("title")
        h_head.addWidget(lbl_head)
        h_head.addStretch()

        btn_add = QPushButton("+ Nueva Cuenta")
        btn_add.setObjectName("btn_primary")
        btn_add.clicked.connect(self._handle_add)
        h_head.addWidget(btn_add)
        layout.addLayout(h_head)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Nombre", "Tipo", "Saldo Inicial", "Saldo Actual", "Acciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            accounts = account_service.get_accounts(db, self.user.id)
            code = self.user.currency_code or "USD"

            self.table.setRowCount(len(accounts))
            for row, acc in enumerate(accounts):
                self.table.setItem(row, 0, QTableWidgetItem(acc.name))
                self.table.setItem(row, 1, QTableWidgetItem(acc.type.capitalize()))
                self.table.setItem(row, 2, QTableWidgetItem(format_money(acc.initial_balance, code)))

                cur_item = QTableWidgetItem(format_money(acc.current_balance, code))
                cur_item.setForeground(Qt.GlobalColor.green if acc.current_balance >= 0 else Qt.GlobalColor.red)
                self.table.setItem(row, 3, cur_item)

                # Actions
                w_act = QWidget()
                h_act = QHBoxLayout(w_act)
                h_act.setContentsMargins(4, 2, 4, 2)
                h_act.setSpacing(6)

                btn_edit = QPushButton("✏️")
                btn_edit.clicked.connect(lambda _, a=acc: self._handle_edit(a))
                h_act.addWidget(btn_edit)

                btn_del = QPushButton("🗑️")
                btn_del.setObjectName("btn_danger")
                btn_del.clicked.connect(lambda _, a_id=acc.id: self._handle_delete(a_id))
                h_act.addWidget(btn_del)

                self.table.setCellWidget(row, 4, w_act)
        finally:
            db.close()

    def _handle_add(self):
        dlg = AccountDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db = SessionLocal()
            try:
                account_service.create_account(db, self.user, AccountCreate(**data))
            finally:
                db.close()
            self.refresh()

    def _handle_edit(self, acc: Account):
        dlg = AccountDialog(acc=acc, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db = SessionLocal()
            try:
                account_service.update_account(db, self.user.id, acc.id, AccountUpdate(**data))
            finally:
                db.close()
            self.refresh()

    def _handle_delete(self, acc_id: int):
        if QMessageBox.question(self, "Confirmar", "¿Eliminar esta cuenta y todos sus movimientos?") == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            try:
                account_service.delete_account(db, self.user.id, acc_id)
            finally:
                db.close()
            self.refresh()
