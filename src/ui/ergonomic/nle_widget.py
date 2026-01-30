"""NLE (NIOSH Lifting Equation) 결과 표시 및 입력 위젯"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QGridLayout, QFrame, QSpinBox, QDoubleSpinBox,
    QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ...core.ergonomic.nle_calculator import NLECalculator, NLEResult


class NLEWidget(QWidget):
    """NLE 평가 입력 및 결과 표시 위젯"""

    # 시그널
    inputs_changed = pyqtSignal()  # 입력값 변경 시

    # 색상 정의
    COLORS = {
        'safe': '#4CAF50',       # 초록
        'increased': '#FF9800',   # 주황
        'high': '#F44336',        # 빨강
    }

    RISK_LABELS = {
        'safe': '안전',
        'increased': '주의 필요',
        'high': '즉시 개선',
    }

    COUPLING_OPTIONS = [
        (1, 'Good (양호)'),
        (2, 'Fair (보통)'),
        (3, 'Poor (불량)'),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._calculator = NLECalculator()
        self._current_result: NLEResult = None
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # 제목
        title_label = QLabel("NLE")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #5a8ab8;")
        layout.addWidget(title_label)

        # 상단: 결과 표시
        result_frame = QFrame()
        result_frame.setFrameShape(QFrame.Shape.StyledPanel)
        result_layout = QHBoxLayout(result_frame)
        result_layout.setContentsMargins(5, 5, 5, 5)

        # RWL
        rwl_box = QVBoxLayout()
        rwl_box.addWidget(QLabel("RWL (kg)"))
        self._rwl_label = QLabel("–")
        self._rwl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rwl_font = QFont()
        rwl_font.setPointSize(18)
        rwl_font.setBold(True)
        self._rwl_label.setFont(rwl_font)
        rwl_box.addWidget(self._rwl_label)
        result_layout.addLayout(rwl_box)

        # LI
        li_box = QVBoxLayout()
        li_box.addWidget(QLabel("LI"))
        self._li_label = QLabel("–")
        self._li_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._li_label.setFont(rwl_font)
        li_box.addWidget(self._li_label)
        result_layout.addLayout(li_box)

        # Risk
        risk_box = QVBoxLayout()
        risk_box.addWidget(QLabel("위험도"))
        self._risk_label = QLabel("–")
        self._risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        risk_font = QFont()
        risk_font.setPointSize(12)
        risk_font.setBold(True)
        self._risk_label.setFont(risk_font)
        risk_box.addWidget(self._risk_label)
        result_layout.addLayout(risk_box)

        layout.addWidget(result_frame)

        # 중단: 입력 폼
        input_box = QGroupBox("입력 파라미터")
        input_layout = QGridLayout(input_box)
        input_layout.setSpacing(5)

        # H (수평 거리)
        input_layout.addWidget(QLabel("H (cm):"), 0, 0)
        self._h_spin = QDoubleSpinBox()
        self._h_spin.setRange(25, 63)
        self._h_spin.setValue(25)
        self._h_spin.setSingleStep(1)
        self._h_spin.setToolTip("수평 거리: 손과 척추 중심선 사이 거리 (25-63 cm)")
        input_layout.addWidget(self._h_spin, 0, 1)

        # V (수직 높이)
        input_layout.addWidget(QLabel("V (cm):"), 0, 2)
        self._v_spin = QDoubleSpinBox()
        self._v_spin.setRange(0, 175)
        self._v_spin.setValue(75)
        self._v_spin.setSingleStep(5)
        self._v_spin.setToolTip("수직 높이: 손 위치의 바닥으로부터 높이 (0-175 cm)")
        input_layout.addWidget(self._v_spin, 0, 3)

        # D (이동 거리)
        input_layout.addWidget(QLabel("D (cm):"), 1, 0)
        self._d_spin = QDoubleSpinBox()
        self._d_spin.setRange(25, 175)
        self._d_spin.setValue(25)
        self._d_spin.setSingleStep(5)
        self._d_spin.setToolTip("이동 거리: 들기 시작과 끝의 수직 거리 (25-175 cm)")
        input_layout.addWidget(self._d_spin, 1, 1)

        # A (비틀림 각도)
        input_layout.addWidget(QLabel("A (°):"), 1, 2)
        self._a_spin = QDoubleSpinBox()
        self._a_spin.setRange(0, 135)
        self._a_spin.setValue(0)
        self._a_spin.setSingleStep(15)
        self._a_spin.setToolTip("비틀림 각도: 몸통 비틀림 각도 (0-135°)")
        input_layout.addWidget(self._a_spin, 1, 3)

        # F (빈도)
        input_layout.addWidget(QLabel("F (회/분):"), 2, 0)
        self._f_spin = QDoubleSpinBox()
        self._f_spin.setRange(0.2, 15)
        self._f_spin.setValue(1)
        self._f_spin.setSingleStep(0.5)
        self._f_spin.setToolTip("빈도: 분당 들기 횟수 (0.2-15 회/분)")
        input_layout.addWidget(self._f_spin, 2, 1)

        # Load (실제 중량)
        input_layout.addWidget(QLabel("Load (kg):"), 2, 2)
        self._load_spin = QDoubleSpinBox()
        self._load_spin.setRange(0, 100)
        self._load_spin.setValue(0)
        self._load_spin.setSingleStep(1)
        self._load_spin.setToolTip("실제 중량 (kg)")
        input_layout.addWidget(self._load_spin, 2, 3)

        # C (커플링)
        input_layout.addWidget(QLabel("Coupling:"), 3, 0)
        self._c_combo = QComboBox()
        for value, text in self.COUPLING_OPTIONS:
            self._c_combo.addItem(text, value)
        self._c_combo.setToolTip("손잡이 품질")
        input_layout.addWidget(self._c_combo, 3, 1, 1, 3)

        layout.addWidget(input_box)

        # 하단: Multipliers
        mult_box = QGroupBox("Multipliers")
        mult_layout = QGridLayout(mult_box)
        mult_layout.setSpacing(3)

        self._mult_labels = {}
        mult_names = ['HM', 'VM', 'DM', 'AM', 'FM', 'CM']
        for i, name in enumerate(mult_names):
            row, col = i // 3, (i % 3) * 2
            mult_layout.addWidget(QLabel(f"{name}:"), row, col)
            label = QLabel("–")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mult_layout.addWidget(label, row, col + 1)
            self._mult_labels[name.lower()] = label

        layout.addWidget(mult_box)

        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _connect_signals(self):
        """시그널 연결"""
        self._h_spin.valueChanged.connect(self._on_input_changed)
        self._v_spin.valueChanged.connect(self._on_input_changed)
        self._d_spin.valueChanged.connect(self._on_input_changed)
        self._a_spin.valueChanged.connect(self._on_input_changed)
        self._f_spin.valueChanged.connect(self._on_input_changed)
        self._load_spin.valueChanged.connect(self._on_input_changed)
        self._c_combo.currentIndexChanged.connect(self._on_input_changed)

    def _on_input_changed(self):
        """입력값 변경 시 재계산"""
        self._calculate()
        self.inputs_changed.emit()

    def _calculate(self):
        """현재 입력값으로 계산"""
        h = self._h_spin.value()
        v = self._v_spin.value()
        d = self._d_spin.value()
        a = self._a_spin.value()
        f = self._f_spin.value()
        c = self._c_combo.currentData()
        load = self._load_spin.value()

        self._current_result = self._calculator.calculate(
            h=h, v=v, d=d, a=a,
            frequency=f, duration_hours=1.0, coupling=c, load=load
        )

        self._update_display()

    def _update_display(self):
        """결과 표시 업데이트"""
        if not self._current_result:
            return

        result = self._current_result

        # RWL, LI
        self._rwl_label.setText(f"{result.rwl:.1f}")
        self._li_label.setText(f"{result.li:.2f}")

        # Risk
        risk_text = self.RISK_LABELS.get(result.risk_level, result.risk_level)
        color = self.COLORS.get(result.risk_level, '#888888')
        self._risk_label.setText(risk_text)
        self._risk_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self._li_label.setStyleSheet(f"color: {color};")

        # Multipliers
        self._mult_labels['hm'].setText(f"{result.hm:.3f}")
        self._mult_labels['vm'].setText(f"{result.vm:.3f}")
        self._mult_labels['dm'].setText(f"{result.dm:.3f}")
        self._mult_labels['am'].setText(f"{result.am:.3f}")
        self._mult_labels['fm'].setText(f"{result.fm:.3f}")
        self._mult_labels['cm'].setText(f"{result.cm:.3f}")

    def get_inputs(self) -> dict:
        """현재 입력값 반환"""
        return {
            'h': self._h_spin.value(),
            'v': self._v_spin.value(),
            'd': self._d_spin.value(),
            'a': self._a_spin.value(),
            'f': self._f_spin.value(),
            'c': self._c_combo.currentData(),
            'load': self._load_spin.value(),
        }

    def set_inputs(self, h=25, v=75, d=25, a=0, f=1, c=1, load=0):
        """입력값 설정"""
        self._h_spin.blockSignals(True)
        self._v_spin.blockSignals(True)
        self._d_spin.blockSignals(True)
        self._a_spin.blockSignals(True)
        self._f_spin.blockSignals(True)
        self._load_spin.blockSignals(True)
        self._c_combo.blockSignals(True)

        self._h_spin.setValue(h)
        self._v_spin.setValue(v)
        self._d_spin.setValue(d)
        self._a_spin.setValue(a)
        self._f_spin.setValue(f)
        self._load_spin.setValue(load)

        # Coupling 설정
        for i in range(self._c_combo.count()):
            if self._c_combo.itemData(i) == c:
                self._c_combo.setCurrentIndex(i)
                break

        self._h_spin.blockSignals(False)
        self._v_spin.blockSignals(False)
        self._d_spin.blockSignals(False)
        self._a_spin.blockSignals(False)
        self._f_spin.blockSignals(False)
        self._load_spin.blockSignals(False)
        self._c_combo.blockSignals(False)

        self._calculate()

    def get_result(self) -> NLEResult:
        """현재 결과 반환"""
        return self._current_result

    def clear(self):
        """초기화"""
        self._rwl_label.setText("–")
        self._li_label.setText("–")
        self._risk_label.setText("–")
        self._risk_label.setStyleSheet("")
        self._li_label.setStyleSheet("")

        for label in self._mult_labels.values():
            label.setText("–")

        self._current_result = None
