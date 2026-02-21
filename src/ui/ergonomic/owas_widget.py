"""OWAS 결과 표시 위젯"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QGridLayout, QFrame, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ...core.ergonomic.owas_calculator import OWASResult


class OWASWidget(QWidget):
    """OWAS 평가 결과 표시 위젯"""

    # 수동 입력 변경 시그널 (하중 또는 앉음 변경 시 재계산 요청)
    manual_input_changed = pyqtSignal()

    # 색상 정의
    COLORS = {
        'normal': '#4CAF50',        # 초록
        'slight': '#FFC107',        # 노랑
        'harmful': '#FF9800',       # 주황
        'very_harmful': '#F44336',  # 빨강
    }

    AC_LABELS = {
        1: 'AC1',
        2: 'AC2',
        3: 'AC3',
        4: 'AC4',
    }

    RISK_LABELS = {
        'normal': '개선 필요 없음',
        'slight': '부분적 개선',
        'harmful': '곧 개선 필요',
        'very_harmful': '즉시 개선',
    }

    BACK_DESCRIPTIONS = {
        1: '직립',
        2: '굴곡',
        3: '회전/측굴',
        4: '굴곡+회전',
    }

    ARMS_DESCRIPTIONS = {
        1: '양팔 어깨 아래',
        2: '한 팔 어깨 위',
        3: '양팔 어깨 위',
    }

    LEGS_DESCRIPTIONS = {
        1: '앉기',
        2: '양다리 서기',
        3: '한다리 서기',
        4: '양무릎 굴곡',
        5: '한무릎 굴곡',
        6: '무릎꿇기',
        7: '걷기/이동',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 제목
        title_label = QLabel("OWAS")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #FF5722;")
        layout.addWidget(title_label)

        # 상단: 자세 코드 및 AC
        code_frame = QFrame()
        code_frame.setFrameShape(QFrame.Shape.StyledPanel)
        code_layout = QVBoxLayout(code_frame)

        # 자세 코드
        self._posture_code_label = QLabel("–,–,–,–")
        self._posture_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code_font = QFont()
        code_font.setPointSize(36)
        code_font.setBold(True)
        code_font.setFamily("Courier")
        self._posture_code_label.setFont(code_font)
        code_layout.addWidget(self._posture_code_label)

        # AC 표시
        self._ac_label = QLabel("–")
        self._ac_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ac_font = QFont()
        ac_font.setPointSize(24)
        ac_font.setBold(True)
        self._ac_label.setFont(ac_font)
        code_layout.addWidget(self._ac_label)

        # 위험 수준
        self._risk_label = QLabel("대기 중")
        self._risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        risk_font = QFont()
        risk_font.setPointSize(14)
        self._risk_label.setFont(risk_font)
        code_layout.addWidget(self._risk_label)

        layout.addWidget(code_frame)

        # 중단: 자세 코드 설명
        code_box = QGroupBox("자세 코드 상세")
        code_detail_layout = QGridLayout(code_box)

        # 각 코드 설명
        code_detail_layout.addWidget(QLabel("등 (1자리):"), 0, 0)
        self._back_code_label = QLabel("–")
        self._back_code_label.setStyleSheet("font-weight: bold;")
        code_detail_layout.addWidget(self._back_code_label, 0, 1)
        self._back_desc_label = QLabel("")
        code_detail_layout.addWidget(self._back_desc_label, 0, 2)

        code_detail_layout.addWidget(QLabel("팔 (2자리):"), 1, 0)
        self._arms_code_label = QLabel("–")
        self._arms_code_label.setStyleSheet("font-weight: bold;")
        code_detail_layout.addWidget(self._arms_code_label, 1, 1)
        self._arms_desc_label = QLabel("")
        code_detail_layout.addWidget(self._arms_desc_label, 1, 2)

        code_detail_layout.addWidget(QLabel("다리 (3자리):"), 2, 0)
        self._legs_code_label = QLabel("–")
        self._legs_code_label.setStyleSheet("font-weight: bold;")
        code_detail_layout.addWidget(self._legs_code_label, 2, 1)
        self._legs_desc_label = QLabel("")
        code_detail_layout.addWidget(self._legs_desc_label, 2, 2)

        code_detail_layout.addWidget(QLabel("하중 (4자리):"), 3, 0)
        self._load_code_label = QLabel("–")
        self._load_code_label.setStyleSheet("font-weight: bold;")
        code_detail_layout.addWidget(self._load_code_label, 3, 1)
        self._load_desc_label = QLabel("")
        code_detail_layout.addWidget(self._load_desc_label, 3, 2)

        layout.addWidget(code_box)

        # 수동 입력 영역
        manual_box = QGroupBox("수동 입력")
        manual_layout = QGridLayout(manual_box)

        # 하중 셀렉트 박스
        manual_layout.addWidget(QLabel("하중:"), 0, 0)
        self._load_combo = QComboBox()
        self._load_combo.addItem("1: 10kg 미만", 1)
        self._load_combo.addItem("2: 10-20kg", 2)
        self._load_combo.addItem("3: 20kg 초과", 3)
        self._load_combo.setCurrentIndex(0)
        self._load_combo.setToolTip("하중 코드 (1-3)")
        self._load_combo.currentIndexChanged.connect(self._on_manual_input_changed)
        manual_layout.addWidget(self._load_combo, 0, 1)

        # 앉음 체크박스
        self._sitting_checkbox = QCheckBox("앉음 (의자 등)")
        self._sitting_checkbox.setToolTip("의자 등에 앉은 상태일 때 체크\n(스켈레톤으로 판별 불가)")
        self._sitting_checkbox.stateChanged.connect(self._on_manual_input_changed)
        manual_layout.addWidget(self._sitting_checkbox, 1, 0, 1, 2)

        layout.addWidget(manual_box)

        layout.addStretch()

    def update_result(self, result: OWASResult):
        """결과 업데이트"""
        if result is None:
            self.clear()
            return

        color = self.COLORS.get(result.risk_level, '#888888')

        # 자세 코드 (콤마로 구분)
        code_with_comma = ",".join(result.posture_code)
        self._posture_code_label.setText(code_with_comma)
        self._posture_code_label.setStyleSheet(f"color: {color};")

        # AC
        ac_text = self.AC_LABELS.get(result.action_category, str(result.action_category))
        self._ac_label.setText(ac_text)
        self._ac_label.setStyleSheet(f"color: {color};")

        # 위험 수준
        risk_text = self.RISK_LABELS.get(result.risk_level, result.risk_level)
        self._risk_label.setText(risk_text)
        self._risk_label.setStyleSheet(f"color: {color};")

        # 코드 상세
        self._back_code_label.setText(str(result.back_code))
        self._back_desc_label.setText(self.BACK_DESCRIPTIONS.get(result.back_code, ''))

        self._arms_code_label.setText(str(result.arms_code))
        self._arms_desc_label.setText(self.ARMS_DESCRIPTIONS.get(result.arms_code, ''))

        self._legs_code_label.setText(str(result.legs_code))
        self._legs_desc_label.setText(self.LEGS_DESCRIPTIONS.get(result.legs_code, ''))

        load_descriptions = {1: '10kg 미만', 2: '10-20kg', 3: '20kg 초과'}
        self._load_code_label.setText(str(result.load_code))
        self._load_desc_label.setText(load_descriptions.get(result.load_code, ''))

    def _on_manual_input_changed(self):
        """수동 입력 변경 시 시그널 발생"""
        self.manual_input_changed.emit()

    def get_load_code(self) -> int:
        """현재 선택된 하중 코드 반환"""
        return self._load_combo.currentData()

    def is_sitting_checked(self) -> bool:
        """앉음 체크박스 상태 반환"""
        return self._sitting_checkbox.isChecked()

    def clear(self):
        """초기화"""
        self._posture_code_label.setText("–,–,–,–")
        self._posture_code_label.setStyleSheet("")
        self._ac_label.setText("–")
        self._ac_label.setStyleSheet("")
        self._risk_label.setText("대기 중")
        self._risk_label.setStyleSheet("")
        self._back_code_label.setText("–")
        self._back_desc_label.setText("")
        self._arms_code_label.setText("–")
        self._arms_desc_label.setText("")
        self._legs_code_label.setText("–")
        self._legs_desc_label.setText("")
        self._load_code_label.setText("–")
        self._load_desc_label.setText("")
