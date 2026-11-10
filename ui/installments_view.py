"""
Installments & Credit Purchases Management View (PyQt6).
Allows tracking of installment payments accumulated in months or money.
"""
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QDateEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QDate
from db.database import SessionLocal
from models.models import User, Account
from schemas.schemas import InstallmentCreate, InstallmentUpdate
from services import installment_service
from ui.dashboard_view import format_money


class InstallmentFormDialog(QDialog):
    def __init__(self, user: User, accounts: list[Account], inst_data: dict | None = None, parent=None):
        super().__init__(parent)
        self.user = user
        self.accounts = accounts
        self.inst_data = inst_data
        self.setWindowTitle("Modificar Cuota" if inst_data else "Registrar Compra en Cuotas")
        self.resize(460, 520)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Description
        layout.addWidget(QLabel("Descripción de la compra o crédito:"))
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Ej. Celular, Pasajes, Laptop...")
        if inst_data:
            self.txt_desc.setText(inst_data.get("description", ""))
        layout.addWidget(self.txt_desc)

        # Total amount & Total installments
        h_nums = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Monto Total:"))
        self.spn_total = QDoubleSpinBox()
        self.spn_total.setMaximum(100_000_000)
        self.spn_total.setValue(inst_data.get("total_amount", 0.0) if inst_data else 0.0)
        self.spn_total.valueChanged.connect(self._auto_calc_cuota)
        v1.addWidget(self.spn_total)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Total de Cuotas (Meses):"))
        self.spn_cuotas = QSpinBox()
        self.spn_cuotas.setRange(1, 120)
        self.spn_cuotas.setValue(inst_data.get("total_installments", 12) if inst_data else 12)
        self.spn_cuotas.valueChanged.connect(self._auto_calc_cuota)
        v2.addWidget(self.spn_cuotas)
        h_nums.addLayout(v1)
        h_nums.addLayout(v2)
        layout.addLayout(h_nums)

        # Installment amount & Start date
        h_nums2 = QHBoxLayout()
        v3 = QVBoxLayout()
        v3.addWidget(QLabel("Monto por Cuota:"))
        self.spn_cuota_amt = QDoubleSpinBox()
        self.spn_cuota_amt.setMaximum(100_000_000)
        self.spn_cuota_amt.setValue(inst_data.get("installment_amount", 0.0) if inst_data else 0.0)
        v3.addWidget(self.spn_cuota_amt)

        v4 = QVBoxLayout()
        v4.addWidget(QLabel("Fecha de Inicio:"))
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        if inst_data and inst_data.get("start_date"):
            sd = inst_data["start_date"]
            self.date_start.setDate(QDate(sd.year, sd.month, sd.day))
        else:
            self.date_start.setDate(QDate.currentDate())
        v4.addWidget(self.date_start)
        h_nums2.addLayout(v3)
        h_nums2.addLayout(v4)
        layout.addLayout(h_nums2)

        # Progress Accumulator Frame (Months vs Money)
        accum_frame = QFrame()
        accum_frame.setObjectName("card")
        accum_layout = QVBoxLayout(accum_frame)
        accum_layout.addWidget(QLabel("<b>Cuotas Pagadas Acumuladas:</b>"))

        btn_group = QHBoxLayout()
        self.rb_months = QRadioButton("Por Meses / Cuotas")
        self.rb_money = QRadioButton("Por Dinero ($)")
        self.rb_months.setChecked(True)
        btn_group.addWidget(self.rb_months)
        btn_group.addWidget(self.rb_money)
        accum_layout.addLayout(btn_group)

        self.spn_paid_months = QSpinBox()
        self.spn_paid_months.setRange(0, 120)
        self.spn_paid_months.setValue(inst_data.get("paid_installments", 0) if inst_data else 0)
        accum_layout.addWidget(self.spn_paid_months)

        self.spn_paid_money = QDoubleSpinBox()
        self.spn_paid_money.setMaximum(100_000_000)
        self.spn_paid_money.setValue(inst_data.get("paid_amount", 0.0) if inst_data else 0.0)
        self.spn_paid_money.setVisible(False)
        self.spn_paid_money.valueChanged.connect(self._sync_paid_money)
        accum_layout.addWidget(self.spn_paid_money)

        self.rb_months.toggled.connect(lambda chk: self.spn_paid_months.setVisible(chk))
        self.rb_money.toggled.connect(lambda chk: self.spn_paid_money.setVisible(chk))

        layout.addWidget(accum_frame)

        # Account & Category
        h_acc = QHBoxLayout()
        v5 = QVBoxLayout()
        v5.addWidget(QLabel("Tarjeta o Cuenta Asociada:"))
        self.cb_account = QComboBox()
        self.cb_account.addItem("(Sin asignar)", None)
        for acc in self.accounts:
            self.cb_account.addItem(f"{acc.name} ({acc.type})", acc.id)
        if inst_data and inst_data.get("account_id"):
            idx = self.cb_account.findData(inst_data["account_id"])
            if idx >= 0:
                self.cb_account.setCurrentIndex(idx)
        v5.addWidget(self.cb_account)

        v6 = QVBoxLayout()
        v6.addWidget(QLabel("Categoría:"))
        self.cb_cat = QComboBox()
        self.cb_cat.addItem("🛍️ Gasto Personal", "PERSONAL")
        self.cb_cat.addItem("📌 Gasto Fijo", "FIXED")
        self.cb_cat.addItem("🏦 Ahorro / Inversión", "SAVINGS")
        if inst_data and inst_data.get("category"):
            idx = self.cb_cat.findData(inst_data["category"])
            if idx >= 0:
                self.cb_cat.setCurrentIndex(idx)
        v6.addWidget(self.cb_cat)
        h_acc.addLayout(v5)
        h_acc.addLayout(v6)
        layout.addLayout(h_acc)

        # Dialog Buttons
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

    def _auto_calc_cuota(self):
        tot = self.spn_total.value()
        cuotas = max(1, self.spn_cuotas.value())
        if tot > 0:
            self.spn_cuota_amt.setValue(round(tot / cuotas, 2))

    def _sync_paid_money(self, money: float):
        cuota = self.spn_cuota_amt.value()
        if cuota > 0:
            calc_months = min(self.spn_cuotas.value(), int(round(money / cuota)))
            self.spn_paid_months.setValue(calc_months)

    def _save(self):
        if not self.txt_desc.text().strip():
            QMessageBox.warning(self, "Atención", "Ingresa una descripción.")
            return
        if self.spn_total.value() <= 0:
            QMessageBox.warning(self, "Atención", "El monto total debe ser mayor a cero.")
            return
        self.accept()

    def get_data(self) -> dict:
        qdate = self.date_start.date()
        st_date = date(qdate.year(), qdate.month(), qdate.day())
        return {
            "description": self.txt_desc.text().strip(),
            "total_amount": self.spn_total.value(),
            "installment_amount": self.spn_cuota_amt.value(),
            "total_installments": self.spn_cuotas.value(),
            "paid_installments": self.spn_paid_months.value(),
            "start_date": st_date,
            "account_id": self.cb_account.currentData(),
            "category": self.cb_cat.currentData(),
        }


