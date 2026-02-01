"""라이센스 제한 오버레이 위젯

유료 기능에 대해 미등록 사용자에게 표시되는 오버레이입니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class LicenseOverlay(QWidget):
    """라이센스 제한 오버레이 위젯

    부모 위젯 위에 반투명 오버레이로 표시되며,
    라이센스 등록 다이얼로그를 열 수 있는 버튼을 제공합니다.
    """

    # 라이센스 등록 버튼 클릭 시그널
    register_clicked = pyqtSignal()

    def __init__(self, parent=None, feature_name: str = "이 기능"):
        super().__init__(parent)
        self._feature_name = feature_name
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        # 부모 위젯 전체를 덮도록 설정
        self.setAutoFillBackground(True)

        # 반투명 배경
        self.setStyleSheet("""
            LicenseOverlay {
                background-color: rgba(0, 0, 0, 0.85);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 중앙 컨테이너
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border-radius: 12px;
            }
        """)
        container.setFixedSize(360, 200)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(32, 28, 32, 28)
        container_layout.setSpacing(16)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 잠금 아이콘
        icon_label = QLabel("🔒")
        icon_font = QFont()
        icon_font.setPointSize(36)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        container_layout.addWidget(icon_label)

        # 메시지
        message_label = QLabel(f"{self._feature_name}은(는)\n등록 버전에서 사용할 수 있습니다")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            color: #e0e0e0;
            font-size: 14px;
            background: transparent;
        """)
        message_label.setWordWrap(True)
        container_layout.addWidget(message_label)

        # 등록 버튼
        register_btn = QPushButton("라이센스 등록")
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5aaeFF;
            }
            QPushButton:pressed {
                background-color: #3a8eef;
            }
        """)
        register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        register_btn.clicked.connect(self._on_register_clicked)
        container_layout.addWidget(register_btn)

        layout.addWidget(container)

        # 초기에는 숨김
        self.hide()

    def _on_register_clicked(self):
        """등록 버튼 클릭"""
        self.register_clicked.emit()

    def showEvent(self, event):
        """표시 이벤트 - 부모 크기에 맞춤"""
        super().showEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())

    def resizeEvent(self, event):
        """크기 변경 이벤트"""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())
