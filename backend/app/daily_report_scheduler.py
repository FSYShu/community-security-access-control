"""Background scheduler that generates the previous day's security report."""

import logging
import threading
from datetime import datetime, timedelta, timezone

from app.models.report import DailyReport
from app.report.service import generate_daily_report


logger = logging.getLogger(__name__)
_CST = timezone(timedelta(hours=8))


class DailyReportScheduler:
    def __init__(self, app):
        self.app = app
        self.stop_event = threading.Event()
        self.thread = threading.Thread(
            target=self._run,
            name='security-daily-report-scheduler',
            daemon=True,
        )

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.stop_event.set()

    def _run(self):
        interval = self.app.config.get('DAILY_REPORT_CHECK_INTERVAL', 60)
        while not self.stop_event.is_set():
            try:
                self.run_if_due()
            except Exception:
                logger.exception('Automatic security daily report failed')
            self.stop_event.wait(interval)

    def run_if_due(self, now=None):
        now = now or datetime.now(_CST)
        hour, minute = _parse_generate_time(
            self.app.config.get('DAILY_REPORT_GENERATE_TIME', '00:10')
        )
        if (now.hour, now.minute) < (hour, minute):
            return None
        report_date = (now.date() - timedelta(days=1)).isoformat()
        with self.app.app_context():
            existing = DailyReport.query.filter_by(report_date=report_date).first()
            if existing is not None:
                return existing.to_dict()
            report = generate_daily_report(report_date)
            logger.info('Automatic security report generated for %s', report_date)
            return report.to_dict()


def start_daily_report_scheduler(app):
    if app.config.get('TESTING') or not app.config.get('DAILY_REPORT_AUTO_ENABLED', True):
        return None
    existing = app.extensions.get('daily_report_scheduler')
    if existing is not None:
        return existing
    scheduler = DailyReportScheduler(app).start()
    app.extensions['daily_report_scheduler'] = scheduler
    logger.info(
        'Security daily report scheduler started, generate time=%s',
        app.config.get('DAILY_REPORT_GENERATE_TIME', '00:10'),
    )
    return scheduler


def _parse_generate_time(value):
    try:
        hour_text, minute_text = value.split(':', 1)
        hour, minute = int(hour_text), int(minute_text)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
    except (AttributeError, TypeError, ValueError):
        pass
    logger.warning('Invalid DAILY_REPORT_GENERATE_TIME=%r, using 00:10', value)
    return 0, 10
