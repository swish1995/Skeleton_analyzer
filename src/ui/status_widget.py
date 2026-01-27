"""스테이터스 위젯 모듈 (스켈레톤 + 각도)"""
from PyQt6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt
import numpy as np

from .skeleton_widget import SkeletonWidget
from .angle_widget import AngleWidget
from ..core.pose_detector import PoseDetector
from ..core.angle_calculator import AngleCalculator


class StatusWidget(QWidget):
    """스테이터스 위젯 (스켈레톤 시각화 + 각도 표시)"""

    def __init__(self):
        super().__init__()
        self._pose_detector = PoseDetector()
        self._angle_calculator = AngleCalculator()

        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 스플리터 (좌우 분할)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 왼쪽: 스켈레톤 시각화
        self._skeleton_widget = SkeletonWidget()
        splitter.addWidget(self._skeleton_widget)

        # 오른쪽: 각도 표시
        self._angle_widget = AngleWidget()
        splitter.addWidget(self._angle_widget)

        # 50:50 비율
        splitter.setSizes([400, 400])

        layout.addWidget(splitter)

    def process_frame(self, frame: np.ndarray):
        """프레임 처리"""
        # 포즈 감지
        result = self._pose_detector.detect(frame)

        if result.pose_detected and result.landmarks:
            # 스켈레톤 표시
            self._skeleton_widget.set_landmarks(result.landmarks)

            # 각도 계산 및 표시
            angles = self._angle_calculator.calculate_all_angles(result.landmarks)
            self._angle_widget.set_angles(angles)
        else:
            # 감지 안 됨
            self._skeleton_widget.clear()
            self._angle_widget.clear()

    def release(self):
        """리소스 해제"""
        self._pose_detector.release()
