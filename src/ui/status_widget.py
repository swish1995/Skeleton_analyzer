"""스테이터스 위젯 모듈 (스켈레톤 + 각도 + 인체공학적 평가 + 캡처 스프레드시트)"""
from PyQt6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
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

    # 토글 버튼 스타일 (ai-generate 스타일 - On 상태)
    TOGGLE_BUTTON_ON_STYLE = """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3a9a8a, stop:1 #2a8a7a);
            color: white;
            border: none;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4aaa9a, stop:1 #3a9a8a);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2a8a7a, stop:1 #1a7a6a);
        }
    """

    # 토글 버튼 스타일 (ai-generate 스타일 - Off 상태)
    TOGGLE_BUTTON_OFF_STYLE = """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #555555, stop:1 #444444);
            color: #999999;
            border: none;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #666666, stop:1 #555555);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #444444, stop:1 #333333);
        }
    """

    # 안전지표 서브 버튼 스타일 (On 상태)
    SUB_BUTTON_ON_STYLE = """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3a8a7a, stop:1 #2a7a6a);
            color: white;
            border: none;
            padding: 5px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4a9a8a, stop:1 #3a8a7a);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2a7a6a, stop:1 #1a6a5a);
        }
    """

    # 안전지표 서브 버튼 스타일 (Off 상태)
    SUB_BUTTON_OFF_STYLE = """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4a4a4a, stop:1 #3a3a3a);
            color: #888888;
            border: none;
            padding: 5px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5a5a5a, stop:1 #4a4a4a);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3a3a3a, stop:1 #2a2a2a);
        }
        QPushButton:disabled {
            background: #333333;
            color: #555555;
        }
    """

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 상단: 메뉴바 컨테이너 (왼쪽 메뉴바와 동일한 크기)
        menubar_container = QWidget()
        menubar_container.setStyleSheet("background-color: #333333; border-radius: 4px;")
        menubar_container.setFixedHeight(32)
        menubar_layout = QHBoxLayout(menubar_container)
        menubar_layout.setContentsMargins(8, 2, 8, 0)
        menubar_layout.setSpacing(4)

        # 상태 버튼 (토글) - 각도 패널
        self._angle_btn = QPushButton("상태: On")
        self._angle_btn.setFixedHeight(26)
        self._angle_btn.setCheckable(True)
        self._angle_btn.setChecked(True)
        self._update_toggle_style(self._angle_btn, True, "상태")
        menubar_layout.addWidget(self._angle_btn)

        # 데이터 버튼 (토글) - 스프레드시트
        self._spreadsheet_btn = QPushButton("데이터: On")
        self._spreadsheet_btn.setFixedHeight(26)
        self._spreadsheet_btn.setCheckable(True)
        self._spreadsheet_btn.setChecked(True)
        self._update_toggle_style(self._spreadsheet_btn, True, "데이터")
        menubar_layout.addWidget(self._spreadsheet_btn)

        # 구분선
        menubar_layout.addSpacing(8)

        # 안전지표 버튼 (토글)
        self._ergonomic_btn = QPushButton("안전지표: On")
        self._ergonomic_btn.setFixedHeight(26)
        self._ergonomic_btn.setCheckable(True)
        self._ergonomic_btn.setChecked(True)
        self._update_toggle_style(self._ergonomic_btn, True, "안전지표")
        menubar_layout.addWidget(self._ergonomic_btn)

        # RULA 버튼
        self._rula_btn = QPushButton("RULA")
        self._rula_btn.setFixedHeight(26)
        self._rula_btn.setCheckable(True)
        self._rula_btn.setChecked(True)
        self._update_sub_toggle_style(self._rula_btn, True)
        menubar_layout.addWidget(self._rula_btn)

        # REBA 버튼
        self._reba_btn = QPushButton("REBA")
        self._reba_btn.setFixedHeight(26)
        self._reba_btn.setCheckable(True)
        self._reba_btn.setChecked(True)
        self._update_sub_toggle_style(self._reba_btn, True)
        menubar_layout.addWidget(self._reba_btn)

        # OWAS 버튼
        self._owas_btn = QPushButton("OWAS")
        self._owas_btn.setFixedHeight(26)
        self._owas_btn.setCheckable(True)
        self._owas_btn.setChecked(True)
        self._update_sub_toggle_style(self._owas_btn, True)
        menubar_layout.addWidget(self._owas_btn)

        menubar_layout.addStretch()
        layout.addWidget(menubar_container)

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

    def _update_toggle_style(self, btn: QPushButton, checked: bool, label: str):
        """토글 버튼 스타일 업데이트 (On/Off 텍스트)"""
        if checked:
            btn.setText(f"{label}: On")
            btn.setStyleSheet(self.TOGGLE_BUTTON_ON_STYLE)
        else:
            btn.setText(f"{label}: Off")
            btn.setStyleSheet(self.TOGGLE_BUTTON_OFF_STYLE)

    def _update_sub_toggle_style(self, btn: QPushButton, checked: bool):
        """서브 토글 버튼 스타일 업데이트"""
        if checked:
            btn.setStyleSheet(self.SUB_BUTTON_ON_STYLE)
        else:
            btn.setStyleSheet(self.SUB_BUTTON_OFF_STYLE)

    def _connect_signals(self):
        """시그널 연결"""
        self._angle_btn.toggled.connect(self._on_angle_toggled)
        self._ergonomic_btn.toggled.connect(self._on_ergonomic_toggled)
        self._spreadsheet_btn.toggled.connect(self._on_spreadsheet_toggled)
        self._rula_btn.toggled.connect(self._on_rula_toggled)
        self._reba_btn.toggled.connect(self._on_reba_toggled)
        self._owas_btn.toggled.connect(self._on_owas_toggled)

    def _on_angle_toggled(self, checked: bool):
        """각도 패널 토글"""
        self._angle_widget.setVisible(checked)
        self._update_toggle_style(self._angle_btn, checked, "상태")
        self.visibility_changed.emit('angle', checked)

    def _on_ergonomic_toggled(self, checked: bool):
        """안전지표 패널 토글"""
        self._ergonomic_widget.setVisible(checked)
        self._update_toggle_style(self._ergonomic_btn, checked, "안전지표")
        # RULA/REBA/OWAS 버튼 활성/비활성
        self._rula_btn.setEnabled(checked)
        self._reba_btn.setEnabled(checked)
        self._owas_btn.setEnabled(checked)
        self.visibility_changed.emit('ergonomic', checked)

    def _on_spreadsheet_toggled(self, checked: bool):
        """스프레드시트 패널 토글"""
        self._spreadsheet_widget.setVisible(checked)
        self._update_toggle_style(self._spreadsheet_btn, checked, "데이터")
        self.visibility_changed.emit('spreadsheet', checked)

    def _on_rula_toggled(self, checked: bool):
        """RULA 패널 토글"""
        self._ergonomic_widget.set_rula_visible(checked)
        self._update_sub_toggle_style(self._rula_btn, checked)

    def _on_reba_toggled(self, checked: bool):
        """REBA 패널 토글"""
        self._ergonomic_widget.set_reba_visible(checked)
        self._update_sub_toggle_style(self._reba_btn, checked)

    def _on_owas_toggled(self, checked: bool):
        """OWAS 패널 토글"""
        self._ergonomic_widget.set_owas_visible(checked)
        self._update_sub_toggle_style(self._owas_btn, checked)

    # === 외부에서 패널 가시성 제어 ===

    def set_angle_visible(self, visible: bool):
        """각도 패널 가시성 설정"""
        self._angle_btn.setChecked(visible)

    def set_ergonomic_visible(self, visible: bool):
        """안전지표 패널 가시성 설정"""
        self._ergonomic_btn.setChecked(visible)

    def set_spreadsheet_visible(self, visible: bool):
        """스프레드시트 패널 가시성 설정"""
        self._spreadsheet_btn.setChecked(visible)

    def set_rula_visible(self, visible: bool):
        """RULA 패널 가시성 설정"""
        self._rula_btn.setChecked(visible)

    def set_reba_visible(self, visible: bool):
        """REBA 패널 가시성 설정"""
        self._reba_btn.setChecked(visible)

    def set_owas_visible(self, visible: bool):
        """OWAS 패널 가시성 설정"""
        self._owas_btn.setChecked(visible)

    def is_angle_visible(self) -> bool:
        """각도 패널 가시성 반환"""
        return self._angle_btn.isChecked()

    def is_ergonomic_visible(self) -> bool:
        """안전지표 패널 가시성 반환"""
        return self._ergonomic_btn.isChecked()

    def is_spreadsheet_visible(self) -> bool:
        """스프레드시트 패널 가시성 반환"""
        return self._spreadsheet_btn.isChecked()

    def is_rula_visible(self) -> bool:
        """RULA 패널 가시성 반환"""
        return self._rula_btn.isChecked()

    def is_reba_visible(self) -> bool:
        """REBA 패널 가시성 반환"""
        return self._reba_btn.isChecked()

    def is_owas_visible(self) -> bool:
        """OWAS 패널 가시성 반환"""
        return self._owas_btn.isChecked()

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