class InstallmentsView(QWidget):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.user = user

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Row
        h_head = QHBoxLayout()
        lbl_head = QLabel("💳 Seguimiento de Cuotas y Créditos")
        lbl_head.setObjectName("title")
        h_head.addWidget(lbl_head)
        h_head.addStretch()

        btn_add = QPushButton("+ Registrar Nueva Compra")
        btn_add.setObjectName("btn_primary")
        btn_add.clicked.connect(self._handle_add)
        h_head.addWidget(btn_add)
        layout.addLayout(h_head)

        # KPI Summary Row
        self.h_kpis = QHBoxLayout()
        layout.addLayout(self.h_kpis)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Descripción", "Monto Total", "Cuota Mensual", "Avance Cuotas",
            "Deuda Restante", "Tarjeta / Cuenta", "Estado", "Acciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        # Clear KPIs
        for i in reversed(range(self.h_kpis.count())):
            w = self.h_kpis.itemAt(i).widget()
            if w:
                w.setParent(None)

        db = SessionLocal()
        try:
            summary = installment_service.get_installment_summary(db, self.user.id)
            items = installment_service.get_installments(db, self.user.id)
            code = self.user.currency_code or "USD"

            # Render KPI mini cards
            k1 = QFrame()
            k1.setObjectName("card")
            l1 = QVBoxLayout(k1)
            l1.addWidget(QLabel("DEUDA ACTIVA RESTANTE"))
            val1 = QLabel(format_money(summary.total_active_debt, code))
            val1.setStyleSheet("font-size: 20px; font-weight: bold; color: #f87171;")
            l1.addWidget(val1)
            self.h_kpis.addWidget(k1)

            k2 = QFrame()
            k2.setObjectName("card")
            l2 = QVBoxLayout(k2)
            l2.addWidget(QLabel("COMPROMISO MENSUAL EN CUOTAS"))
            val2 = QLabel(format_money(summary.monthly_commitment, code))
            val2.setStyleSheet("font-size: 20px; font-weight: bold; color: #fbbf24;")
            l2.addWidget(val2)
            self.h_kpis.addWidget(k2)

            k3 = QFrame()
            k3.setObjectName("card")
            l3 = QVBoxLayout(k3)
            l3.addWidget(QLabel("TOTAL YA AMORTIZADO"))
            val3 = QLabel(format_money(summary.total_paid_debt, code))
            val3.setStyleSheet("font-size: 20px; font-weight: bold; color: #4ade80;")
            l3.addWidget(val3)
            self.h_kpis.addWidget(k3)

            # Populate Table
            self.table.setRowCount(len(items))
            for row, inst in enumerate(items):
                self.table.setItem(row, 0, QTableWidgetItem(inst["description"]))
                self.table.setItem(row, 1, QTableWidgetItem(format_money(inst["total_amount"], code)))
                self.table.setItem(row, 2, QTableWidgetItem(format_money(inst["installment_amount"], code)))

                progress_str = f"{inst['paid_installments']} / {inst['total_installments']} ({inst['progress_pct']}%)"
                self.table.setItem(row, 3, QTableWidgetItem(progress_str))
                self.table.setItem(row, 4, QTableWidgetItem(format_money(inst["remaining_amount"], code)))
                self.table.setItem(row, 5, QTableWidgetItem(inst.get("account_name") or "-"))

                is_done = inst["status"] == "COMPLETED" or inst["paid_installments"] >= inst["total_installments"]
                st_item = QTableWidgetItem("✓ Finalizada" if is_done else "Activa")
                st_item.setForeground(Qt.GlobalColor.green if is_done else Qt.GlobalColor.yellow)
                self.table.setItem(row, 6, st_item)

                # Actions Widget (Pay Next + Edit + Delete)
                w_actions = QWidget()
                h_act = QHBoxLayout(w_actions)
                h_act.setContentsMargins(4, 2, 4, 2)
                h_act.setSpacing(6)

                if not is_done:
                    btn_pay = QPushButton("➕ Pagar 1 Cuota")
                    btn_pay.setObjectName("btn_success")
                    btn_pay.clicked.connect(lambda _, i_id=inst["id"]: self._handle_pay_next(i_id))
                    h_act.addWidget(btn_pay)

                btn_edit = QPushButton("✏️")
                btn_edit.setToolTip("Editar cuota")
                btn_edit.clicked.connect(lambda _, item=inst: self._handle_edit(item))
                h_act.addWidget(btn_edit)

                btn_del = QPushButton("🗑️")
                btn_del.setObjectName("btn_danger")
                btn_del.setToolTip("Eliminar")
                btn_del.clicked.connect(lambda _, i_id=inst["id"]: self._handle_delete(i_id))
                h_act.addWidget(btn_del)

                self.table.setCellWidget(row, 7, w_actions)

        finally:
            db.close()

    def _handle_add(self):
        db = SessionLocal()
        try:
            accounts = db.query(Account).filter(Account.user_id == self.user.id).all()
        finally:
            db.close()

        dlg = InstallmentFormDialog(self.user, accounts, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db = SessionLocal()
            try:
                installment_service.create_installment(db, self.user, InstallmentCreate(**data))
            finally:
                db.close()
            self.refresh()

    def _handle_edit(self, inst: dict):
        db = SessionLocal()
        try:
            accounts = db.query(Account).filter(Account.user_id == self.user.id).all()
        finally:
            db.close()

        dlg = InstallmentFormDialog(self.user, accounts, inst_data=inst, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db = SessionLocal()
            try:
                installment_service.update_installment(db, self.user.id, inst["id"], InstallmentUpdate(**data))
            finally:
                db.close()
            self.refresh()

    def _handle_pay_next(self, inst_id: int):
        db = SessionLocal()
        try:
            installment_service.increment_installment(db, self.user.id, inst_id)
        finally:
            db.close()
        self.refresh()

    def _handle_delete(self, inst_id: int):
        if QMessageBox.question(self, "Confirmar", "¿Eliminar esta compra en cuotas?") == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            try:
                installment_service.delete_installment(db, self.user.id, inst_id)
            finally:
                db.close()
            self.refresh()
