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
    NLEResult,
    SIResult,
)
from .rula_widget import RULAWidget
from .reba_widget import REBAWidget
from .owas_widget import OWASWidget
from .nle_widget import NLEWidget
from .si_widget import SIWidget


class ErgonomicWidget(QWidget):
    """인체공학적 평가 통합 위젯 (1행 5분할 레이아웃)

    RULA | REBA | OWAS | NLE | SI
    """

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
        layout.setSpacing(2)

        # 스플리터 스타일
        horizontal_splitter_style = """
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
        """

        # 메인 가로 스플리터 (RULA | REBA | OWAS | NLE | SI)
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.setHandleWidth(8)
        self._main_splitter.setStyleSheet(horizontal_splitter_style)

        # RULA
        self._rula_widget = RULAWidget()
        self._rula_widget.setMinimumWidth(120)
        self._main_splitter.addWidget(self._rula_widget)

        # REBA
        self._reba_widget = REBAWidget()
        self._reba_widget.setMinimumWidth(120)
        self._main_splitter.addWidget(self._reba_widget)

        # OWAS
        self._owas_widget = OWASWidget()
        self._owas_widget.setMinimumWidth(120)
        self._main_splitter.addWidget(self._owas_widget)

        # NLE
        self._nle_widget = NLEWidget()
        self._nle_widget.setMinimumWidth(120)
        self._nle_widget.setVisible(False)  # 기본 숨김
        self._main_splitter.addWidget(self._nle_widget)

        # SI
        self._si_widget = SIWidget()
        self._si_widget.setMinimumWidth(120)
        self._si_widget.setVisible(False)  # 기본 숨김
        self._main_splitter.addWidget(self._si_widget)

        # 스플리터 축소 방지
        for i in range(5):
            self._main_splitter.setCollapsible(i, False)

        # 초기 크기 (균등 분할)
        self._main_splitter.setSizes([200, 200, 200, 200, 200])

        layout.addWidget(self._main_splitter)

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

    def set_nle_visible(self, visible: bool):
        """NLE 위젯 가시성 설정"""
        self._nle_widget.setVisible(visible)

    def set_si_visible(self, visible: bool):
        """SI 위젯 가시성 설정"""
        self._si_widget.setVisible(visible)

    def is_rula_visible(self) -> bool:
        """RULA 위젯 가시성 반환"""
        return self._rula_widget.isVisible()

    def is_reba_visible(self) -> bool:
        """REBA 위젯 가시성 반환"""
        return self._reba_widget.isVisible()

    def is_owas_visible(self) -> bool:
        """OWAS 위젯 가시성 반환"""
        return self._owas_widget.isVisible()

    def is_nle_visible(self) -> bool:
        """NLE 위젯 가시성 반환"""
        return self._nle_widget.isVisible()

    def is_si_visible(self) -> bool:
        """SI 위젯 가시성 반환"""
        return self._si_widget.isVisible()

    def update_assessment(self, angles: Dict[str, float], landmarks: List[Dict]):
        """
        모든 평가 업데이트 (영상 분석 기반 - RULA/REBA/OWAS만)

        Args:
            angles: 관절 각도 딕셔너리
            landmarks: MediaPipe landmark 리스트
        """
        if not angles or not landmarks:
            self.clear_image_based()
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

    def clear_image_based(self):
        """영상 분석 기반 위젯 초기화 (RULA/REBA/OWAS)"""
        self._rula_widget.clear()
        self._reba_widget.clear()
        self._owas_widget.clear()
        self._current_rula_result = None
        self._current_reba_result = None
        self._current_owas_result = None

    def clear(self):
        """모든 위젯 초기화"""
        self.clear_image_based()
        self._nle_widget.clear()
        self._si_widget.clear()

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

    @property
    def nle_widget(self) -> NLEWidget:
        """NLE 위젯 반환"""
        return self._nle_widget

    @property
    def si_widget(self) -> SIWidget:
        """SI 위젯 반환"""
        return self._si_widget

    def get_current_results(self) -> Dict:
        """
        현재 평가 결과 반환

        Returns:
            dict with 'rula', 'reba', 'owas', 'nle', 'si' keys containing result objects
        """
        return {
            'rula': self._current_rula_result,
            'reba': self._current_reba_result,
            'owas': self._current_owas_result,
            'nle': self._nle_widget.get_result(),
            'si': self._si_widget.get_result(),
        }

    def has_results(self) -> bool:
        """현재 결과가 있는지 확인"""
        return (
            self._current_rula_result is not None or
            self._current_reba_result is not None or
            self._current_owas_result is not None
        )

    def get_nle_inputs(self) -> dict:
        """NLE 입력값 반환"""
        return self._nle_widget.get_inputs()

    def get_si_inputs(self) -> dict:
        """SI 입력값 반환"""
        return self._si_widget.get_inputs()

    def set_nle_inputs(self, **kwargs):
        """NLE 입력값 설정"""
        self._nle_widget.set_inputs(**kwargs)

    def set_si_inputs(self, **kwargs):
        """SI 입력값 설정"""
        self._si_widget.set_inputs(**kwargs)
