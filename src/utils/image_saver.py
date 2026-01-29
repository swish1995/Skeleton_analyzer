"""
이미지 저장 유틸리티

캡처된 프레임과 스켈레톤 이미지를 저장하는 유틸리티 클래스.
"""

import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtGui import QPixmap


class ImageSaver:
    """이미지 저장 유틸리티"""

    def __init__(self, base_dir: str = "captures"):
        """
        Args:
            base_dir: 캡처 이미지 저장 기본 디렉토리
        """
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
            return cv2.imwrite(path, frame)
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
            filename = self.generate_filename(timestamp, "frame")
            path = os.path.join(dir_path, filename)
            if self.save_frame(frame, path):
                frame_path = path

        if skeleton_pixmap is not None:
            filename = self.generate_filename(timestamp, "skeleton")
            path = os.path.join(dir_path, filename)
            if self.save_pixmap(skeleton_pixmap, path):
                skeleton_path = path

        return frame_path, skeleton_path
