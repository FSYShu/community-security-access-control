"""Security daily report analysis and optional AI text generation."""

import json
import logging
from datetime import datetime
from urllib import request as urlrequest


logger = logging.getLogger(__name__)

ALARM_TYPE_LABELS = {
    'device_blocked': '摄像头遮挡',
    'device_blurred': '画面模糊',
    'device_moved': '设备移动',
    'camera_impact': '设备拍打',
    'open_flame': '明火',
    'smoke': '烟雾',
    'tailgating': '贴身尾随',
    'stream_offline': '视频断流',
    'danger_zone_intrusion': '危险区域入侵',
}


class SecurityReportWorkflow:
    """Collect statistics, assess risk, then generate readable report text."""

    def __init__(self, ai_service_url='', ai_enabled=True, ai_timeout=60.0,
                 ai_endpoint='/chat/completions', ai_provider='siliconflow',
                 ai_model='Qwen/Qwen2.5-7B-Instruct', ai_api_key=''):
        self.ai_service_url = (ai_service_url or '').rstrip('/')
        self.ai_timeout = ai_timeout
        self.ai_endpoint = ai_endpoint
        self.ai_provider = ai_provider
        self.ai_model = ai_model
        self.ai_api_key = ai_api_key
        self.ai_enabled = bool(
            ai_enabled
            and self.ai_service_url
            and (self.ai_provider != 'siliconflow' or self.ai_api_key)
        )

    def run(self, report_date, pass_records, alarms, gates):
        gate_map = {gate.id: gate for gate in gates}
        pass_stats = self._build_pass_stats(pass_records, gate_map)
        alarm_stats = self._build_alarm_stats(alarms, gate_map)
        risk_level, risk_score = self._assess_risk(pass_stats, alarm_stats)
        fallback = {
            'summary': self._build_summary(
                report_date, pass_stats, alarm_stats, risk_level
            ),
            'recommendations': self._build_recommendations(
                pass_stats, alarm_stats
            ),
        }

        generated = self._call_ai(
            report_date,
            pass_stats,
            alarm_stats,
            fallback,
            risk_level,
            risk_score,
        )
        source = self.ai_provider if generated else 'local_rules'
        content = generated or fallback
        return {
            'pass_stats': pass_stats,
            'alarm_stats': alarm_stats,
            'abnormal_events': [
                alarm.to_dict() for alarm in alarms
                if alarm.alarm_level == 'critical'
            ],
            'ai_summary': content['summary'],
            'risk_level': risk_level,
            'risk_score': risk_score,
            'recommendations': content['recommendations'],
            'workflow_source': source,
        }

    @staticmethod
    def _build_pass_stats(records, gate_map):
        pass_count = sum(record.pass_result == 'pass' for record in records)
        reject_count = sum(record.pass_result == 'reject' for record in records)
        gate_distribution = {}
        level_distribution = {}
        reject_reasons = {}
        hourly_distribution = {}

        for record in records:
            gate = gate_map.get(record.gate_id)
            gate_name = gate.gate_name if gate else '门禁{}'.format(record.gate_id)
            gate_level = gate.gate_level if gate else 'unknown'
            gate_item = gate_distribution.setdefault(
                gate_name, {'pass': 0, 'reject': 0}
            )
            level_item = level_distribution.setdefault(
                gate_level, {'pass': 0, 'reject': 0}
            )
            key = 'pass' if record.pass_result == 'pass' else 'reject'
            gate_item[key] += 1
            level_item[key] += 1

            hour = _extract_hour(record.pass_time)
            if hour is not None:
                hour_key = '{:02d}:00'.format(hour)
                hourly_distribution[hour_key] = hourly_distribution.get(hour_key, 0) + 1
            if record.pass_result == 'reject':
                reason = record.reject_reason or '未说明原因'
                reject_reasons[reason] = reject_reasons.get(reason, 0) + 1

        total = len(records)
        return {
            'total': total,
            'pass_count': pass_count,
            'reject_count': reject_count,
            'reject_rate': round(reject_count * 100 / total, 1) if total else 0.0,
            'level_distribution': level_distribution,
            'gate_distribution': gate_distribution,
            'reject_reasons': reject_reasons,
            'hourly_distribution': hourly_distribution,
        }

    @staticmethod
    def _build_alarm_stats(alarms, gate_map):
        type_distribution = {}
        level_distribution = {}
        gate_distribution = {}
        pending_count = 0
        handled_count = 0

        for alarm in alarms:
            type_distribution[alarm.alarm_type] = (
                type_distribution.get(alarm.alarm_type, 0) + 1
            )
            level_distribution[alarm.alarm_level] = (
                level_distribution.get(alarm.alarm_level, 0) + 1
            )
            if alarm.handle_status == 'handled':
                handled_count += 1
            else:
                pending_count += 1
            if alarm.source_type == 'gate':
                gate = gate_map.get(alarm.source_id)
                gate_name = gate.gate_name if gate else '门禁{}'.format(alarm.source_id)
                gate_distribution[gate_name] = gate_distribution.get(gate_name, 0) + 1

        return {
            'total': len(alarms),
            'pending_count': pending_count,
            'handled_count': handled_count,
            'critical_count': level_distribution.get('critical', 0),
            'type_distribution': type_distribution,
            'level_distribution': level_distribution,
            'gate_distribution': gate_distribution,
        }

    @staticmethod
    def _assess_risk(pass_stats, alarm_stats):
        emergency_count = sum(
            alarm_stats['type_distribution'].get(item, 0)
            for item in ('open_flame', 'smoke')
        )
        score = min(100, (
            alarm_stats['critical_count'] * 12
            + alarm_stats['pending_count'] * 5
            + min(pass_stats['reject_count'], 10) * 2
            + emergency_count * 15
        ))
        if emergency_count or score >= 60:
            return 'high', score
        if alarm_stats['critical_count'] or alarm_stats['pending_count'] or score >= 20:
            return 'medium', score
        return 'low', score

    @staticmethod
    def _build_summary(report_date, pass_stats, alarm_stats, risk_level):
        risk_label = {'low': '低', 'medium': '中', 'high': '高'}[risk_level]
        type_items = sorted(
            alarm_stats['type_distribution'].items(),
            key=lambda item: item[1],
            reverse=True,
        )
        if type_items:
            top_types = '、'.join(
                '{}{}次'.format(ALARM_TYPE_LABELS.get(name, name), count)
                for name, count in type_items[:3]
            )
            alarm_text = '主要告警为{}。'.format(top_types)
        else:
            alarm_text = '当天没有记录到安全告警。'
        return (
            '{}共记录通行{}次，其中放行{}次、拒绝{}次；产生告警{}条，'
            '仍有{}条待处理。{}综合风险等级为{}。'
        ).format(
            report_date,
            pass_stats['total'],
            pass_stats['pass_count'],
            pass_stats['reject_count'],
            alarm_stats['total'],
            alarm_stats['pending_count'],
            alarm_text,
            risk_label,
        )

    @staticmethod
    def _build_recommendations(pass_stats, alarm_stats):
        recommendations = []
        types = alarm_stats['type_distribution']
        if alarm_stats['pending_count']:
            recommendations.append('优先处理仍处于待处理状态的告警，并填写处置结果。')
        if types.get('open_flame') or types.get('smoke'):
            recommendations.append('复核明火烟雾截图和视频，必要时安排现场巡查。')
        if any(types.get(item) for item in (
                'device_blocked', 'camera_impact', 'device_moved', 'stream_offline')):
            recommendations.append('检查门禁摄像头供电、网络、安装角度和镜头状态。')
        if types.get('tailgating'):
            recommendations.append('复核尾随告警时段的通行记录和监控视频。')
        if pass_stats['reject_count']:
            recommendations.append('核对被拒绝通行人员及拒绝原因，排查异常尝试。')
        if not recommendations:
            recommendations.append('当天未发现明显风险，继续保持日常巡检。')
        return recommendations

    def _call_ai(self, report_date, pass_stats, alarm_stats, fallback,
                 risk_level, risk_score):
        if not self.ai_enabled:
            return None
        if self.ai_provider == 'siliconflow':
            return self._call_siliconflow(
                report_date,
                pass_stats,
                alarm_stats,
                risk_level,
                risk_score,
                fallback,
            )
        return self._call_custom_ai(report_date, pass_stats, alarm_stats, fallback)

    def _call_siliconflow(self, report_date, pass_stats, alarm_stats,
                          risk_level, risk_score, fallback):
        statistics = {
            'report_date': report_date,
            'pass_stats': pass_stats,
            'alarm_stats': alarm_stats,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'alarm_type_labels': ALARM_TYPE_LABELS,
            'allowed_recommendations': fallback['recommendations'],
        }
        payload = {
            'model': self.ai_model,
            'stream': False,
            'temperature': 0,
            'max_tokens': 512,
            'response_format': {'type': 'json_object'},
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        '你是社区安防日报助手。请根据统计数据生成简短、客观的中文日报。'
                        '只输出JSON，格式为{"recommendations":["建议1","建议2"]}。'
                        '只能简化或改写allowed_recommendations，不得增加新的事件、地点、设备或处置动作。'
                        '建议不超过3条，不要编造设备、人员或事件。'
                        '告警类型必须使用alarm_type_labels中的中文名称。'
                        '不要改变系统给出的风险等级和风险分数。'
                    ),
                },
                {
                    'role': 'user',
                    'content': json.dumps(statistics, ensure_ascii=False),
                },
            ],
        }
        try:
            result = self._post_json(payload)
            choices = result.get('choices', [])
            content = (
                choices[0].get('message', {}).get('content', '')
                if choices else ''
            )
            data = _parse_json_content(content)
            recommendations = data.get('recommendations', [])
            if not isinstance(recommendations, list) or not recommendations:
                return None
            return {
                'summary': fallback['summary'],
                'recommendations': [
                    str(item).strip() for item in recommendations[:3]
                    if str(item).strip()
                ],
            }
        except Exception as exc:
            logger.info('SiliconFlow unavailable, using local rules: %s', exc)
            return None

    def _call_custom_ai(self, report_date, pass_stats, alarm_stats, fallback):
        payload = {
            'task': 'security_daily_report',
            'language': 'zh-CN',
            'report_date': report_date,
            'statistics': {
                'pass': pass_stats,
                'alarm': alarm_stats,
            },
            'fallback_draft': fallback,
            'output_schema': {
                'summary': 'string',
                'recommendations': ['string'],
            },
        }
        try:
            result = self._post_json(payload)
            data = result.get('data', result)
            return _validate_ai_content(data)
        except Exception as exc:
            logger.info('AI report service unavailable, using local rules: %s', exc)
        return None

    def _post_json(self, payload):
        headers = {'Content-Type': 'application/json'}
        if self.ai_api_key:
            headers['Authorization'] = 'Bearer {}'.format(self.ai_api_key)
        req = urlrequest.Request(
            self.ai_service_url + self.ai_endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            method='POST',
        )
        with urlrequest.urlopen(req, timeout=self.ai_timeout) as response:
            return json.loads(response.read().decode('utf-8'))


def _extract_hour(value):
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).hour
    except (ValueError, TypeError, AttributeError):
        return None


def _parse_json_content(content):
    text = str(content or '').strip()
    if text.startswith('```'):
        lines = text.splitlines()
        text = '\n'.join(lines[1:-1]).strip()
    return json.loads(text)


def _validate_ai_content(data):
    if not isinstance(data, dict):
        return None
    summary = str(data.get('summary', '')).strip()
    recommendations = data.get('recommendations', [])
    if not summary or not isinstance(recommendations, list):
        return None
    return {
        'summary': summary,
        'recommendations': [str(item).strip() for item in recommendations if str(item).strip()],
    }
