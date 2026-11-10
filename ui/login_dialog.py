"""
Login and registration dialog for PyQt6 desktop application.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget, QWidget, QComboBox
)
from PyQt6.QtCore import Qt
from db.database import SessionLocal
from models.models import User
from core.security import verify_password
from services.auth_service import register_user
from schemas.schemas import UserRegister
from ui.styles import DARK_THEME_QSS


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestor Presupuestario - Acceso")
        self.resize(380, 440)
        self.setStyleSheet(DARK_THEME_QSS)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.authenticated_user = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header Logo & Title
        header = QVBoxLayout()
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = QLabel("💎")
        logo.setStyleSheet("font-size: 36px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(logo)

        title = QLabel("Gestor Presupuestario")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(title)

        subtitle = QLabel("Control de Liquidez y Finanzas Personales")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Tabs: Iniciar Sesión / Registrarse
        self.tabs = QTabWidget()
        self.tab_login = QWidget()
        self.tab_register = QWidget()

        self._setup_login_tab()
        self._setup_register_tab()

        self.tabs.addTab(self.tab_login, "Iniciar Sesión")
        self.tabs.addTab(self.tab_register, "Crear Cuenta")
        layout.addWidget(self.tabs)

    def _setup_login_tab(self):
        vbox = QVBoxLayout(self.tab_login)
        vbox.setSpacing(12)
        vbox.setContentsMargins(0, 16, 0, 0)

        vbox.addWidget(QLabel("Correo Electrónico:"))
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("ejemplo@correo.com")
        vbox.addWidget(self.login_email)

        vbox.addWidget(QLabel("Contraseña:"))
        self.login_pwd = QLineEdit()
        self.login_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_pwd.setPlaceholderText("••••••••")
        vbox.addWidget(self.login_pwd)

        btn_login = QPushButton("Entrar al Sistema")
        btn_login.setObjectName("btn_primary")
        btn_login.setFixedHeight(38)
        btn_login.clicked.connect(self._handle_login)
        vbox.addWidget(btn_login)
        vbox.addStretch()

    def _setup_register_tab(self):
        vbox = QVBoxLayout(self.tab_register)
        vbox.setSpacing(10)
        vbox.setContentsMargins(0, 16, 0, 0)

        vbox.addWidget(QLabel("Nombre de Usuario:"))
        self.reg_user = QLineEdit()
        vbox.addWidget(self.reg_user)

        vbox.addWidget(QLabel("Correo Electrónico:"))
        self.reg_email = QLineEdit()
        vbox.addWidget(self.reg_email)

        vbox.addWidget(QLabel("Contraseña:"))
        self.reg_pwd = QLineEdit()
        self.reg_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        vbox.addWidget(self.reg_pwd)

        vbox.addWidget(QLabel("Moneda Principal:"))
        self.reg_currency = QComboBox()
        self.reg_currency.addItems(["CLP", "USD", "EUR", "ARS", "MXN", "COP", "PEN"])
        vbox.addWidget(self.reg_currency)

        btn_reg = QPushButton("Crear Cuenta")
        btn_reg.setObjectName("btn_primary")
        btn_reg.setFixedHeight(38)
        btn_reg.clicked.connect(self._handle_register)
        vbox.addWidget(btn_reg)
        vbox.addStretch()

    def _handle_login(self):
        email = self.login_email.text().strip()
        pwd = self.login_pwd.text().strip()

        if not email or not pwd:
            QMessageBox.warning(self, "Atención", "Por favor ingresa tu correo y contraseña.")
            return

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email.lower()).first()
            if not user or not verify_password(pwd, user.hashed_password):
                QMessageBox.critical(self, "Error", "Credenciales incorrectas o usuario no encontrado.")
                return
            self.authenticated_user = user
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al autenticar: {e}")
        finally:
            db.close()

    def _handle_register(self):
        user_name = self.reg_user.text().strip()
        email = self.reg_email.text().strip()
        pwd = self.reg_pwd.text().strip()
        currency = self.reg_currency.currentText()

        if not user_name or not email or not pwd:
            QMessageBox.warning(self, "Atención", "Completa todos los campos obligatorios.")
            return

        db = SessionLocal()
        try:
            data = UserRegister(
                username=user_name,
                email=email,
                password=pwd,
                currency_code=currency,
                locale="es-CL" if currency == "CLP" else "en-US"
            )
            token_resp = register_user(db, data)
            user = db.query(User).filter(User.id == token_resp.user.id).first()
            self.authenticated_user = user
            QMessageBox.information(self, "Éxito", "¡Usuario registrado correctamente!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el usuario: {e}")
        finally:
            db.close()
