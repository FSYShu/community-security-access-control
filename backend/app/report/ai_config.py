"""Runtime configuration helpers for the security report AI provider."""

import os

from dotenv import set_key


def _default_env_path():
    return os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', '..', '.env'
    ))


def validate_siliconflow_api_key(api_key):
    key = str(api_key or '').strip()
    if not key:
        raise ValueError('请输入硅基流动 API 密钥')
    if '\n' in key or '\r' in key or '\0' in key:
        raise ValueError('API 密钥格式不正确')
    if not key.startswith('sk-') or len(key) < 20:
        raise ValueError('请输入有效的硅基流动 API 密钥')
    return key


def save_siliconflow_api_key(app, api_key, env_path=None):
    """Persist the key without exposing it and apply it to the running app."""
    key = validate_siliconflow_api_key(api_key)
    target = os.path.abspath(env_path or _default_env_path())
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if not os.path.exists(target):
        with open(target, 'a', encoding='utf-8'):
            pass

    set_key(target, 'AI_REPORT_PROVIDER', 'siliconflow')
    set_key(target, 'SILICONFLOW_API_KEY', key)
    set_key(target, 'AI_REPORT_ENABLED', 'true')

    app.config.update(
        AI_REPORT_PROVIDER='siliconflow',
        SILICONFLOW_API_KEY=key,
        AI_REPORT_ENABLED=True,
    )
