from datetime import datetime, timedelta
from io import BytesIO
import json

from flask import Blueprint, request, send_file
from openpyxl import Workbook
from sqlalchemy import DateTime, func, or_

from app.database.database import db
from app.models.audit_event import AuditEvent, serialize_record
from app.models.cita import Cita
from app.models.comprobante import Comprobante
from app.models.detalle_reserva import Detalle_Reserva
from app.models.inventario import Inventario
from app.models.lote import Lote
from app.models.prenda import Prenda
from app.models.prenda_imagen import PrendaImagen
from app.models.reserva import Reserva
from app.models.usuarios import Usuarios
from app.utils.auth_middleware import admin_required
from app.utils.response import response_error

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reportes')

_EXCEL_MAX_DATA_ROWS = 1_048_575
_EXCEL_MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
_REPORT_MODELS = (
    Reserva,
    Comprobante,
    Cita,
    Inventario,
    Lote,
    Prenda,
    PrendaImagen,
    Usuarios,
)
_BUSINESS_DATE_FIELDS = {
    Reserva: ('fecha_reserva', 'fecha_evento', 'fecha_inicio', 'fecha_fin', 'fecha_devolucion'),
    Cita: ('fecha_cita',),
}


def _excel_safe(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def _date_bounds(column, start, end):
    if isinstance(column.type, DateTime):
        return start, end
    return start.date(), end.date()


def _matching_date_labels(instance, fields, start, end):
    labels = []
    for field in fields:
        value = getattr(instance, field, None)
        if value is None:
            continue
        lower_bound, upper_bound = (start, end) if isinstance(value, datetime) else (start.date(), end.date())
        if lower_bound <= value < upper_bound:
            formatted_value = value.isoformat(sep=' ') if isinstance(value, datetime) else value.isoformat()
            labels.append(f'{field}={formatted_value}')
    return '; '.join(labels)


def _current_period_records(start, end):
    for model in _REPORT_MODELS:
        date_fields = [
            field
            for field in ('created_at', 'updated_at', *_BUSINESS_DATE_FIELDS.get(model, ()))
            if hasattr(model, field)
        ]
        date_columns = [getattr(model, field) for field in date_fields]
        if not date_columns:
            continue

        date_filters = []
        for column in date_columns:
            lower_bound, upper_bound = _date_bounds(column, start, end)
            date_filters.append((column >= lower_bound) & (column < upper_bound))
        query = model.query.filter(or_(*date_filters)).order_by(*model.__mapper__.primary_key)

        for instance in query.yield_per(1000):
            yield instance, _matching_date_labels(instance, date_fields, start, end)

    reservation_date_fields = ('created_at', 'updated_at', *_BUSINESS_DATE_FIELDS[Reserva])
    reservation_filters = []
    for field in reservation_date_fields:
        column = getattr(Reserva, field)
        lower_bound, upper_bound = _date_bounds(column, start, end)
        reservation_filters.append((column >= lower_bound) & (column < upper_bound))
    details = (
        db.session.query(Detalle_Reserva, Reserva)
        .join(Reserva, Detalle_Reserva.idReserva == Reserva.idReserva)
        .filter(or_(*reservation_filters))
        .order_by(*Detalle_Reserva.__mapper__.primary_key)
        .yield_per(1000)
    )
    for detail, reservation in details:
        yield detail, f'Reserva: {_matching_date_labels(reservation, reservation_date_fields, start, end)}'


@reports_bp.route('/trimestral/excel', methods=['GET'])
@admin_required
def download_quarterly_report():
    year = request.args.get('year', type=int)
    quarter = request.args.get('quarter', type=int)
    if year is None or quarter is None:
        return response_error("Los parámetros 'year' y 'quarter' son requeridos", 400)
    if year < 1 or year > 9998:
        return response_error("'year' debe estar entre 1 y 9998", 400)
    if quarter not in (1, 2, 3, 4):
        return response_error("'quarter' debe estar entre 1 y 4", 400)

    start_month = (quarter - 1) * 3 + 1
    start = datetime(year, start_month, 1)
    if quarter == 4:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, start_month + 3, 1)
    period = (AuditEvent.occurred_at >= start, AuditEvent.occurred_at < end)

    event_count = AuditEvent.query.filter(*period).count()
    if event_count > _EXCEL_MAX_DATA_ROWS:
        return response_error(
            "El trimestre supera el máximo de filas que admite una hoja de Excel",
            413,
        )

    workbook = Workbook(write_only=True)
    summary_sheet = workbook.create_sheet('Resumen')
    summary_sheet.append(['Reporte trimestral', f'T{quarter} {year}'])
    summary_sheet.append(['Período UTC', f'{start:%Y-%m-%d} a {(end - timedelta(days=1)):%Y-%m-%d}'])
    summary_sheet.append(['Total de eventos registrados', event_count])
    summary_sheet.append([
        'Nota',
        'El historial detallado solo existe desde la instalación; los registros actuales usan fechas disponibles.',
    ])
    summary_sheet.append([])
    summary_sheet.append(['Tipo de registro', 'Acción', 'Cantidad'])

    grouped_counts = (
        db.session.query(AuditEvent.entity_type, AuditEvent.action, func.count(AuditEvent.idAuditEvent))
        .filter(*period)
        .group_by(AuditEvent.entity_type, AuditEvent.action)
        .order_by(AuditEvent.entity_type, AuditEvent.action)
        .all()
    )
    for entity_type, action, count in grouped_counts:
        summary_sheet.append([entity_type, action, count])

    history_sheet = workbook.create_sheet('Historial')
    history_sheet.append([
        'Fecha y hora UTC',
        'Tipo de registro',
        'ID del registro',
        'Acción',
        'ID del usuario responsable',
        'Cambios (JSON)',
    ])
    history_sheet.freeze_panes = 'A2'
    history_sheet.auto_filter.ref = f'A1:F{event_count + 1}'

    events = (
        AuditEvent.query.filter(*period)
        .order_by(AuditEvent.occurred_at, AuditEvent.idAuditEvent)
        .yield_per(1000)
    )
    for item in events:
        history_sheet.append([
            _excel_safe(item.occurred_at.isoformat(sep=' ')),
            _excel_safe(item.entity_type),
            _excel_safe(item.entity_id),
            _excel_safe(item.action),
            item.actor_user_id,
            _excel_safe(json.dumps(item.changes, ensure_ascii=False, sort_keys=True)),
        ])

    current_records_sheet = workbook.create_sheet('Registros actuales')
    current_records_sheet.append([
        'Tipo de registro',
        'ID del registro',
        'Fechas coincidentes UTC',
        'Estado actual (JSON; no reconstruye cambios pasados)',
    ])
    current_records_sheet.freeze_panes = 'A2'
    current_record_count = 0
    for instance, reference_at in _current_period_records(start, end):
        current_record_count += 1
        if current_record_count > _EXCEL_MAX_DATA_ROWS:
            return response_error(
                "El trimestre supera el máximo de filas que admite una hoja de Excel",
                413,
            )
        identity = type(instance).__mapper__.primary_key
        record_id = ':'.join(str(getattr(instance, column.key)) for column in identity)
        current_records_sheet.append([
            _excel_safe(type(instance).__name__),
            _excel_safe(record_id),
            _excel_safe(reference_at),
            _excel_safe(json.dumps(serialize_record(instance), ensure_ascii=False, sort_keys=True)),
        ])
    current_records_sheet.auto_filter.ref = f'A1:D{current_record_count + 1}'

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return send_file(
        output,
        mimetype=_EXCEL_MIMETYPE,
        as_attachment=True,
        download_name=f'reporte_trimestral_{year}_T{quarter}.xlsx',
    )
