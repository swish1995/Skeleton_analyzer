"""스테이터스 위젯 모듈 (스켈레톤 + 각도 + 인체공학적 평가 + 캡처 스프레드시트)"""
from PyQt6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
import numpy as np
from datetime import datetime
from typing import Optional

from .skeleton_widget import SkeletonWidget
from .angle_widget import AngleWidget
from .ergonomic import ErgonomicWidget
from .capture_spreadsheet_widget import CaptureSpreadsheetWidget
from ..core.pose_detector import PoseDetector
from ..core.angle_calculator import AngleCalculator
from ..core.capture_model import CaptureRecord


class StatusWidget(QWidget):
    """스테이터스 위젯 (스켈레톤 + 각도 + 인체공학적 평가 + 캡처 스프레드시트)"""

    # 시그널
    capture_added = pyqtSignal(int)  # 캡처 추가 시 행 인덱스 전달
    visibility_changed = pyqtSignal(str, bool)  # 패널 가시성 변경 (패널명, 상태)

    def __init__(self):
        super().__init__()
        self._pose_detector = PoseDetector()
        self._angle_calculator = AngleCalculator()
        self._current_timestamp = 0.0
        self._current_frame_number = 0

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 상단: 패널 표시 체크박스 바
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(5, 2, 5, 2)
        checkbox_layout.setSpacing(15)

        checkbox_style = """
            QCheckBox {
                color: #cccccc;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
        """

        self._angle_checkbox = QCheckBox("각도")
        self._angle_checkbox.setChecked(True)
        self._angle_checkbox.setStyleSheet(checkbox_style)
        checkbox_layout.addWidget(self._angle_checkbox)

        self._ergonomic_checkbox = QCheckBox("안전지표")
        self._ergonomic_checkbox.setChecked(True)
        self._ergonomic_checkbox.setStyleSheet(checkbox_style)
        checkbox_layout.addWidget(self._ergonomic_checkbox)

        self._spreadsheet_checkbox = QCheckBox("스프레드시트")
        self._spreadsheet_checkbox.setChecked(True)
        self._spreadsheet_checkbox.setStyleSheet(checkbox_style)
        checkbox_layout.addWidget(self._spreadsheet_checkbox)

        checkbox_layout.addStretch()
        layout.addLayout(checkbox_layout)

        # 메인 스플리터 (상/하 분할)
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)

        # 상단: 스켈레톤 + 각도 (좌/우 분할)
        self._top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 왼쪽: 스켈레톤 시각화
        self._skeleton_widget = SkeletonWidget()
        self._top_splitter.addWidget(self._skeleton_widget)

        # 오른쪽: 각도 표시
        self._angle_widget = AngleWidget()
        self._top_splitter.addWidget(self._angle_widget)

        # 50:50 비율
        self._top_splitter.setSizes([400, 400])

        self._main_splitter.addWidget(self._top_splitter)

        # 중단: 인체공학적 평가 (RULA/REBA/OWAS)
        self._ergonomic_widget = ErgonomicWidget()
        self._main_splitter.addWidget(self._ergonomic_widget)

        # 하단: 캡처 스프레드시트
        self._spreadsheet_widget = CaptureSpreadsheetWidget()
        self._main_splitter.addWidget(self._spreadsheet_widget)

        # 상단:중단:하단 = 35:35:30 비율
        self._main_splitter.setSizes([350, 350, 300])

        layout.addWidget(self._main_splitter)

    def _connect_signals(self):
        """시그널 연결"""
        self._angle_checkbox.toggled.connect(self._on_angle_toggled)
        self._ergonomic_checkbox.toggled.connect(self._on_ergonomic_toggled)
        self._spreadsheet_checkbox.toggled.connect(self._on_spreadsheet_toggled)

    def _on_angle_toggled(self, checked: bool):
        """각도 패널 토글"""
        self._angle_widget.setVisible(checked)
        self.visibility_changed.emit('angle', checked)

    def _on_ergonomic_toggled(self, checked: bool):
        """안전지표 패널 토글"""
        self._ergonomic_widget.setVisible(checked)
        self.visibility_changed.emit('ergonomic', checked)

    def _on_spreadsheet_toggled(self, checked: bool):
        """스프레드시트 패널 토글"""
        self._spreadsheet_widget.setVisible(checked)
        self.visibility_changed.emit('spreadsheet', checked)

    # === 외부에서 패널 가시성 제어 ===

    def set_angle_visible(self, visible: bool):
        """각도 패널 가시성 설정"""
        self._angle_checkbox.setChecked(visible)

    def set_ergonomic_visible(self, visible: bool):
        """안전지표 패널 가시성 설정"""
        self._ergonomic_checkbox.setChecked(visible)

    def set_spreadsheet_visible(self, visible: bool):
        """스프레드시트 패널 가시성 설정"""
        self._spreadsheet_checkbox.setChecked(visible)

    def is_angle_visible(self) -> bool:
        """각도 패널 가시성 반환"""
        return self._angle_checkbox.isChecked()

    def is_ergonomic_visible(self) -> bool:
        """안전지표 패널 가시성 반환"""
        return self._ergonomic_checkbox.isChecked()

    def is_spreadsheet_visible(self) -> bool:
        """스프레드시트 패널 가시성 반환"""
        return self._spreadsheet_checkbox.isChecked()

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

            # 인체공학적 평가 업데이트
            self._ergonomic_widget.update_assessment(angles, result.landmarks)
        else:
            # 감지 안 됨
            self._skeleton_widget.clear()
            self._angle_widget.clear()
            self._ergonomic_widget.clear()

    def set_current_position(self, timestamp: float, frame_number: int):
        """현재 재생 위치 설정"""
        self._current_timestamp = timestamp
        self._current_frame_number = frame_number

    def capture_current_state(self) -> Optional[int]:
        """
        현재 상태를 캡처하여 스프레드시트에 추가

        Returns:
            추가된 행 인덱스 또는 None (결과 없을 시)
        """
        if not self._ergonomic_widget.has_results():
            return None

        results = self._ergonomic_widget.get_current_results()
        rula = results.get('rula')
        reba = results.get('reba')
        owas = results.get('owas')

        # CaptureRecord 생성
        record = CaptureRecord(
            timestamp=self._current_timestamp,
            frame_number=self._current_frame_number,
            capture_time=datetime.now(),
            # RULA
            rula_upper_arm=rula.upper_arm_score if rula else 0,
            rula_lower_arm=rula.lower_arm_score if rula else 0,
            rula_wrist=rula.wrist_score if rula else 0,
            rula_wrist_twist=rula.wrist_twist_score if rula else 0,
            rula_neck=rula.neck_score if rula else 0,
            rula_trunk=rula.trunk_score if rula else 0,
            rula_leg=rula.leg_score if rula else 0,
            rula_score_a=rula.arm_wrist_score if rula else 0,
            rula_score_b=rula.neck_trunk_score if rula else 0,
            rula_score=rula.final_score if rula else 0,
            rula_risk=rula.risk_level if rula else '',
            # REBA
            reba_neck=reba.neck_score if reba else 0,
            reba_trunk=reba.trunk_score if reba else 0,
            reba_leg=reba.leg_score if reba else 0,
            reba_upper_arm=reba.upper_arm_score if reba else 0,
            reba_lower_arm=reba.lower_arm_score if reba else 0,
            reba_wrist=reba.wrist_score if reba else 0,
            reba_score_a=reba.group_a_score if reba else 0,
            reba_score_b=reba.group_b_score if reba else 0,
            reba_score=reba.final_score if reba else 0,
            reba_risk=reba.risk_level if reba else '',
            # OWAS
            owas_back=owas.back_code if owas else 1,
            owas_arms=owas.arms_code if owas else 1,
            owas_legs=owas.legs_code if owas else 1,
            owas_load=owas.load_code if owas else 1,
            owas_code=owas.posture_code if owas else '1111',
            owas_ac=owas.action_category if owas else 1,
            owas_risk=owas.risk_level if owas else '',
        )

        # 스프레드시트에 추가
        row_idx = self._spreadsheet_widget.add_record(record)
        self.capture_added.emit(row_idx)
        return row_idx

    @property
    def spreadsheet_widget(self) -> CaptureSpreadsheetWidget:
        """스프레드시트 위젯 반환"""
        return self._spreadsheet_widget

    @property
    def ergonomic_widget(self) -> ErgonomicWidget:
        """인체공학적 평가 위젯 반환"""
        return self._ergonomic_widget

    def release(self):
        """리소스 해제"""
        self._pose_detector.release()
