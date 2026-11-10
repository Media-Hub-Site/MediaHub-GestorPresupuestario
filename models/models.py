"""
SQLAlchemy ORM models for the budget management application.
"""
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    currency_code = Column(String(3), nullable=False, default="USD")
    locale = Column(String(10), nullable=False, default="en-US")
    created_at = Column(DateTime, default=_utcnow)

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    rules = relationship("CategorizationRule", back_populates="user", cascade="all, delete-orphan")
    email_integration = relationship("EmailIntegration", back_populates="user", uselist=False, cascade="all, delete-orphan")
    installments = relationship("Installment", back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False, default="checking")  # checking|vista|rut|savings|wallet|credit
    initial_balance = Column(Float, nullable=False, default=0.0)
    current_balance = Column(Float, nullable=False, default=0.0)
    currency_code = Column(String(3), nullable=False, default="USD")
    icon = Column(String, nullable=True, default="wallet")
    color = Column(String, nullable=True, default="#6366f1")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    installments = relationship("Installment", back_populates="account")


# ---------------------------------------------------------------------------
# Transaction
# ---------------------------------------------------------------------------
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    type = Column(String, nullable=False)            # INCOME | EXPENSE | TRANSFER
    status = Column(String, nullable=False, default="PENDING")  # PENDING | CLASSIFIED | TRANSFER
    category = Column(String, nullable=True)          # FIXED | PERSONAL | SAVINGS | TRANSFER | null
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    raw_description = Column(String, nullable=True)
    linked_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=True)
    rule_id = Column(Integer, ForeignKey("categorization_rules.id"), nullable=True)
    transaction_date = Column(Date, nullable=False, default=lambda: date.today())
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    account = relationship("Account", back_populates="transactions")
    budget = relationship("Budget", back_populates="transactions")
    rule = relationship("CategorizationRule", back_populates="transactions")
    linked_transaction = relationship("Transaction", remote_side=[id], foreign_keys=[linked_transaction_id])


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------
class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)  # FIXED | PERSONAL | SAVINGS
    monthly_limit = Column(Float, nullable=False, default=0.0)
    annual_limit = Column(Float, nullable=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="budgets")
    transactions = relationship("Transaction", back_populates="budget")


# ---------------------------------------------------------------------------
# Categorization Rule
# ---------------------------------------------------------------------------
class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keyword = Column(String, nullable=False)
    category = Column(String, nullable=False)  # FIXED | PERSONAL | SAVINGS
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)

    # Relationships
    user = relationship("User", back_populates="rules")
    transactions = relationship("Transaction", back_populates="rule")


# ---------------------------------------------------------------------------
# Email Integration
# ---------------------------------------------------------------------------
class EmailIntegration(Base):
    __tablename__ = "email_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    imap_server = Column(String, nullable=False, default="imap.gmail.com")
    imap_port = Column(Integer, nullable=False, default=993)
    encrypted_password = Column(String, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="email_integration")


# ---------------------------------------------------------------------------
# Installment (Seguimiento de compras en cuotas / créditos)
# ---------------------------------------------------------------------------
class Installment(Base):
    __tablename__ = "installments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)  # Cuenta/tarjeta asociada
    description = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)        # Monto total de la compra/deuda
    installment_amount = Column(Float, nullable=False)  # Monto de cada cuota
    total_installments = Column(Integer, nullable=False) # Cantidad total de cuotas (ej. 12)
    paid_installments = Column(Integer, nullable=False, default=0) # Cuotas pagadas acumuladas (ej. 4)
    start_date = Column(Date, nullable=False, default=lambda: date.today())
    category = Column(String, nullable=False, default="PERSONAL") # FIXED | PERSONAL | SAVINGS
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE | COMPLETED
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="installments")
    account = relationship("Account", back_populates="installments")
