"""
Categorization rule service: CRUD for auto-classification rules.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.models import CategorizationRule, User
from schemas.schemas import RuleCreate, RuleUpdate


def create_rule(db: Session, user: User, data: RuleCreate) -> CategorizationRule:
    """Create a new categorization rule."""
    rule = CategorizationRule(
        user_id=user.id,
        keyword=data.keyword.strip(),
        category=data.category.upper(),
        is_active=data.is_active,
        priority=data.priority,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_rules(db: Session, user_id: int) -> list[CategorizationRule]:
    """Get all rules for a user, ordered by priority (highest first)."""
    return (
        db.query(CategorizationRule)
        .filter(CategorizationRule.user_id == user_id)
        .order_by(CategorizationRule.priority.desc())
        .all()
    )


def update_rule(db: Session, user_id: int, rule_id: int, data: RuleUpdate) -> CategorizationRule:
    """Update an existing rule."""
    rule = (
        db.query(CategorizationRule)
        .filter(CategorizationRule.id == rule_id, CategorizationRule.user_id == user_id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")

    if data.keyword is not None:
        rule.keyword = data.keyword.strip()
    if data.category is not None:
        rule.category = data.category.upper()
    if data.is_active is not None:
        rule.is_active = data.is_active
    if data.priority is not None:
        rule.priority = data.priority
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, user_id: int, rule_id: int) -> None:
    """Delete a categorization rule."""
    rule = (
        db.query(CategorizationRule)
        .filter(CategorizationRule.id == rule_id, CategorizationRule.user_id == user_id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    db.delete(rule)
    db.commit()
