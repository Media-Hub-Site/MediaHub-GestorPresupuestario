"""
Pydantic schemas for request/response validation.
"""
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════════════════════
class UserRegister(BaseModel):
    email: str = Field(..., min_length=5)
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6)
    currency_code: str = Field(default="USD", max_length=3)
    locale: str = Field(default="en-US", max_length=10)


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    email: str
    username: str
    currency_code: str
    locale: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ═══════════════════════════════════════════════════════════════════════════
# Account
# ═══════════════════════════════════════════════════════════════════════════
class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(default="checking")  # checking|vista|rut|savings|wallet|credit
    initial_balance: float = Field(default=0.0)
    currency_code: str | None = None  # inherits from user if null
    icon: str = Field(default="wallet")
    color: str = Field(default="#6366f1")


class AccountUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    initial_balance: float | None = None
    icon: str | None = None
    color: str | None = None


class AccountRead(BaseModel):
    id: int
    user_id: int
    name: str
    type: str
    initial_balance: float
    current_balance: float
    currency_code: str
    icon: str | None
    color: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════
# Transaction
# ═══════════════════════════════════════════════════════════════════════════
class TransactionCreate(BaseModel):
    account_id: int
    type: str  # INCOME | EXPENSE
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1)
    transaction_date: date | None = None


class TransactionClassify(BaseModel):
    category: str  # FIXED | PERSONAL | SAVINGS | TRANSFER | DEPOSIT


class TransactionReassign(BaseModel):
    account_id: int


class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float = Field(..., gt=0)
    description: str = Field(default="Transferencia interna")
    transaction_date: date | None = None


class TransactionRead(BaseModel):
    id: int
    account_id: int
    type: str
    status: str
    category: str | None
    amount: float
    description: str
    raw_description: str | None
    linked_transaction_id: int | None
    budget_id: int | None
    rule_id: int | None
    transaction_date: date
    created_at: datetime
    updated_at: datetime | None

    # Nested account name for display
    account_name: str | None = None
    account_color: str | None = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════
# Budget
# ═══════════════════════════════════════════════════════════════════════════
class BudgetCreate(BaseModel):
    category: str  # FIXED | PERSONAL | SAVINGS
    monthly_limit: float = Field(..., ge=0)
    annual_limit: float | None = None
    year: int
    month: int = Field(..., ge=1, le=12)


class BudgetUpdate(BaseModel):
    monthly_limit: float | None = None
    annual_limit: float | None = None


class BudgetRead(BaseModel):
    id: int
    user_id: int
    category: str
    monthly_limit: float
    annual_limit: float | None
    year: int
    month: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class BudgetSummary(BaseModel):
    """Budget consumption summary for a given period."""
    category: str
    monthly_limit: float
    annual_limit: float | None
    spent_this_month: float
    spent_this_year: float
    month_progress_pct: float  # 0-100
    year_progress_pct: float | None  # 0-100


# ═══════════════════════════════════════════════════════════════════════════
# Categorization Rule
# ═══════════════════════════════════════════════════════════════════════════
class RuleCreate(BaseModel):
    keyword: str = Field(..., min_length=1)
    category: str  # FIXED | PERSONAL | SAVINGS
    is_active: bool = True
    priority: int = Field(default=0)


class RuleUpdate(BaseModel):
    keyword: str | None = None
    category: str | None = None
    is_active: bool | None = None
    priority: int | None = None


class RuleRead(BaseModel):
    id: int
    user_id: int
    keyword: str
    category: str
    is_active: bool
    priority: int
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════
# Dashboard Metrics
# ═══════════════════════════════════════════════════════════════════════════
class DashboardMetrics(BaseModel):
    total_balance: float
    liquid_balance: float = 0.0          # Liquidez real (excluyendo tarjetas de crédito y cuentas de ahorro bloqueadas)
    pending_amount: float = 0.0          # Monto total en movimientos pendientes de clasificar
    total_income_month: float
    total_expenses_month: float
    pending_count: int
    budget_summaries: list[BudgetSummary]
    accounts_count: int
    currency_code: str
    currency_symbol: str
    active_installments_monthly: float = 0.0  # Compromiso mensual estimado en cuotas


# ═══════════════════════════════════════════════════════════════════════════
# Installment (Cuotas)
# ═══════════════════════════════════════════════════════════════════════════
class InstallmentCreate(BaseModel):
    account_id: int | None = None
    description: str = Field(..., min_length=1, max_length=200)
    total_amount: float = Field(..., gt=0)
    installment_amount: float | None = None  # Si es null, se calcula total_amount / total_installments
    total_installments: int = Field(..., gt=0)
    paid_installments: int = Field(default=0, ge=0)
    start_date: date | None = None
    category: str = Field(default="PERSONAL")


class InstallmentUpdate(BaseModel):
    account_id: int | None = None
    description: str | None = None
    total_amount: float | None = None
    installment_amount: float | None = None
    total_installments: int | None = None
    paid_installments: int | None = None
    start_date: date | None = None
    category: str | None = None
    status: str | None = None


class InstallmentRead(BaseModel):
    id: int
    user_id: int
    account_id: int | None
    account_name: str | None = None
    account_color: str | None = None
    description: str
    total_amount: float
    installment_amount: float
    total_installments: int
    paid_installments: int
    remaining_installments: int
    paid_amount: float
    remaining_amount: float
    progress_pct: float
    start_date: date
    category: str
    status: str
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class InstallmentSummary(BaseModel):
    total_active_debt: float
    total_paid_debt: float
    monthly_commitment: float
    active_count: int
    completed_count: int


# ═══════════════════════════════════════════════════════════════════════════
# Currency
# ═══════════════════════════════════════════════════════════════════════════
class CurrencyRead(BaseModel):
    code: str
    name: str
    symbol: str
    decimals: int
    locale: str
    flag: str
    country: str
