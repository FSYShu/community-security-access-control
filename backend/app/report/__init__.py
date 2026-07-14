"""Security daily report API."""

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

from app.models.report import DailyReport
from app.report.service import (
    ReportAlreadyExists,
    ReportGenerationInProgress,
    delete_daily_report,
    generate_daily_report,
    validate_report_date,
)
from core.audit_logger import log_audit
from utils.permissions import admin_required
from utils.response import error_response, success_response


report_bp = Blueprint('report', __name__)


@report_bp.route('/list', methods=['GET'])
@jwt_required()
def get_report_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = DailyReport.query
    if start_date:
        query = query.filter(DailyReport.report_date >= start_date)
    if end_date:
        query = query.filter(DailyReport.report_date <= end_date)
    pagination = query.order_by(DailyReport.report_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return success_response(data={
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
    })


@report_bp.route('/workflow/status', methods=['GET'])
@admin_required
def get_workflow_status():
    provider = current_app.config.get('AI_REPORT_PROVIDER', 'siliconflow')
    ai_configured = (
        bool(current_app.config.get('SILICONFLOW_API_KEY', ''))
        if provider == 'siliconflow'
        else bool(current_app.config.get('AI_SERVICE_URL', ''))
    )
    return success_response(data={
        'auto_enabled': current_app.config.get('DAILY_REPORT_AUTO_ENABLED', True),
        'generate_time': current_app.config.get('DAILY_REPORT_GENERATE_TIME', '00:10'),
        'ai_enabled': current_app.config.get('AI_REPORT_ENABLED', True),
        'ai_provider': provider,
        'ai_configured': ai_configured,
        'ai_model': current_app.config.get(
            'SILICONFLOW_MODEL', 'Qwen/Qwen2.5-7B-Instruct'
        ),
        'ai_service_url': current_app.config.get(
            'SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1'
        ),
        'fallback_enabled': True,
    })


@report_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report_detail(report_id):
    report = DailyReport.query.get(report_id)
    if not report:
        return error_response(message='日报不存在', code=404)
    return success_response(data=report.to_dict())


@report_bp.route('/generate', methods=['POST'])
@admin_required
def generate_report():
    data = request.get_json(silent=True) or {}
    report_date = data.get('report_date', '')
    try:
        validate_report_date(report_date)
        report = generate_daily_report(report_date)
    except ValueError as exc:
        return error_response(message=str(exc), code=400)
    except ReportAlreadyExists:
        return error_response(
            message='该日期日报已存在，请使用重新生成', code=400
        )
    except ReportGenerationInProgress:
        return error_response(message='日报正在生成，请稍候', code=409, http_status=409)
    log_audit(
        operation_type='generate_report',
        operation_content='生成AI安防日报: {}'.format(report_date),
    )
    return success_response(data=report.to_dict(), message='AI安防日报生成成功')


@report_bp.route('/<int:report_id>/regenerate', methods=['POST'])
@admin_required
def regenerate_report(report_id):
    report = DailyReport.query.get(report_id)
    if not report:
        return error_response(message='日报不存在', code=404)
    try:
        report = generate_daily_report(report.report_date, replace=True)
    except ReportGenerationInProgress:
        return error_response(message='日报正在生成，请稍候', code=409, http_status=409)
    log_audit(
        operation_type='regenerate_report',
        operation_content='重新生成AI安防日报: {}'.format(report.report_date),
    )
    return success_response(data=report.to_dict(), message='AI安防日报重新生成成功')


@report_bp.route('/<int:report_id>', methods=['DELETE'])
@admin_required
def delete_report(report_id):
    try:
        report_date = delete_daily_report(report_id)
    except ReportGenerationInProgress:
        return error_response(message='日报正在生成，请稍候', code=409, http_status=409)

    if report_date is None:
        return error_response(message='日报不存在', code=404)

    log_audit(
        operation_type='delete_report',
        operation_content='删除AI安防日报: {}'.format(report_date),
    )
    return success_response(message='AI安防日报删除成功')


def _build_report(report_date):
    """Backward-compatible helper used by older callers."""
    return generate_daily_report(report_date)
