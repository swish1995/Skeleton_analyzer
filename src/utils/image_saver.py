"""
이미지 저장 유틸리티

캡처된 프레임과 스켈레톤 이미지를 저장하는 유틸리티 클래스.
"""

import os
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import numpy as np
from PyQt6.QtGui import QPixmap

from src.utils.cv_unicode import imwrite as cv_imwrite

if TYPE_CHECKING:
    from utils.config import Config


class ImageSaver:
    """이미지 저장 유틸리티"""

    def __init__(self, base_dir: str = "captures", config: Optional["Config"] = None):
        """
        Args:
            base_dir: 캡처 이미지 저장 기본 디렉토리
            config: 설정 객체 (directories.capture_save 키 사용)
        """
        if config is not None:
            self._base_dir = config.get("directories.capture_save", base_dir)
        else:
            self._base_dir = base_dir

    def generate_filename(self, timestamp: float, prefix: str) -> str:
        """
        타임스탬프 기반 파일명 생성

        Args:
            timestamp: 동영상 타임스탬프 (초)
            prefix: 파일명 접두사 (예: "frame", "skeleton")

        Returns:
            형식: {prefix}_{MM}_{SS}_{ms}.png
        """
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        milliseconds = int((timestamp % 1) * 1000)
        return f"{prefix}_{minutes:02d}_{seconds:02d}_{milliseconds:03d}.png"

    def ensure_capture_directory(self, video_name: str) -> str:
        """
        캡처 디렉토리 생성

        Args:
            video_name: 동영상 이름 (확장자 제외)

        Returns:
            생성된 디렉토리 경로
        """
        dir_path = os.path.join(self._base_dir, video_name)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    def generate_unique_filename(self, dir_path: str, base_name: str) -> str:
        """
        충돌 없는 고유 파일명 생성

        기존 파일이 존재하면 _1, _2 등의 시퀀스 번호를 추가

        Args:
            dir_path: 디렉토리 경로
            base_name: 기본 파일명 (예: "frame_00_05_123.png")

        Returns:
            고유 파일명 (예: "frame_00_05_123_1.png")
        """
        name, ext = os.path.splitext(base_name)
        full_path = os.path.join(dir_path, base_name)

        if not os.path.exists(full_path):
            return base_name

        seq = 1
        while True:
            new_name = f"{name}_{seq}{ext}"
            new_path = os.path.join(dir_path, new_name)
            if not os.path.exists(new_path):
                return new_name
            seq += 1

    def save_frame(self, frame: np.ndarray, path: str) -> bool:
        """
        OpenCV 프레임을 PNG로 저장

        Args:
            frame: BGR 형식의 numpy 배열
            path: 저장 경로

        Returns:
            성공 여부
        """
        try:
            return cv_imwrite(path, frame)
        except Exception:
            return False

    def save_pixmap(self, pixmap: QPixmap, path: str) -> bool:
        """
        QPixmap을 PNG로 저장

        Args:
            pixmap: QPixmap 객체
            path: 저장 경로

        Returns:
            성공 여부
        """
        try:
            return pixmap.save(path, "PNG")
        except Exception:
            return False

    def save_capture(
        self,
        video_name: str,
        timestamp: float,
        frame: Optional[np.ndarray] = None,
        skeleton_pixmap: Optional[QPixmap] = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        프레임과 스켈레톤 이미지를 한번에 저장

        Args:
            video_name: 동영상 이름
            timestamp: 동영상 타임스탬프
            frame: BGR 프레임 (선택)
            skeleton_pixmap: 스켈레톤 QPixmap (선택)

        Returns:
            (프레임 경로, 스켈레톤 경로) 튜플. 저장 실패 시 None.
        """
        dir_path = self.ensure_capture_directory(video_name)

        frame_path = None
        skeleton_path = None

        if frame is not None:
            base_filename = self.generate_filename(timestamp, "frame")
            filename = self.generate_unique_filename(dir_path, base_filename)
            path = os.path.join(dir_path, filename)
            if self.save_frame(frame, path):
                frame_path = path

        if skeleton_pixmap is not None:
            base_filename = self.generate_filename(timestamp, "skeleton")
            filename = self.generate_unique_filename(dir_path, base_filename)
            path = os.path.join(dir_path, filename)
            if self.save_pixmap(skeleton_pixmap, path):
                skeleton_path = path

        return frame_path, skeleton_path
