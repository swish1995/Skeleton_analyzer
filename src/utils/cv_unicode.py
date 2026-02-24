"""OpenCV 한글 경로 호환 유틸리티 (Windows)

Windows에서 OpenCV가 non-ASCII 경로를 처리하지 못하는 문제를 우회합니다.
macOS/Linux는 UTF-8 네이티브이므로 원본 함수를 그대로 사용합니다.

사용법:
    from src.utils.cv_unicode import imread, imwrite, VideoCapture
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

_IS_WINDOWS = sys.platform == 'win32'


def _has_non_ascii(path: str) -> bool:
    """경로에 non-ASCII 문자가 포함되어 있는지 확인"""
    try:
        path.encode('ascii')
        return False
    except UnicodeEncodeError:
        return True


def imread(path: str, flags: int = cv2.IMREAD_COLOR) -> Optional[np.ndarray]:
    """cv2.imread 한글 경로 호환 래퍼"""
    if _IS_WINDOWS and _has_non_ascii(path):
        buf = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(buf, flags)
    return cv2.imread(path, flags)


def imwrite(path: str, img: np.ndarray, params=None) -> bool:
    """cv2.imwrite 한글 경로 호환 래퍼"""
    if _IS_WINDOWS and _has_non_ascii(path):
        ext = Path(path).suffix or '.png'
        if params is None:
            result, buf = cv2.imencode(ext, img)
        else:
            result, buf = cv2.imencode(ext, img, params)
        if result:
            buf.tofile(path)
            return True
        return False
    if params is None:
        return cv2.imwrite(path, img)
    return cv2.imwrite(path, img, params)


class VideoCapture:
    """cv2.VideoCapture 한글 경로 호환 래퍼

    Windows에서 한글 경로인 경우 임시 심볼릭 링크로 우회합니다.
    심볼릭 링크 실패 시(권한 부족) 하드링크로 폴백합니다.
    """

    def __init__(self, path: str):
        self._temp_link: Optional[str] = None
        actual_path = path

        if _IS_WINDOWS and _has_non_ascii(path):
            link_path = self._create_temp_link(path)
            if link_path:
                actual_path = link_path

        self._cap = cv2.VideoCapture(actual_path)

    def _create_temp_link(self, path: str) -> Optional[str]:
        """임시 링크 생성 (symlink → hardlink 폴백)"""
        ext = Path(path).suffix
        link_name = f"sa_{uuid.uuid4().hex[:8]}{ext}"
        link_path = os.path.join(tempfile.gettempdir(), link_name)

        # 1) 심볼릭 링크 시도
        try:
            os.symlink(path, link_path)
            self._temp_link = link_path
            return link_path
        except OSError:
            pass

        # 2) 하드링크 폴백 (같은 볼륨, 관리자 권한 불필요)
        try:
            os.link(path, link_path)
            self._temp_link = link_path
            return link_path
        except OSError:
            return None

    def isOpened(self) -> bool:
        return self._cap.isOpened()

    def read(self):
        return self._cap.read()

    def get(self, prop_id: int):
        return self._cap.get(prop_id)

    def set(self, prop_id: int, value):
        return self._cap.set(prop_id, value)

    def release(self):
        self._cap.release()
        self._cleanup()

    def _cleanup(self):
        if self._temp_link:
            try:
                os.remove(self._temp_link)
            except OSError:
                pass
            self._temp_link = None

    def __del__(self):
        self._cleanup()
