"""인체공학적 평가 통합 위젯"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt
from typing import Dict, List

from ...core.ergonomic import (
    RULACalculator, RULAResult,
    REBACalculator, REBAResult,
    OWASCalculator, OWASResult,
)
from .rula_widget import RULAWidget
from .reba_widget import REBAWidget
from .owas_widget import OWASWidget


class ErgonomicWidget(QWidget):
    """인체공학적 평가 통합 위젯 (체크박스 + 가로 3분할)"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 계산기 초기화
        self._rula_calculator = RULACalculator()
        self._reba_calculator = REBACalculator()
        self._owas_calculator = OWASCalculator()

        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 상단: 체크박스 영역
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setSpacing(15)

        self._rula_checkbox = QCheckBox("RULA")
        self._reba_checkbox = QCheckBox("REBA")
        self._owas_checkbox = QCheckBox("OWAS")

        # 기본: 모두 체크
        self._rula_checkbox.setChecked(True)
        self._reba_checkbox.setChecked(True)
        self._owas_checkbox.setChecked(True)

        # 체크박스 스타일
        checkbox_style = """
            QCheckBox {
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """
        self._rula_checkbox.setStyleSheet(checkbox_style)
        self._reba_checkbox.setStyleSheet(checkbox_style)
        self._owas_checkbox.setStyleSheet(checkbox_style)

        # 체크박스 연결
        self._rula_checkbox.toggled.connect(self._update_visibility)
        self._reba_checkbox.toggled.connect(self._update_visibility)
        self._owas_checkbox.toggled.connect(self._update_visibility)

        checkbox_layout.addWidget(self._rula_checkbox)
        checkbox_layout.addWidget(self._reba_checkbox)
        checkbox_layout.addWidget(self._owas_checkbox)
        checkbox_layout.addStretch()

        layout.addLayout(checkbox_layout)

        # 하단: 가로 스플리터 (왼쪽 | 가운데 | 오른쪽)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # 각 평가 위젯
        self._rula_widget = RULAWidget()
        self._reba_widget = REBAWidget()
        self._owas_widget = OWASWidget()

        self._splitter.addWidget(self._rula_widget)
        self._splitter.addWidget(self._reba_widget)
        self._splitter.addWidget(self._owas_widget)

        # 균등 분할
        self._splitter.setSizes([300, 300, 300])

        layout.addWidget(self._splitter)

    def _update_visibility(self):
        """체크박스 상태에 따라 위젯 가시성 업데이트"""
        self._rula_widget.setVisible(self._rula_checkbox.isChecked())
        self._reba_widget.setVisible(self._reba_checkbox.isChecked())
        self._owas_widget.setVisible(self._owas_checkbox.isChecked())

    def update_assessment(self, angles: Dict[str, float], landmarks: List[Dict]):
        """
        모든 평가 업데이트

        Args:
            angles: 관절 각도 딕셔너리
            landmarks: MediaPipe landmark 리스트
        """
        if not angles or not landmarks:
            self.clear()
            return

        # RULA 계산 및 업데이트
        rula_result = self._rula_calculator.calculate(angles, landmarks)
        self._rula_widget.update_result(rula_result)

        # REBA 계산 및 업데이트
        reba_result = self._reba_calculator.calculate(angles, landmarks)
        self._reba_widget.update_result(reba_result)

        # OWAS 계산 및 업데이트
        owas_result = self._owas_calculator.calculate(angles, landmarks)
        self._owas_widget.update_result(owas_result)

    def clear(self):
        """모든 위젯 초기화"""
        self._rula_widget.clear()
        self._reba_widget.clear()
        self._owas_widget.clear()

    @property
    def rula_widget(self) -> RULAWidget:
        """RULA 위젯 반환"""
        return self._rula_widget

    @property
    def reba_widget(self) -> REBAWidget:
        """REBA 위젯 반환"""
        return self._reba_widget

    @property
    def owas_widget(self) -> OWASWidget:
        """OWAS 위젯 반환"""
        return self._owas_widget
