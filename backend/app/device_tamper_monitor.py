"""Background camera tamper monitoring for gates with configured streams."""

import logging
import threading
import time

from app.models.gate import Gate
from core.fire_smoke_detector import FireSmokeDetector
from core.device_tamper import NORMAL, DeviceTamperDetector

from .video_monitor.device_tamper_stream import _open_capture, _placeholder, _record_alarm

logger = logging.getLogger(__name__)


class DeviceTamperMonitor:
    """Keep one tamper-detection worker running for every configured gate."""

    def __init__(self, app):
        self.app = app
        self.stop_event = threading.Event()
        self.workers = {}
        self.lock = threading.Lock()
        self.supervisor = None

    def start(self):
        if self.supervisor and self.supervisor.is_alive():
            return
        self.supervisor = threading.Thread(
            target=self._supervise,
            name='device-tamper-supervisor',
            daemon=True,
        )
        self.supervisor.start()
        logger.info('Background device tamper monitoring started')

    def stop(self):
        self.stop_event.set()
        with self.lock:
            for worker in self.workers.values():
                worker['stop_event'].set()

    def get_snapshot(self, gate_id):
        with self.lock:
            worker = self.workers.get(gate_id)
        if worker is None:
            return None
        with worker['state_lock']:
            frame = worker['frame']
            return {
                'frame': None if frame is None else frame.copy(),
                'status': worker['status'],
                'metrics': dict(worker['metrics']),
                'updated_at': worker['updated_at'],
            }

    def _supervise(self):
        refresh_interval = self.app.config.get('DEVICE_TAMPER_GATE_REFRESH_INTERVAL', 10)
        while not self.stop_event.is_set():
            try:
                self._sync_workers()
            except Exception:
                logger.exception('Failed to synchronize background tamper workers')
            self.stop_event.wait(refresh_interval)

    def _sync_workers(self):
        with self.app.app_context():
            gates = Gate.query.filter(Gate.push_key != '', Gate.push_key.isnot(None)).all()
            configured = {gate.id: gate.push_key for gate in gates}

        with self.lock:
            for gate_id, worker in list(self.workers.items()):
                if configured.get(gate_id) != worker['push_key']:
                    worker['stop_event'].set()
                    self.workers.pop(gate_id, None)

            for gate_id, push_key in configured.items():
                if gate_id in self.workers:
                    continue
                worker_stop = threading.Event()
                worker = {
                    'push_key': push_key,
                    'stop_event': worker_stop,
                    'state_lock': threading.Lock(),
                    'frame': None,
                    'status': 'stream_offline',
                    'metrics': {},
                    'updated_at': 0.0,
                }
                thread = threading.Thread(
                    target=self._monitor_gate,
                    args=(gate_id, push_key, worker_stop, worker),
                    name='device-tamper-gate-{}'.format(gate_id),
                    daemon=True,
                )
                worker['thread'] = thread
                self.workers[gate_id] = worker
                thread.start()

    def _monitor_gate(self, gate_id, push_key, worker_stop, worker):
        config = self.app.config
        stream_url = 'rtmp://{}:{}/live/{}'.format(
            config.get('RTMP_SERVER_HOST', '127.0.0.1'),
            config.get('RTMP_SERVER_PORT', 9090),
            push_key,
        )
        detector = DeviceTamperDetector(
            confirm_frames=config.get('DEVICE_TAMPER_CONFIRM_FRAMES', 3),
            blocked_confirm_frames=config.get('DEVICE_BLOCKED_CONFIRM_FRAMES', 8),
            recovery_frames=config.get('DEVICE_TAMPER_RECOVERY_FRAMES', 4),
            impact_confirm_frames=config.get('DEVICE_IMPACT_CONFIRM_FRAMES', 1),
            impact_motion_threshold=config.get('DEVICE_IMPACT_MOTION_THRESHOLD', 6.0),
            impact_coherence_threshold=config.get('DEVICE_IMPACT_COHERENCE_THRESHOLD', 0.6),
            impact_reversal_cosine=config.get('DEVICE_IMPACT_REVERSAL_COSINE', -0.35),
            impact_window_frames=config.get('DEVICE_IMPACT_WINDOW_FRAMES', 6),
            impact_blur_drop_threshold=config.get('DEVICE_IMPACT_BLUR_DROP_THRESHOLD', 0.35),
            impact_min_tracked_points=config.get('DEVICE_IMPACT_MIN_TRACKED_POINTS', 20),
            impact_scene_change_limit=config.get('DEVICE_IMPACT_SCENE_CHANGE_LIMIT', 0.60),
            impact_sudden_multiplier=config.get('DEVICE_IMPACT_SUDDEN_MULTIPLIER', 1.25),
        )
        emergency_detector = FireSmokeDetector(
            confirm_frames=config.get('FIRE_SMOKE_CONFIRM_FRAMES', 4),
            recovery_frames=config.get('FIRE_SMOKE_RECOVERY_FRAMES', 60),
            fire_recovery_frames=config.get('FIRE_RECOVERY_FRAMES', 10),
            fire_ratio_threshold=config.get('FIRE_RATIO_THRESHOLD', 0.006),
            smoke_ratio_threshold=config.get('SMOKE_RATIO_THRESHOLD', 0.10),
            warmup_frames=config.get('FIRE_SMOKE_WARMUP_FRAMES', 10),
            scene_change_ratio=config.get('FIRE_SMOKE_SCENE_CHANGE_RATIO', 0.35),
            static_fire_ratio_threshold=config.get('STATIC_FIRE_RATIO_THRESHOLD', 0.02),
        )
        open_timeout = config.get('DEVICE_STREAM_OPEN_TIMEOUT', 20)
        reconnect_interval = config.get('DEVICE_TAMPER_RECONNECT_INTERVAL', 2)
        check_interval = config.get('DEVICE_TAMPER_CHECK_INTERVAL', 0.1)
        alarm_cooldown = config.get('DEVICE_ALARM_COOLDOWN', 60)
        max_width = config.get('VIDEO_MAX_WIDTH', 640)
        placeholder = _placeholder('STREAM OFFLINE', (max_width, int(max_width * 9 / 16)))

        while not self.stop_event.is_set() and not worker_stop.is_set():
            cap = _open_capture(stream_url, timeout=open_timeout)
            if cap is None:
                self._update_worker_state(worker, placeholder, 'stream_offline', {})
                _record_alarm(self.app, gate_id, 'stream_offline', placeholder, {}, alarm_cooldown)
                worker_stop.wait(reconnect_interval)
                continue

            logger.info('Background tamper monitor connected for gate %s', gate_id)
            last_frame = placeholder
            last_check = 0.0
            result_status = NORMAL
            result_metrics = {}
            display_status = NORMAL
            display_metrics = {}
            try:
                while not self.stop_event.is_set() and not worker_stop.is_set():
                    ok, frame = cap.read()
                    if not ok or frame is None:
                        self._update_worker_state(worker, last_frame, 'stream_offline', {})
                        _record_alarm(
                            self.app, gate_id, 'stream_offline', last_frame, {}, alarm_cooldown
                        )
                        break

                    last_frame = frame
                    now = time.monotonic()
                    if now - last_check < check_interval:
                        self._update_worker_state(
                            worker, frame, display_status, display_metrics
                        )
                        continue

                    result = detector.analyze(frame)
                    emergency = emergency_detector.analyze(frame)
                    result_status = result.status
                    result_metrics = result.metrics
                    last_check = now
                    self._update_worker_state(worker, frame, result_status, result_metrics)
                    if result.event:
                        _record_alarm(
                            self.app,
                            gate_id,
                            result.status,
                            frame,
                            result.metrics,
                            alarm_cooldown,
                        )

                    display_status = result_status
                    if result_status == 'device_blocked':
                        display_status = result_status
                    elif emergency.fire:
                        display_status = 'open_flame'
                    elif emergency.smoke:
                        display_status = 'smoke'
                    display_metrics = {**result_metrics, **emergency.metrics}
                    self._update_worker_state(
                        worker,
                        frame,
                        display_status,
                        display_metrics,
                    )
                    if emergency.event:
                        if emergency.fire:
                            _record_alarm(
                                self.app, gate_id, 'open_flame', frame,
                                emergency.metrics, alarm_cooldown,
                            )
                        if emergency.smoke:
                            _record_alarm(
                                self.app, gate_id, 'smoke', frame,
                                emergency.metrics, alarm_cooldown,
                            )
            except Exception:
                logger.exception('Background tamper monitor failed for gate %s', gate_id)
                self._update_worker_state(worker, last_frame, 'stream_offline', {})
            finally:
                cap.release()

            worker_stop.wait(reconnect_interval)

        logger.info('Background tamper monitor stopped for gate %s', gate_id)

    @staticmethod
    def _update_worker_state(worker, frame, status, metrics):
        with worker['state_lock']:
            worker['frame'] = None if frame is None else frame.copy()
            worker['status'] = status
            worker['metrics'] = dict(metrics)
            worker['updated_at'] = time.monotonic()


def start_device_tamper_monitor(app):
    if not app.config.get('DEVICE_TAMPER_BACKGROUND_ENABLED', True):
        return None
    if app.config.get('TESTING'):
        return None

    monitor = app.extensions.get('device_tamper_monitor')
    if monitor is None:
        monitor = DeviceTamperMonitor(app)
        app.extensions['device_tamper_monitor'] = monitor
    monitor.start()
    return monitor
