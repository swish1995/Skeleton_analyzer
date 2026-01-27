"""REBA 결과 표시 위젯"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ...core.ergonomic.reba_calculator import REBAResult


class REBAWidget(QWidget):
    """REBA 평가 결과 표시 위젯"""

    # 색상 정의
    COLORS = {
        'negligible': '#4CAF50',    # 초록
        'low': '#8BC34A',           # 연두
        'medium': '#FFC107',        # 노랑
        'high': '#FF9800',          # 주황
        'very_high': '#F44336',     # 빨강
    }

    RISK_LABELS = {
        'negligible': '무시 가능',
        'low': '낮음',
        'medium': '중간',
        'high': '높음',
        'very_high': '매우 높음',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 상단: 최종 점수
        score_frame = QFrame()
        score_frame.setFrameShape(QFrame.Shape.StyledPanel)
        score_layout = QVBoxLayout(score_frame)

        self._score_label = QLabel("–")
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(48)
        font.setBold(True)
        self._score_label.setFont(font)

        self._risk_label = QLabel("대기 중")
        self._risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        risk_font = QFont()
        risk_font.setPointSize(14)
        self._risk_label.setFont(risk_font)

        score_layout.addWidget(self._score_label)
        score_layout.addWidget(self._risk_label)
        layout.addWidget(score_frame)

        # 중단: 그룹 점수
        group_box = QGroupBox("그룹 점수")
        group_layout = QHBoxLayout(group_box)

        # A그룹 (목/몸통/다리)
        a_group = QVBoxLayout()
        a_group.addWidget(QLabel("A그룹 (목/몸통/다리)"))
        self._a_score_label = QLabel("–")
        self._a_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        a_font = QFont()
        a_font.setPointSize(24)
        a_font.setBold(True)
        self._a_score_label.setFont(a_font)
        a_group.addWidget(self._a_score_label)
        group_layout.addLayout(a_group)

        # B그룹 (상지)
        b_group = QVBoxLayout()
        b_group.addWidget(QLabel("B그룹 (상지)"))
        self._b_score_label = QLabel("–")
        self._b_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._b_score_label.setFont(a_font)
        b_group.addWidget(self._b_score_label)
        group_layout.addLayout(b_group)

        layout.addWidget(group_box)

        # 하단: 상세 점수
        detail_box = QGroupBox("부위별 점수")
        detail_layout = QGridLayout(detail_box)

        # A그룹 상세
        detail_layout.addWidget(QLabel("목:"), 0, 0)
        self._neck_label = QLabel("–")
        detail_layout.addWidget(self._neck_label, 0, 1)

        detail_layout.addWidget(QLabel("몸통:"), 0, 2)
        self._trunk_label = QLabel("–")
        detail_layout.addWidget(self._trunk_label, 0, 3)

        detail_layout.addWidget(QLabel("다리:"), 1, 0)
        self._leg_label = QLabel("–")
        detail_layout.addWidget(self._leg_label, 1, 1)

        # B그룹 상세
        detail_layout.addWidget(QLabel("상완:"), 2, 0)
        self._upper_arm_label = QLabel("–")
        detail_layout.addWidget(self._upper_arm_label, 2, 1)

        detail_layout.addWidget(QLabel("전완:"), 2, 2)
        self._lower_arm_label = QLabel("–")
        detail_layout.addWidget(self._lower_arm_label, 2, 3)

        detail_layout.addWidget(QLabel("손목:"), 3, 0)
        self._wrist_label = QLabel("–")
        detail_layout.addWidget(self._wrist_label, 3, 1)

        layout.addWidget(detail_box)

        # 조치 권고
        self._action_label = QLabel("")
        self._action_label.setWordWrap(True)
        self._action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._action_label)

        layout.addStretch()

    def update_result(self, result: REBAResult):
        """결과 업데이트"""
        if result is None:
            self.clear()
            return

        # 최종 점수
        self._score_label.setText(str(result.final_score))
        color = self.COLORS.get(result.risk_level, '#888888')
        self._score_label.setStyleSheet(f"color: {color};")

        # 위험 수준
        risk_text = self.RISK_LABELS.get(result.risk_level, result.risk_level)
        self._risk_label.setText(risk_text)
        self._risk_label.setStyleSheet(f"color: {color};")

        # 그룹 점수
        self._a_score_label.setText(str(result.group_a_score))
        self._b_score_label.setText(str(result.group_b_score))

        # 상세 점수
        self._neck_label.setText(str(result.neck_score))
        self._trunk_label.setText(str(result.trunk_score))
        self._leg_label.setText(str(result.leg_score))
        self._upper_arm_label.setText(str(result.upper_arm_score))
        self._lower_arm_label.setText(str(result.lower_arm_score))
        self._wrist_label.setText(str(result.wrist_score))

        # 조치 권고
        self._action_label.setText(result.action_required)
        self._action_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def clear(self):
        """초기화"""
        self._score_label.setText("–")
        self._score_label.setStyleSheet("")
        self._risk_label.setText("대기 중")
        self._risk_label.setStyleSheet("")
        self._a_score_label.setText("–")
        self._b_score_label.setText("–")
        self._neck_label.setText("–")
        self._trunk_label.setText("–")
        self._leg_label.setText("–")
        self._upper_arm_label.setText("–")
        self._lower_arm_label.setText("–")
        self._wrist_label.setText("–")
        self._action_label.setText("")
