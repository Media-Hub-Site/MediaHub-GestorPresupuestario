"""
Budget service: CRUD and consumption metrics.
"""
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from models.models import Budget, Transaction, Account, User
from schemas.schemas import BudgetCreate, BudgetUpdate, BudgetSummary


def create_budget(db: Session, user: User, data: BudgetCreate) -> Budget:
    """Create or update a budget for a category/month/year."""
    # Check if one already exists for this slot
    existing = (
        db.query(Budget)
        .filter(
            Budget.user_id == user.id,
            Budget.category == data.category,
            Budget.year == data.year,
            Budget.month == data.month,
        )
        .first()
    )
    if existing:
        existing.monthly_limit = data.monthly_limit
        if data.annual_limit is not None:
            existing.annual_limit = data.annual_limit
        db.commit()
        db.refresh(existing)
        return existing

    budget = Budget(
        user_id=user.id,
        category=data.category,
        monthly_limit=data.monthly_limit,
        annual_limit=data.annual_limit,
        year=data.year,
        month=data.month,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def get_budgets(db: Session, user_id: int, year: int | None = None, month: int | None = None) -> list[Budget]:
    """Get budgets, optionally filtered by year/month."""
    query = db.query(Budget).filter(Budget.user_id == user_id)
    if year:
        query = query.filter(Budget.year == year)
    if month:
        query = query.filter(Budget.month == month)
    return query.order_by(Budget.year.desc(), Budget.month.desc()).all()


def update_budget(db: Session, user_id: int, budget_id: int, data: BudgetUpdate) -> Budget:
    """Update budget limits."""
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.user_id == user_id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

    if data.monthly_limit is not None:
        budget.monthly_limit = data.monthly_limit
    if data.annual_limit is not None:
        budget.annual_limit = data.annual_limit
    db.commit()
    db.refresh(budget)
    return budget


def _get_spent(db: Session, user_id: int, category: str, year: int, month: int | None = None) -> float:
    """Calculate total spent for a category in a given period."""
    query = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .join(Account)
        .filter(
            Account.user_id == user_id,
            Transaction.type == "EXPENSE",
            Transaction.category == category,
            Transaction.status == "CLASSIFIED",
            extract("year", Transaction.transaction_date) == year,
        )
    )
    if month is not None:
        query = query.filter(extract("month", Transaction.transaction_date) == month)
    return float(query.scalar())


def get_budget_summary(db: Session, user_id: int, year: int, month: int) -> list[BudgetSummary]:
    """Get budget consumption summaries for a given month."""
    budgets = get_budgets(db, user_id, year=year, month=month)

    summaries = []
    for budget in budgets:
        spent_month = _get_spent(db, user_id, budget.category, year, month)
        spent_year = _get_spent(db, user_id, budget.category, year)

        month_pct = (spent_month / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0
        year_pct = None
        if budget.annual_limit and budget.annual_limit > 0:
            year_pct = spent_year / budget.annual_limit * 100

        summaries.append(BudgetSummary(
            category=budget.category,
            monthly_limit=budget.monthly_limit,
            annual_limit=budget.annual_limit,
            spent_this_month=spent_month,
            spent_this_year=spent_year,
            month_progress_pct=round(month_pct, 1),
            year_progress_pct=round(year_pct, 1) if year_pct is not None else None,
        ))

    return summaries
