"""
Account service: CRUD operations and balance recalculation.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.models import Account, Transaction, User
from schemas.schemas import AccountCreate, AccountUpdate


def recalculate_balance(db: Session, account_id: int) -> float:
    """
    Recalculate the current_balance for an account based on its transactions.
    Formula: current_balance = initial_balance + SUM(incomes) - SUM(expenses)
    Transfers are treated as income (to) or expense (from) for balance purposes.
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return 0.0

    # Sum all INCOME / incoming transfers
    incomes = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.account_id == account_id,
            Transaction.type.in_(["INCOME"]),
        )
        .scalar()
    )

    # Sum incoming transfers (TRANSFER type where this account receives)
    # Exclude standalone transfers (category == "TRANSFER" but not an internal dual transfer)
    # Internal transfers are created with positive amount on destination and negative on source with linked_transaction_id
    incoming_transfers = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.account_id == account_id,
            Transaction.type == "TRANSFER",
            Transaction.category == "TRANSFER",
            Transaction.linked_transaction_id.isnot(None),
            Transaction.amount > 0,
        )
        .scalar()
    )

    # Sum all EXPENSE / outgoing transfers
    expenses = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.account_id == account_id,
            Transaction.type.in_(["EXPENSE"]),
        )
        .scalar()
    )

    # Sum outgoing transfers (linked internal transfers where amount < 0)
    outgoing_transfers = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.account_id == account_id,
            Transaction.type == "TRANSFER",
            Transaction.category == "TRANSFER",
            Transaction.linked_transaction_id.isnot(None),
            Transaction.amount < 0,
        )
        .scalar()
    )

    # Standalone transfers (e.g. categorized as TRANSFER from a bank debit/expense):
    # If a bank expense was classified as TRANSFER without linked_transaction_id,
    # it represents money that left the account (outflow).
    standalone_transfer_outflows = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.account_id == account_id,
            Transaction.type == "TRANSFER",
            Transaction.linked_transaction_id.is_(None),
        )
        .scalar()
    )

    new_balance = (
        account.initial_balance
        + float(incomes)
        + float(incoming_transfers)
        - float(expenses)
        + float(outgoing_transfers)  # outgoing_transfers is negative, so adding it subtracts
        - float(standalone_transfer_outflows) # standalone outgoing transfer reduces account balance
    )

    account.current_balance = new_balance
    db.commit()
    return new_balance


def create_account(db: Session, user: User, data: AccountCreate) -> Account:
    """Create a new account for a user."""
    account = Account(
        user_id=user.id,
        name=data.name,
        type=data.type,
        initial_balance=data.initial_balance,
        current_balance=data.initial_balance,  # starts at initial
        currency_code=data.currency_code or user.currency_code,
        icon=data.icon,
        color=data.color,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def get_accounts(db: Session, user_id: int) -> list[Account]:
    """Get all accounts for a user."""
    return db.query(Account).filter(Account.user_id == user_id).all()


def get_account(db: Session, user_id: int, account_id: int) -> Account:
    """Get a specific account by ID, scoped to user."""
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == user_id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada",
        )
    return account


def update_account(db: Session, user_id: int, account_id: int, data: AccountUpdate) -> Account:
    """Update an existing account."""
    account = get_account(db, user_id, account_id)
    if data.name is not None:
        account.name = data.name
    if data.type is not None:
        account.type = data.type
    if data.icon is not None:
        account.icon = data.icon
    if data.color is not None:
        account.color = data.color
    if data.initial_balance is not None:
        account.initial_balance = data.initial_balance
    db.commit()
    db.refresh(account)

    if data.initial_balance is not None:
        recalculate_balance(db, account_id)
        db.refresh(account)

    return account


def delete_account(db: Session, user_id: int, account_id: int) -> None:
    """Delete an account and all its transactions."""
    account = get_account(db, user_id, account_id)
    db.delete(account)
    db.commit()
