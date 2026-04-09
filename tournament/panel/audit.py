"""Audit logging helpers — thin wrappers around AuditEntry creation."""

from ..models import AuditEntry


def log_audit(
    *,
    user,
    category,
    action,
    detail="",
    entity_type="",
    entity_id=None,
    entity_label="",
):
    """Create an AuditEntry. Call from views after key actions."""
    AuditEntry.objects.create(
        user=user if user and user.is_authenticated else None,
        category=category,
        action=action,
        detail=detail,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_label=entity_label,
    )
