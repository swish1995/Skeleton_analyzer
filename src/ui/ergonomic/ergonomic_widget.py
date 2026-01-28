"""인체공학적 평가 통합 위젯"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter
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
    """인체공학적 평가 통합 위젯 (가로 3분할)"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 계산기 초기화
        self._rula_calculator = RULACalculator()
        self._reba_calculator = REBACalculator()
        self._owas_calculator = OWASCalculator()

        # 현재 결과 저장
        self._current_rula_result: RULAResult = None
        self._current_reba_result: REBAResult = None
        self._current_owas_result: OWASResult = None

        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(0)

        # 가로 스플리터 (왼쪽 | 가운데 | 오른쪽)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(8)
        self._splitter.setStyleSheet("""
            QSplitter::handle:horizontal {
                width: 2px;
                margin-left: 1px;
                margin-right: 5px;
                background: qlineargradient(
                    x1: 0, y1: 0.25,
                    x2: 0, y2: 0.75,
                    stop: 0 transparent,
                    stop: 0.001 #888888,
                    stop: 0.999 #888888,
                    stop: 1 transparent
                );
            }
        """)

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

    # === 외부에서 패널 가시성 제어 ===

    def set_rula_visible(self, visible: bool):
        """RULA 위젯 가시성 설정"""
        self._rula_widget.setVisible(visible)

    def set_reba_visible(self, visible: bool):
        """REBA 위젯 가시성 설정"""
        self._reba_widget.setVisible(visible)

    def set_owas_visible(self, visible: bool):
        """OWAS 위젯 가시성 설정"""
        self._owas_widget.setVisible(visible)

    def is_rula_visible(self) -> bool:
        """RULA 위젯 가시성 반환"""
        return self._rula_widget.isVisible()

    def is_reba_visible(self) -> bool:
        """REBA 위젯 가시성 반환"""
        return self._reba_widget.isVisible()

    def is_owas_visible(self) -> bool:
        """OWAS 위젯 가시성 반환"""
        return self._owas_widget.isVisible()

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
        self._current_rula_result = self._rula_calculator.calculate(angles, landmarks)
        self._rula_widget.update_result(self._current_rula_result)

        # REBA 계산 및 업데이트
        self._current_reba_result = self._reba_calculator.calculate(angles, landmarks)
        self._reba_widget.update_result(self._current_reba_result)

        # OWAS 계산 및 업데이트
        self._current_owas_result = self._owas_calculator.calculate(angles, landmarks)
        self._owas_widget.update_result(self._current_owas_result)

    def clear(self):
        """모든 위젯 초기화"""
        self._rula_widget.clear()
        self._reba_widget.clear()
        self._owas_widget.clear()
        self._current_rula_result = None
        self._current_reba_result = None
        self._current_owas_result = None

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

    def get_current_results(self) -> Dict:
        """
        현재 평가 결과 반환

        Returns:
            dict with 'rula', 'reba', 'owas' keys containing result dicts
        """
        return {
            'rula': self._current_rula_result,
            'reba': self._current_reba_result,
            'owas': self._current_owas_result,
        }

    def has_results(self) -> bool:
        """현재 결과가 있는지 확인"""
        return (
            self._current_rula_result is not None or
            self._current_reba_result is not None or
            self._current_owas_result is not None
        )
