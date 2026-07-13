import os
import json
import threading
import numpy as np
import dlib

DLIB_MODEL_DIR = os.getenv(
    'DLIB_MODEL_DIR',
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dat')
)
DLIB_MODELS = {
    'shape_predictor_68_face_landmarks.dat': {
        'url': 'https://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2',
        'sha256': None
    },
    'dlib_face_recognition_resnet_model_v1.dat': {
        'url': 'https://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2',
        'sha256': None
    }
}


def ensure_models_downloaded():
    """检查并自动下载dlib模型文件"""
    os.makedirs(DLIB_MODEL_DIR, exist_ok=True)
    missing = []
    for filename in DLIB_MODELS:
        filepath = os.path.join(DLIB_MODEL_DIR, filename)
        if not os.path.exists(filepath):
            missing.append(filename)
    if not missing:
        return
    try:
        import bz2
        from urllib.request import urlretrieve
    except ImportError:
        print('[WARN] 缺少bz2或urllib模块，无法自动下载dlib模型，请手动下载到 backend/dat/ 目录')
        return
    for filename in missing:
        model_info = DLIB_MODELS[filename]
        url = model_info['url']
        target_path = os.path.join(DLIB_MODEL_DIR, filename)
        print('[INFO] 正在下载dlib模型: {} ...'.format(filename))
        try:
            bz2_path = target_path + '.bz2'
            urlretrieve(url, bz2_path)
            with open(bz2_path, 'rb') as f_src:
                decompressed = bz2.decompress(f_src.read())
            with open(target_path, 'wb') as f_dst:
                f_dst.write(decompressed)
            os.remove(bz2_path)
            print('[INFO] 模型下载完成: {}'.format(filename))
        except Exception as e:
            print('[ERROR] 模型下载失败: {} - {}'.format(filename, str(e)))
            print('[INFO] 请手动从 {} 下载并解压到 {}'.format(url, DLIB_MODEL_DIR))
            if os.path.exists(bz2_path):
                os.remove(bz2_path)


class FaceRecognizer:
    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        with self._init_lock:
            if self._initialized:
                return
            ensure_models_downloaded()
            dat_dir = DLIB_MODEL_DIR
            predictor_path = os.path.join(dat_dir, 'shape_predictor_68_face_landmarks.dat')
            recognition_model_path = os.path.join(dat_dir, 'dlib_face_recognition_resnet_model_v1.dat')

            self.detector = dlib.get_frontal_face_detector()
            self.sp = dlib.shape_predictor(predictor_path)
            self.facerec = dlib.face_recognition_model_v1(recognition_model_path)
            self._dlib_lock = threading.Lock()
            self._initialized = True

    def _to_rgb(self, image):
        if isinstance(image, np.ndarray) and len(image.shape) == 3 and image.shape[2] == 3:
            return np.ascontiguousarray(image[:, :, ::-1])
        return image

    def detect_faces(self, image):
        rgb_image = self._to_rgb(image)
        with self._dlib_lock:
            dets = self.detector(rgb_image, 1)
        faces = []
        for d in dets:
            faces.append((d.left(), d.top(), d.right(), d.bottom()))
        return faces

    def detect_faces_rgb(self, rgb_image):
        with self._dlib_lock:
            dets = self.detector(rgb_image, 1)
        faces = []
        for d in dets:
            faces.append((d.left(), d.top(), d.right(), d.bottom()))
        return faces

    def compute_face_descriptor(self, image, face_rect):
        rgb_image = self._to_rgb(image)
        if isinstance(face_rect, tuple):
            rect = dlib.rectangle(face_rect[0], face_rect[1], face_rect[2], face_rect[3])
        else:
            rect = face_rect
        with self._dlib_lock:
            shape = self.sp(rgb_image, rect)
            descriptor = self.facerec.compute_face_descriptor(rgb_image, shape)
        return np.array(descriptor)

    def compute_face_descriptor_rgb(self, rgb_image, face_rect):
        if isinstance(face_rect, tuple):
            rect = dlib.rectangle(face_rect[0], face_rect[1], face_rect[2], face_rect[3])
        else:
            rect = face_rect
        with self._dlib_lock:
            shape = self.sp(rgb_image, rect)
            descriptor = self.facerec.compute_face_descriptor(rgb_image, shape)
        return np.array(descriptor)

    def compare_faces(self, face_descriptor, registered_descriptors, tolerance=0.4):
        if not registered_descriptors:
            return '陌生人', -1, float('inf')

        min_distance = float('inf')
        matched_name = '陌生人'
        matched_id = -1

        for reg in registered_descriptors:
            reg_descriptor = np.array(reg['face_descriptor'])
            distance = np.linalg.norm(face_descriptor - reg_descriptor)
            if distance < min_distance:
                min_distance = distance
                if distance < tolerance:
                    matched_name = reg.get('person_name', '陌生人')
                    matched_id = reg.get('id', -1)

        if min_distance >= tolerance:
            return '陌生人', -1, min_distance

        return matched_name, matched_id, min_distance


_cache_lock = threading.Lock()
_cache = {'faces': None, 'mtime': 0.0}


def load_registered_faces_from_file(faces_file):
    if not faces_file or not os.path.exists(faces_file):
        return []
    with open(faces_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_registered_faces():
    try:
        from flask import current_app
        faces_file = current_app.config.get('REGISTERED_FACES_FILE')
    except Exception:
        faces_file = None
    if not faces_file:
        faces_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'registered_faces.json')

    if not os.path.exists(faces_file):
        return []

    try:
        mtime = os.path.getmtime(faces_file)
    except OSError:
        mtime = 0.0

    with _cache_lock:
        if _cache['faces'] is not None and _cache['mtime'] == mtime:
            return _cache['faces']

    faces = load_registered_faces_from_file(faces_file)

    with _cache_lock:
        _cache['faces'] = faces
        _cache['mtime'] = mtime

    return faces
