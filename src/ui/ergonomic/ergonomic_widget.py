"""인체공학적 평가 통합 위젯"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
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
    """인체공학적 평가 통합 위젯 (탭 방식)"""

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
        layout.setContentsMargins(0, 0, 0, 0)

        # 탭 위젯
        self._tab_widget = QTabWidget()

        # 각 평가 위젯
        self._rula_widget = RULAWidget()
        self._reba_widget = REBAWidget()
        self._owas_widget = OWASWidget()

        self._tab_widget.addTab(self._rula_widget, "RULA")
        self._tab_widget.addTab(self._reba_widget, "REBA")
        self._tab_widget.addTab(self._owas_widget, "OWAS")

        layout.addWidget(self._tab_widget)

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
    def tab_widget(self) -> QTabWidget:
        """탭 위젯 반환"""
        return self._tab_widget

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
