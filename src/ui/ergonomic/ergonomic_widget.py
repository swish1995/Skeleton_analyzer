"""인체공학적 평가 통합 위젯"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QStackedWidget, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict, List

from ...core.ergonomic import (
    RULACalculator, RULAResult,
    REBACalculator, REBAResult,
    OWASCalculator, OWASResult,
    NLEResult,
    SIResult,
)
from ...license import LicenseManager
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

        # 라이센스 매니저
        self._license_manager = LicenseManager.instance()
        self._license_manager.license_changed.connect(self._update_license_state)

        self._init_ui()

        # 초기 라이센스 상태 적용
        self._update_license_state()

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

        # NLE (QStackedWidget으로 위젯/잠금화면 전환)
        self._nle_stack = QStackedWidget()
        self._nle_widget = NLEWidget()
        self._nle_lock = self._create_lock_widget("NLE 분석")
        self._nle_stack.addWidget(self._nle_widget)  # index 0: 실제 위젯
        self._nle_stack.addWidget(self._nle_lock)    # index 1: 잠금 화면
        self._nle_stack.setMinimumWidth(120)
        self._nle_stack.setVisible(False)  # 기본 숨김
        self._main_splitter.addWidget(self._nle_stack)

        # SI (QStackedWidget으로 위젯/잠금화면 전환)
        self._si_stack = QStackedWidget()
        self._si_widget = SIWidget()
        self._si_lock = self._create_lock_widget("SI 분석")
        self._si_stack.addWidget(self._si_widget)  # index 0: 실제 위젯
        self._si_stack.addWidget(self._si_lock)    # index 1: 잠금 화면
        self._si_stack.setMinimumWidth(120)
        self._si_stack.setVisible(False)  # 기본 숨김
        self._main_splitter.addWidget(self._si_stack)

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
        self._nle_stack.setVisible(visible)
        if visible:
            self._update_license_state()

    def set_si_visible(self, visible: bool):
        """SI 위젯 가시성 설정"""
        self._si_stack.setVisible(visible)
        if visible:
            self._update_license_state()

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
        return self._nle_stack.isVisible()

    def is_si_visible(self) -> bool:
        """SI 위젯 가시성 반환"""
        return self._si_stack.isVisible()

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

    # === 라이센스 관련 메서드 ===

    def _update_license_state(self):
        """라이센스 상태에 따른 위젯/잠금화면 전환"""
        can_use_nle = self._license_manager.check_feature('nle_analysis')
        can_use_si = self._license_manager.check_feature('si_analysis')

        # NLE: 0=위젯, 1=잠금화면
        self._nle_stack.setCurrentIndex(0 if can_use_nle else 1)

        # SI: 0=위젯, 1=잠금화면
        self._si_stack.setCurrentIndex(0 if can_use_si else 1)

    def _create_lock_widget(self, feature_name: str) -> QWidget:
        """잠금 화면 위젯 생성"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 잠금 아이콘
        icon_label = QLabel("🔒")
        icon_font = QFont()
        icon_font.setPointSize(36)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)

        # 메시지
        message_label = QLabel(f"{feature_name}은(는)\n등록 버전에서 사용할 수 있습니다")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            color: #888888;
            font-size: 13px;
            background: transparent;
        """)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # 등록 버튼
        register_btn = QPushButton("라이센스 등록")
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5aaeFF;
            }
            QPushButton:pressed {
                background-color: #3a8eef;
            }
        """)
        register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        register_btn.clicked.connect(self._show_license_dialog)
        register_btn.setFixedWidth(140)
        layout.addWidget(register_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return widget

    def _show_license_dialog(self):
        """라이센스 다이얼로그 표시"""
        from ...license.license_dialog import LicenseDialog
        dialog = LicenseDialog(self.window())
        dialog.exec()
