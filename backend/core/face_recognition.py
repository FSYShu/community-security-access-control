import os
import json
import threading
import numpy as np
import dlib


class FaceRecognizer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        dat_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dat')
        predictor_path = os.path.join(dat_dir, 'shape_predictor_68_face_landmarks.dat')
        recognition_model_path = os.path.join(dat_dir, 'dlib_face_recognition_resnet_model_v1.dat')

        self.detector = dlib.get_frontal_face_detector()
        self.sp = dlib.shape_predictor(predictor_path)
        self.facerec = dlib.face_recognition_model_v1(recognition_model_path)
        self._initialized = True

    def _to_rgb(self, image):
        if isinstance(image, np.ndarray) and len(image.shape) == 3 and image.shape[2] == 3:
            return np.ascontiguousarray(image[:, :, ::-1])
        return image

    def detect_faces(self, image):
        rgb_image = self._to_rgb(image)
        dets = self.detector(rgb_image, 1)
        faces = []
        for d in dets:
            faces.append((d.left(), d.top(), d.right(), d.bottom()))
        return faces

    def detect_faces_rgb(self, rgb_image):
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
        shape = self.sp(rgb_image, rect)
        descriptor = self.facerec.compute_face_descriptor(rgb_image, shape)
        return np.array(descriptor)

    def compute_face_descriptor_rgb(self, rgb_image, face_rect):
        if isinstance(face_rect, tuple):
            rect = dlib.rectangle(face_rect[0], face_rect[1], face_rect[2], face_rect[3])
        else:
            rect = face_rect
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
