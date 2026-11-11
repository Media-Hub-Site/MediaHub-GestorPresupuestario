"""
Transaction service: ingest, classify, transfer, and query transactions.
"""
from datetime import date
from core.exceptions import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.models import Account, Transaction, CategorizationRule, Budget, User
from schemas.schemas import TransactionCreate, TransactionClassify, TransferCreate
from services.account_service import recalculate_balance


def _try_auto_classify(db: Session, user_id: int, description: str) -> tuple[str | None, int | None]:
    """
    Attempt to auto-classify a transaction by matching its description
    against the user's active categorization rules, ordered by priority.
    Returns (category, rule_id) or (None, None).
    """
    rules = (
        db.query(CategorizationRule)
        .filter(
            CategorizationRule.user_id == user_id,
            CategorizationRule.is_active == True,
        )
        .order_by(CategorizationRule.priority.desc())
        .all()
    )
    desc_lower = description.lower()
    for rule in rules:
        if rule.keyword.lower() in desc_lower:
            return rule.category, rule.id
    return None, None


def _find_budget(db: Session, user_id: int, category: str, tx_date: date) -> int | None:
    """Find the matching budget for a category and date."""
    budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.category == category,
            Budget.year == tx_date.year,
            Budget.month == tx_date.month,
        )
        .first()
    )
    return budget.id if budget else None


def ingest_transaction(db: Session, user: User, data: TransactionCreate) -> Transaction:
    """
    Ingest a new transaction. Attempts auto-classification by rules.
    Updates the account balance accordingly.
    """
    # Verify account belongs to user
    account = (
        db.query(Account)
        .filter(Account.id == data.account_id, Account.user_id == user.id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    tx_date = data.transaction_date or date.today()

    # Try auto-classify for expenses
    category = None
    rule_id = None
    tx_status = "PENDING"

    if data.type == "EXPENSE":
        category, rule_id = _try_auto_classify(db, user.id, data.description)
        if category:
            tx_status = "CLASSIFIED"
    elif data.type == "INCOME":
        tx_status = "CLASSIFIED"
        category = None  # Incomes don't have a budget category

    budget_id = None
    if category and data.type == "EXPENSE":
        budget_id = _find_budget(db, user.id, category, tx_date)

    tx = Transaction(
        account_id=data.account_id,
        type=data.type,
        status=tx_status,
        category=category,
        amount=data.amount,
        description=data.description,
        raw_description=data.description,
        rule_id=rule_id,
        budget_id=budget_id,
        transaction_date=tx_date,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    # Recalculate account balance
    recalculate_balance(db, data.account_id)

    return tx


def classify_transaction(
    db: Session, user: User, transaction_id: int, data: TransactionClassify
) -> Transaction:
    """
    Manually classify a pending transaction.
    """
    tx = (
        db.query(Transaction)
        .join(Account)
        .filter(Transaction.id == transaction_id, Account.user_id == user.id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    old_type = tx.type
    tx.category = data.category
    tx.status = "CLASSIFIED"

    if data.category == "DEPOSIT":
        tx.type = "NEUTRAL"
        tx.budget_id = None
    elif data.category == "TRANSFER":
        tx.type = "TRANSFER"
        tx.budget_id = None
    elif tx.type == "EXPENSE" and data.category in ("FIXED", "PERSONAL", "SAVINGS"):
        tx.budget_id = _find_budget(db, user.id, data.category, tx.transaction_date)

    db.commit()
    db.refresh(tx)

    # Recalculate balance if type changed (e.g. from EXPENSE to NEUTRAL/TRANSFER)
    if old_type != tx.type:
        recalculate_balance(db, tx.account_id)

    return tx


def reassign_transaction_account(db: Session, user: User, transaction_id: int, new_account_id: int) -> Transaction:
    """Reassign a transaction to another account belonging to the user and recalculate both balances."""
    tx = (
        db.query(Transaction)
        .join(Account)
        .filter(Transaction.id == transaction_id, Account.user_id == user.id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    new_acc = (
        db.query(Account)
        .filter(Account.id == new_account_id, Account.user_id == user.id)
        .first()
    )
    if not new_acc:
        raise HTTPException(status_code=404, detail="Cuenta de destino no encontrada")

    old_account_id = tx.account_id
    if old_account_id != new_account_id:
        tx.account_id = new_account_id
        db.commit()
        recalculate_balance(db, old_account_id)
        recalculate_balance(db, new_account_id)
        db.refresh(tx)

    return tx


def create_transfer(db: Session, user: User, data: TransferCreate) -> tuple[Transaction, Transaction]:
    """
    Create an internal transfer between two accounts.
    Creates two linked transactions. Budget impact = $0.
    """
    from_account = (
        db.query(Account)
        .filter(Account.id == data.from_account_id, Account.user_id == user.id)
        .first()
    )
    to_account = (
        db.query(Account)
        .filter(Account.id == data.to_account_id, Account.user_id == user.id)
        .first()
    )
    if not from_account or not to_account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    if from_account.id == to_account.id:
        raise HTTPException(status_code=400, detail="No puedes transferir a la misma cuenta")

    tx_date = data.transaction_date or date.today()

    # Outgoing transaction (debit from source)
    tx_out = Transaction(
        account_id=from_account.id,
        type="TRANSFER",
        status="TRANSFER",
        category="TRANSFER",
        amount=-data.amount,  # negative = outgoing
        description=f"{data.description} → {to_account.name}",
        raw_description=data.description,
        transaction_date=tx_date,
    )
    db.add(tx_out)
    db.flush()  # get the ID

    # Incoming transaction (credit to destination)
    tx_in = Transaction(
        account_id=to_account.id,
        type="TRANSFER",
        status="TRANSFER",
        category="TRANSFER",
        amount=data.amount,  # positive = incoming
        description=f"{data.description} ← {from_account.name}",
        raw_description=data.description,
        linked_transaction_id=tx_out.id,
        transaction_date=tx_date,
    )
    db.add(tx_in)
    db.flush()

    # Link them both ways
    tx_out.linked_transaction_id = tx_in.id

    db.commit()
    db.refresh(tx_out)
    db.refresh(tx_in)

    # Recalculate both balances
    recalculate_balance(db, from_account.id)
    recalculate_balance(db, to_account.id)

    return tx_out, tx_in


def get_transactions(
    db: Session,
    user_id: int,
    status_filter: str | None = None,
    category_filter: str | None = None,
    type_filter: str | None = None,
    account_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Transaction]:
    """Query transactions with optional filters, scoped to user."""
    query = (
        db.query(Transaction)
        .join(Account)
        .filter(Account.user_id == user_id)
    )
    if status_filter:
        query = query.filter(Transaction.status == status_filter)
    if category_filter:
        query = query.filter(Transaction.category == category_filter)
    if type_filter:
        query = query.filter(Transaction.type == type_filter)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    return (
        query
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_pending_transactions(db: Session, user_id: int) -> list[Transaction]:
    """Get all pending transactions for a user."""
    return get_transactions(db, user_id, status_filter="PENDING")


def get_transaction_count(db: Session, user_id: int, status_filter: str | None = None) -> int:
    """Count transactions, optionally filtered by status."""
    query = (
        db.query(Transaction)
        .join(Account)
        .filter(Account.user_id == user_id)
    )
    if status_filter:
        query = query.filter(Transaction.status == status_filter)
    return query.count()
