"""앱 다크 테마에 맞는 커스텀 다이얼로그"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt


class CustomDialog(QDialog):
    """다크 테마 커스텀 다이얼로그

    사용 예:
        # Yes/No 확인
        if CustomDialog.ask(self, "제목", "메시지"):
            ...

        # 정보 알림
        CustomDialog.info(self, "제목", "메시지")

        # 경고 알림
        CustomDialog.warning(self, "제목", "메시지")

        # 오류 알림
        CustomDialog.error(self, "제목", "메시지")

        # 3버튼 (저장/삭제/취소)
        result = CustomDialog.ask_save(self, "제목", "메시지")
        # result: "save", "discard", "cancel"

        # 커스텀 버튼
        result = CustomDialog.custom(self, "제목", "메시지",
            buttons=[("버튼1", "btn1"), ("버튼2", "btn2")],
            default_index=0, primary_index=1)
        # result: "btn1" 또는 "btn2" 또는 None(닫기)
    """

    # 결과값 상수
    SAVE = "save"
    DISCARD = "discard"
    CANCEL = "cancel"

    def __init__(self, title: str, message: str, buttons: list = None,
                 default_index: int = -1, primary_index: int = -1,
                 parent=None):
        """
        Args:
            title: 다이얼로그 제목
            message: 표시할 메시지
            buttons: [(텍스트, 결과값), ...] 리스트
            default_index: 기본 포커스 버튼 인덱스
            primary_index: 강조(파란색) 버튼 인덱스
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowCloseButtonHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._result_value = None
        self._buttons_data = buttons or [("확인", "ok")]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(16)

        # 메시지
        msg_label = QLabel(message)
        msg_label.setObjectName("cdMessage")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        layout.addStretch()

        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._btn_widgets = []
        for i, (text, value) in enumerate(self._buttons_data):
            btn = QPushButton(text)
            btn.setFixedSize(max(90, len(text) * 12 + 24), 34)

            if i == primary_index:
                btn.setObjectName("cdPrimaryBtn")
            else:
                btn.setObjectName("cdNormalBtn")

            if i == default_index:
                btn.setDefault(True)

            btn.clicked.connect(lambda checked, v=value: self._on_click(v))
            btn_layout.addWidget(btn)
            self._btn_widgets.append(btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 크기 계산
        line_count = message.count('\n') + 1
        height = max(160, 100 + line_count * 20)
        total_btn_width = sum(b.width() for b in self._btn_widgets) + 16 * len(self._btn_widgets)
        width = max(340, total_btn_width + 80)
        self.setFixedSize(width, min(height, 400))

        self._apply_style()

    def _on_click(self, value):
        self._result_value = value
        if value in (self.CANCEL, None):
            self.reject()
        else:
            self.accept()

    @property
    def result_value(self):
        return self._result_value

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel#cdMessage {
                color: #e0e0e0;
                font-size: 13px;
            }
            QPushButton#cdNormalBtn {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 16px;
            }
            QPushButton#cdNormalBtn:hover {
                background-color: #4a4a4a;
                border-color: #5a5a5a;
            }
            QPushButton#cdNormalBtn:pressed {
                background-color: #2a2a2a;
            }
            QPushButton#cdPrimaryBtn {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 6px 16px;
            }
            QPushButton#cdPrimaryBtn:hover {
                background-color: #5aaeFF;
            }
            QPushButton#cdPrimaryBtn:pressed {
                background-color: #3a8eef;
            }
        """)

    # === 편의 정적 메서드 ===

    @staticmethod
    def ask(parent, title: str, message: str,
            yes_text: str = "예", no_text: str = "아니오") -> bool:
        """Yes/No 확인 다이얼로그. Yes 클릭 시 True 반환."""
        dlg = CustomDialog(
            title, message,
            buttons=[(no_text, "no"), (yes_text, "yes")],
            default_index=0, primary_index=1,
            parent=parent
        )
        dlg.exec()
        return dlg.result_value == "yes"

    @staticmethod
    def ask_save(parent, title: str, message: str,
                 save_text: str = "저장", discard_text: str = "저장 안 함",
                 cancel_text: str = "취소") -> str:
        """저장/삭제/취소 3버튼 다이얼로그. "save"/"discard"/"cancel" 반환."""
        dlg = CustomDialog(
            title, message,
            buttons=[
                (cancel_text, CustomDialog.CANCEL),
                (discard_text, CustomDialog.DISCARD),
                (save_text, CustomDialog.SAVE),
            ],
            default_index=2, primary_index=2,
            parent=parent
        )
        dlg.exec()
        return dlg.result_value or CustomDialog.CANCEL

    @staticmethod
    def info(parent, title: str, message: str):
        """정보 알림 다이얼로그."""
        dlg = CustomDialog(
            title, message,
            buttons=[("확인", "ok")],
            default_index=0, primary_index=0,
            parent=parent
        )
        dlg.exec()

    @staticmethod
    def warning(parent, title: str, message: str):
        """경고 알림 다이얼로그."""
        dlg = CustomDialog(
            title, message,
            buttons=[("확인", "ok")],
            default_index=0, primary_index=0,
            parent=parent
        )
        dlg.exec()

    @staticmethod
    def error(parent, title: str, message: str):
        """오류 알림 다이얼로그."""
        dlg = CustomDialog(
            title, message,
            buttons=[("확인", "ok")],
            default_index=0, primary_index=0,
            parent=parent
        )
        dlg.exec()

    @staticmethod
    def custom(parent, title: str, message: str,
               buttons: list, default_index: int = -1,
               primary_index: int = -1) -> str:
        """커스텀 버튼 다이얼로그. 클릭한 버튼의 결과값 반환, 닫기 시 None."""
        dlg = CustomDialog(
            title, message,
            buttons=buttons,
            default_index=default_index,
            primary_index=primary_index,
            parent=parent
        )
        dlg.exec()
        return dlg.result_value
