"""
文件加密解密工具
使用Fernet对称加密
"""
import os
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', '.secret_key')


def _get_or_create_key():
    """获取或创建加密密钥"""
    os.makedirs(os.path.dirname(_KEY_FILE), exist_ok=True)
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, 'rb') as f:
            return f.read()
    key = Fernet.generate_key()
    with open(_KEY_FILE, 'wb') as f:
        f.write(key)
    return key


def _get_fernet():
    return Fernet(_get_or_create_key())


def encrypt_file(input_path, output_path=None):
    """加密文件"""
    if output_path is None:
        output_path = input_path + '.enc'

    fernet = _get_fernet()
    with open(input_path, 'rb') as f:
        data = f.read()

    encrypted = fernet.encrypt(data)
    with open(output_path, 'wb') as f:
        f.write(encrypted)

    logger.info(f'File encrypted: {input_path} -> {output_path}')
    return output_path


def decrypt_file(input_path, output_path=None):
    """解密文件"""
    if output_path is None:
        if input_path.endswith('.enc'):
            output_path = input_path[:-4]
        else:
            output_path = input_path + '.dec'

    fernet = _get_fernet()
    with open(input_path, 'rb') as f:
        data = f.read()

    decrypted = fernet.decrypt(data)
    with open(output_path, 'wb') as f:
        f.write(decrypted)

    logger.info(f'File decrypted: {input_path} -> {output_path}')
    return output_path