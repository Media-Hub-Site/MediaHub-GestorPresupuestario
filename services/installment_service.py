"""
Installment service: CRUD operations, progress calculations, and summaries.
"""
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.models import Installment, Account, User
from schemas.schemas import InstallmentCreate, InstallmentUpdate, InstallmentSummary


def _enrich_installment(inst: Installment) -> dict:
    """Enrich installment model with calculated fields for response."""
    remaining_inst = max(0, inst.total_installments - inst.paid_installments)
    paid_amt = min(inst.total_amount, inst.paid_installments * inst.installment_amount)
    remaining_amt = max(0.0, inst.total_amount - paid_amt)
    pct = (inst.paid_installments / inst.total_installments * 100) if inst.total_installments > 0 else 100.0

    return {
        "id": inst.id,
        "user_id": inst.user_id,
        "account_id": inst.account_id,
        "account_name": inst.account.name if inst.account else None,
        "account_color": inst.account.color if inst.account else None,
        "description": inst.description,
        "total_amount": inst.total_amount,
        "installment_amount": inst.installment_amount,
        "total_installments": inst.total_installments,
        "paid_installments": inst.paid_installments,
        "remaining_installments": remaining_inst,
        "paid_amount": round(paid_amt, 2),
        "remaining_amount": round(remaining_amt, 2),
        "progress_pct": round(min(100.0, pct), 1),
        "start_date": inst.start_date,
        "category": inst.category,
        "status": inst.status,
        "created_at": inst.created_at,
        "updated_at": inst.updated_at,
    }


def create_installment(db: Session, user: User, data: InstallmentCreate) -> dict:
    """Create a new installment tracker."""
    # Check account if provided
    if data.account_id:
        acc = (
            db.query(Account)
            .filter(Account.id == data.account_id, Account.user_id == user.id)
            .first()
        )
        if not acc:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    # Calculate installment amount if omitted
    inst_amount = data.installment_amount
    if not inst_amount or inst_amount <= 0:
        inst_amount = round(data.total_amount / data.total_installments, 2)

    paid = min(data.paid_installments, data.total_installments)
    status_val = "COMPLETED" if paid >= data.total_installments else "ACTIVE"

    installment = Installment(
        user_id=user.id,
        account_id=data.account_id,
        description=data.description,
        total_amount=data.total_amount,
        installment_amount=inst_amount,
        total_installments=data.total_installments,
        paid_installments=paid,
        start_date=data.start_date or date.today(),
        category=data.category or "PERSONAL",
        status=status_val,
    )
    db.add(installment)
    db.commit()
    db.refresh(installment)
    return _enrich_installment(installment)


def get_installments(db: Session, user_id: int, status_filter: str | None = None) -> list[dict]:
    """List installments for a user."""
    query = db.query(Installment).filter(Installment.user_id == user_id)
    if status_filter:
        query = query.filter(Installment.status == status_filter.upper())
    installments = query.order_by(Installment.status.asc(), Installment.created_at.desc()).all()
    return [_enrich_installment(i) for i in installments]


def get_installment(db: Session, user_id: int, installment_id: int) -> dict:
    """Get single installment."""
    inst = (
        db.query(Installment)
        .filter(Installment.id == installment_id, Installment.user_id == user_id)
        .first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
    return _enrich_installment(inst)


def update_installment(db: Session, user_id: int, installment_id: int, data: InstallmentUpdate) -> dict:
    """Update an installment."""
    inst = (
        db.query(Installment)
        .filter(Installment.id == installment_id, Installment.user_id == user_id)
        .first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")

    if data.account_id is not None:
        if data.account_id > 0:
            acc = db.query(Account).filter(Account.id == data.account_id, Account.user_id == user_id).first()
            if not acc:
                raise HTTPException(status_code=404, detail="Cuenta no encontrada")
            inst.account_id = data.account_id
        else:
            inst.account_id = None

    if data.description is not None:
        inst.description = data.description
    if data.total_amount is not None:
        inst.total_amount = data.total_amount
    if data.total_installments is not None:
        inst.total_installments = data.total_installments
    if data.installment_amount is not None:
        inst.installment_amount = data.installment_amount
    elif data.total_amount is not None or data.total_installments is not None:
        inst.installment_amount = round(inst.total_amount / inst.total_installments, 2)

    if data.paid_installments is not None:
        inst.paid_installments = max(0, min(data.paid_installments, inst.total_installments))

    if data.start_date is not None:
        inst.start_date = data.start_date
    if data.category is not None:
        inst.category = data.category

    if data.status is not None:
        inst.status = data.status.upper()
    else:
        inst.status = "COMPLETED" if inst.paid_installments >= inst.total_installments else "ACTIVE"

    db.commit()
    db.refresh(inst)
    return _enrich_installment(inst)


def increment_installment(db: Session, user_id: int, installment_id: int) -> dict:
    """Convenience method to register 1 more paid installment."""
    inst = (
        db.query(Installment)
        .filter(Installment.id == installment_id, Installment.user_id == user_id)
        .first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")

    if inst.paid_installments < inst.total_installments:
        inst.paid_installments += 1
        if inst.paid_installments >= inst.total_installments:
            inst.status = "COMPLETED"
        db.commit()
        db.refresh(inst)

    return _enrich_installment(inst)


def delete_installment(db: Session, user_id: int, installment_id: int) -> None:
    """Delete an installment tracker."""
    inst = (
        db.query(Installment)
        .filter(Installment.id == installment_id, Installment.user_id == user_id)
        .first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
    db.delete(inst)
    db.commit()


def get_installment_summary(db: Session, user_id: int) -> InstallmentSummary:
    """Calculate aggregated stats for user installments."""
    items = db.query(Installment).filter(Installment.user_id == user_id).all()

    total_active_debt = 0.0
    total_paid_debt = 0.0
    monthly_commitment = 0.0
    active_count = 0
    completed_count = 0

    for item in items:
        paid_amt = min(item.total_amount, item.paid_installments * item.installment_amount)
        rem_amt = max(0.0, item.total_amount - paid_amt)
        total_paid_debt += paid_amt

        if item.status == "ACTIVE" and item.paid_installments < item.total_installments:
            total_active_debt += rem_amt
            monthly_commitment += item.installment_amount
            active_count += 1
        else:
            completed_count += 1

    return InstallmentSummary(
        total_active_debt=round(total_active_debt, 2),
        total_paid_debt=round(total_paid_debt, 2),
        monthly_commitment=round(monthly_commitment, 2),
        active_count=active_count,
        completed_count=completed_count,
    )
