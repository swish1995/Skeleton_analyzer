"""SI (Strain Index) 결과 표시 및 입력 위젯"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QGridLayout, QFrame, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ...core.ergonomic.si_calculator import SICalculator, SIResult


class SIWidget(QWidget):
    """SI 평가 입력 및 결과 표시 위젯"""

    # 시그널
    inputs_changed = pyqtSignal()  # 입력값 변경 시

    # 색상 정의
    COLORS = {
        'safe': '#4CAF50',        # 초록
        'uncertain': '#FF9800',    # 주황
        'hazardous': '#F44336',    # 빨강
    }

    RISK_LABELS = {
        'safe': '안전',
        'uncertain': '불확실',
        'hazardous': '위험',
    }

    # 파라미터 정의
    PARAMS = {
        'ie': {
            'name': 'IE',
            'label': '힘의 강도',
            'tooltip': 'Intensity of Exertion: 힘의 강도',
            'levels': [
                (1, 'Light'),
                (2, 'Somewhat Hard'),
                (3, 'Hard'),
                (4, 'Very Hard'),
                (5, 'Near Maximal'),
            ]
        },
        'de': {
            'name': 'DE',
            'label': '지속시간 비율',
            'tooltip': 'Duration of Exertion: 1회 지속시간 비율 (%)',
            'levels': [
                (1, '<10%'),
                (2, '10-29%'),
                (3, '30-49%'),
                (4, '50-79%'),
                (5, '≥80%'),
            ]
        },
        'em': {
            'name': 'EM',
            'label': '분당 반복 횟수',
            'tooltip': 'Efforts per Minute: 분당 반복 횟수',
            'levels': [
                (1, '<4회/분'),
                (2, '4-8회/분'),
                (3, '9-14회/분'),
                (4, '15-19회/분'),
                (5, '≥20회/분'),
            ]
        },
        'hwp': {
            'name': 'HWP',
            'label': '손목 자세',
            'tooltip': 'Hand/Wrist Posture: 손목 자세',
            'levels': [
                (1, 'Very Good'),
                (2, 'Good'),
                (3, 'Fair'),
                (4, 'Bad'),
                (5, 'Very Bad'),
            ]
        },
        'sw': {
            'name': 'SW',
            'label': '작업 속도',
            'tooltip': 'Speed of Work: 작업 속도',
            'levels': [
                (1, 'Very Slow'),
                (2, 'Slow'),
                (3, 'Fair'),
                (4, 'Fast'),
                (5, 'Very Fast'),
            ]
        },
        'dd': {
            'name': 'DD',
            'label': '일일 작업 시간',
            'tooltip': 'Duration per Day: 일일 작업 시간',
            'levels': [
                (1, '≤1시간'),
                (2, '1-2시간'),
                (3, '2-4시간'),
                (4, '4-8시간'),
                (5, '>8시간'),
            ]
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._calculator = SICalculator()
        self._current_result: SIResult = None
        self._combos = {}
        self._mult_labels = {}
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
        title_label = QLabel("SI")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #b8a85a;")
        layout.addWidget(title_label)

        # 상단: 결과 표시
        result_frame = QFrame()
        result_frame.setFrameShape(QFrame.Shape.StyledPanel)
        result_layout = QHBoxLayout(result_frame)
        result_layout.setContentsMargins(10, 10, 10, 10)

        # Score
        score_box = QVBoxLayout()
        score_box.addWidget(QLabel("SI Score"))
        self._score_label = QLabel("–")
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_font = QFont()
        score_font.setPointSize(28)
        score_font.setBold(True)
        self._score_label.setFont(score_font)
        score_box.addWidget(self._score_label)
        result_layout.addLayout(score_box)

        # Risk
        risk_box = QVBoxLayout()
        risk_box.addWidget(QLabel("위험도"))
        self._risk_label = QLabel("–")
        self._risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        risk_font = QFont()
        risk_font.setPointSize(14)
        risk_font.setBold(True)
        self._risk_label.setFont(risk_font)
        risk_box.addWidget(self._risk_label)
        result_layout.addLayout(risk_box)

        layout.addWidget(result_frame)

        # 중단: 입력 폼
        input_box = QGroupBox("입력 파라미터")
        input_layout = QGridLayout(input_box)
        input_layout.setSpacing(5)

        row = 0
        for key, param in self.PARAMS.items():
            # 라벨
            label = QLabel(f"{param['name']}:")
            label.setToolTip(param['tooltip'])
            input_layout.addWidget(label, row, 0)

            # ComboBox
            combo = QComboBox()
            combo.setToolTip(param['tooltip'])
            for value, text in param['levels']:
                combo.addItem(f"{value}: {text}", value)
            input_layout.addWidget(combo, row, 1)
            self._combos[key] = combo

            # Multiplier 표시
            mult_label = QLabel("–")
            mult_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mult_label.setMinimumWidth(40)
            input_layout.addWidget(mult_label, row, 2)
            self._mult_labels[key] = mult_label

            row += 1

        layout.addWidget(input_box)

        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _connect_signals(self):
        """시그널 연결"""
        for combo in self._combos.values():
            combo.currentIndexChanged.connect(self._on_input_changed)

    def _on_input_changed(self):
        """입력값 변경 시 재계산"""
        self._calculate()
        self.inputs_changed.emit()

    def _calculate(self):
        """현재 입력값으로 계산"""
        inputs = self.get_inputs()
        self._current_result = self._calculator.calculate(**inputs)
        self._update_display()

    def _update_display(self):
        """결과 표시 업데이트"""
        if not self._current_result:
            return

        result = self._current_result

        # Score
        if result.score >= 100:
            self._score_label.setText(f"{result.score:.0f}")
        elif result.score >= 10:
            self._score_label.setText(f"{result.score:.1f}")
        else:
            self._score_label.setText(f"{result.score:.2f}")

        # Risk
        risk_text = self.RISK_LABELS.get(result.risk_level, result.risk_level)
        color = self.COLORS.get(result.risk_level, '#888888')
        self._risk_label.setText(risk_text)
        self._risk_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self._score_label.setStyleSheet(f"color: {color};")

        # Multipliers
        self._mult_labels['ie'].setText(f"{result.ie_m:.1f}")
        self._mult_labels['de'].setText(f"{result.de_m:.1f}")
        self._mult_labels['em'].setText(f"{result.em_m:.1f}")
        self._mult_labels['hwp'].setText(f"{result.hwp_m:.1f}")
        self._mult_labels['sw'].setText(f"{result.sw_m:.1f}")
        self._mult_labels['dd'].setText(f"{result.dd_m:.2f}")

    def get_inputs(self) -> dict:
        """현재 입력값 반환"""
        return {
            'ie': self._combos['ie'].currentData(),
            'de': self._combos['de'].currentData(),
            'em': self._combos['em'].currentData(),
            'hwp': self._combos['hwp'].currentData(),
            'sw': self._combos['sw'].currentData(),
            'dd': self._combos['dd'].currentData(),
        }

    def set_inputs(self, ie=1, de=1, em=1, hwp=1, sw=1, dd=1):
        """입력값 설정"""
        for key, combo in self._combos.items():
            combo.blockSignals(True)

        # 각 콤보박스에서 해당 값 찾기
        params = {'ie': ie, 'de': de, 'em': em, 'hwp': hwp, 'sw': sw, 'dd': dd}
        for key, value in params.items():
            combo = self._combos[key]
            for i in range(combo.count()):
                if combo.itemData(i) == value:
                    combo.setCurrentIndex(i)
                    break

        for combo in self._combos.values():
            combo.blockSignals(False)

        self._calculate()

    def get_result(self) -> SIResult:
        """현재 결과 반환"""
        return self._current_result

    def clear(self):
        """초기화"""
        self._score_label.setText("–")
        self._risk_label.setText("–")
        self._risk_label.setStyleSheet("")
        self._score_label.setStyleSheet("")

        for label in self._mult_labels.values():
            label.setText("–")

        self._current_result = None
