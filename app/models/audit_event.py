from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from flask import current_app, has_request_context, request
from sqlalchemy import event, inspect
import jwt

from app.database.database import db


class AuditEvent(db.Model):
    __tablename__ = 'AuditEvent'

    idAuditEvent = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.String(64), nullable=False)
    action = db.Column(db.String(10), nullable=False)
    actor_user_id = db.Column(db.Integer)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    changes = db.Column(db.JSON, nullable=False)


_SENSITIVE_FIELDS = {'Contrasena'}


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return value


def serialize_record(instance):
    return {
        column.key: _json_value(getattr(instance, column.key))
        for column in inspect(instance).mapper.column_attrs
        if column.key not in _SENSITIVE_FIELDS
    }


def _snapshot(instance):
    return serialize_record(instance)


def _actor_user_id():
    if not has_request_context():
        return None
    payload = getattr(request, 'current_user', None)
    if payload:
        return payload.get('idUsuario')

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None

    try:
        payload = jwt.decode(
            auth_header.split(' ', 1)[1],
            current_app.config['SECRET_KEY'],
            algorithms=['HS256'],
        )
    except (jwt.InvalidTokenError, TypeError, ValueError):
        current_app.logger.warning('Could not attribute audit event to an invalid bearer token')
        return None
    return payload.get('idUsuario')


def _capture_changes(session, flush_context, instances):
    pending = []

    for instance in session.new:
        if isinstance(instance, AuditEvent):
            continue
        pending.append({
            'instance': instance,
            'entity_type': type(instance).__name__,
            'action': 'create',
            'actor_user_id': _actor_user_id(),
            'changes': {'after': _snapshot(instance)},
        })

    for instance in session.dirty:
        if isinstance(instance, AuditEvent) or not session.is_modified(instance, include_collections=False):
            continue

        changes = {}
        state = inspect(instance)
        for column in state.mapper.column_attrs:
            if column.key in _SENSITIVE_FIELDS:
                continue
            history = state.attrs[column.key].history
            if history.has_changes():
                before = history.deleted[0] if history.deleted else None
                after = history.added[0] if history.added else getattr(instance, column.key)
                changes[column.key] = {
                    'before': _json_value(before),
                    'after': _json_value(after),
                }
        if changes:
            pending.append({
                'instance': instance,
                'entity_type': type(instance).__name__,
                'action': 'update',
                'actor_user_id': _actor_user_id(),
                'changes': changes,
            })

    for instance in session.deleted:
        if isinstance(instance, AuditEvent):
            continue
        pending.append({
            'instance': instance,
            'entity_type': type(instance).__name__,
            'action': 'delete',
            'actor_user_id': _actor_user_id(),
            'changes': {'before': _snapshot(instance)},
        })

    if pending:
        session.info.setdefault('pending_audit_events', []).extend(pending)


def _write_changes(session, flush_context):
    pending = session.info.pop('pending_audit_events', [])
    for item in pending:
        identity = inspect(item['instance']).identity
        entity_id = ':'.join(str(value) for value in identity) if identity else 'unknown'
        session.add(AuditEvent(
            entity_type=item['entity_type'],
            entity_id=entity_id,
            action=item['action'],
            actor_user_id=item['actor_user_id'],
            changes=item['changes'],
        ))


def _clear_pending_changes(session):
    session.info.pop('pending_audit_events', None)


def register_audit_listeners():
    session_factory = db.session.session_factory
    if not event.contains(session_factory, 'before_flush', _capture_changes):
        event.listen(session_factory, 'before_flush', _capture_changes)
    if not event.contains(session_factory, 'after_flush_postexec', _write_changes):
        event.listen(session_factory, 'after_flush_postexec', _write_changes)
    if not event.contains(session_factory, 'after_rollback', _clear_pending_changes):
        event.listen(session_factory, 'after_rollback', _clear_pending_changes)
