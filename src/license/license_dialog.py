"""라이센스 등록 다이얼로그 모듈"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame,
    QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .hardware_id import get_hardware_id
from .license_manager import LicenseManager, LicenseMode
from .license_validator import ValidationResult


class LicenseDialog(QDialog):
    """라이센스 등록 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = LicenseManager.instance()
        self._init_ui()
        self._update_state()

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("라이센스 등록")
        self.setFixedSize(500, 420)
        self.setModal(True)

        # 다크 테마 스타일
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 14px;
                font-family: 'SF Mono', 'Menlo', monospace;
            }
            QLineEdit:focus {
                border-color: #4a9eff;
            }
            QLineEdit:read-only {
                background-color: #252525;
                color: #888888;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton#primary {
                background-color: #4a9eff;
                color: white;
            }
            QPushButton#primary:hover {
                background-color: #5aaeFF;
            }
            QPushButton#primary:pressed {
                background-color: #3a8eef;
            }
            QPushButton#primary:disabled {
                background-color: #3a3a3a;
                color: #666666;
            }
            QFrame#separator {
                background-color: #3a3a3a;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 타이틀
        title_label = QLabel("라이센스 등록")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 상태 표시
        self._status_label = QLabel()
        self._status_label.setStyleSheet("color: #888888; font-size: 13px;")
        layout.addWidget(self._status_label)

        # 구분선
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # 하드웨어 ID 섹션
        hw_label = QLabel("하드웨어 ID")
        hw_label.setStyleSheet("font-weight: 500; margin-top: 8px;")
        layout.addWidget(hw_label)

        hw_layout = QHBoxLayout()
        hw_layout.setSpacing(8)

        self._hw_id_edit = QLineEdit()
        self._hw_id_edit.setReadOnly(True)
        self._hw_id_edit.setText(get_hardware_id())
        hw_layout.addWidget(self._hw_id_edit)

        copy_btn = QPushButton("복사")
        copy_btn.setFixedWidth(60)
        copy_btn.clicked.connect(self._copy_hardware_id)
        hw_layout.addWidget(copy_btn)

        layout.addLayout(hw_layout)

        hw_desc = QLabel("라이센스 발급 시 이 ID를 제공해 주세요.")
        hw_desc.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(hw_desc)

        # 개발자 연락처
        contact_label = QLabel("라이센스 문의: swish1995@gmail.com")
        contact_label.setStyleSheet("color: #4a9eff; font-size: 12px; margin-top: 4px;")
        layout.addWidget(contact_label)

        # 라이센스 키 입력 섹션
        key_label = QLabel("라이센스 키")
        key_label.setStyleSheet("font-weight: 500; margin-top: 16px;")
        layout.addWidget(key_label)

        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self._key_edit.textChanged.connect(self._on_key_changed)
        layout.addWidget(self._key_edit)

        # 버튼 영역
        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        button_layout.addStretch()

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self._register_btn = QPushButton("등록")
        self._register_btn.setObjectName("primary")
        self._register_btn.clicked.connect(self._register)
        button_layout.addWidget(self._register_btn)

        layout.addLayout(button_layout)

    def _update_state(self):
        """상태 업데이트"""
        if self._manager.license_mode == LicenseMode.DEV:
            self._status_label.setText("🔧 개발 모드 - 모든 기능 활성화")
            self._status_label.setStyleSheet("color: #ffa500; font-size: 13px;")
            self._key_edit.setEnabled(False)
            self._register_btn.setEnabled(False)
        elif self._manager.license_mode == LicenseMode.LICENSED:
            self._status_label.setText("🔓 강제 등록 모드")
            self._status_label.setStyleSheet("color: #4a9eff; font-size: 13px;")
            self._key_edit.setEnabled(False)
            self._register_btn.setEnabled(False)
        elif self._manager.is_licensed:
            self._status_label.setText("✅ 등록됨")
            self._status_label.setStyleSheet("color: #4ade80; font-size: 13px;")
            self._key_edit.setText(self._manager.license_key or "")
            self._key_edit.setEnabled(False)
            self._register_btn.setEnabled(False)
        else:
            self._status_label.setText("⚠️ 미등록 - 일부 기능이 제한됩니다")
            self._status_label.setStyleSheet("color: #f87171; font-size: 13px;")
            self._key_edit.setEnabled(True)
            self._register_btn.setEnabled(False)

    def _on_key_changed(self, text: str):
        """키 입력 변경"""
        # 형식 체크: XXXX-XXXX-XXXX-XXXX
        normalized = text.strip().upper()
        is_valid_format = len(normalized) == 19 and normalized.count('-') == 3
        self._register_btn.setEnabled(is_valid_format)

    def _copy_hardware_id(self):
        """하드웨어 ID 복사"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._hw_id_edit.text())

        # 복사 완료 피드백 (버튼 텍스트 변경)
        sender = self.sender()
        if isinstance(sender, QPushButton):
            original_text = sender.text()
            sender.setText("✓")
            sender.setStyleSheet("background-color: #4ade80; color: white;")

            # 1초 후 원래대로 복구
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self._restore_copy_button(sender, original_text))

    def _restore_copy_button(self, button: QPushButton, text: str):
        """복사 버튼 복구"""
        button.setText(text)
        button.setStyleSheet("")

    def _register(self):
        """라이센스 등록"""
        key = self._key_edit.text().strip()

        if self._manager.register(key):
            QMessageBox.information(
                self,
                "등록 완료",
                "라이센스가 성공적으로 등록되었습니다.\n모든 기능을 사용할 수 있습니다."
            )
            self._update_state()
            self.accept()
        else:
            # 실패 원인 분석
            from .license_validator import LicenseValidator
            validator = LicenseValidator()
            result = validator.validate(key, get_hardware_id())

            if result == ValidationResult.INVALID_FORMAT:
                message = "라이센스 키 형식이 올바르지 않습니다.\nXXXX-XXXX-XXXX-XXXX 형식으로 입력해 주세요."
            elif result == ValidationResult.INVALID_CHECKSUM:
                message = "유효하지 않은 라이센스 키입니다.\n키를 다시 확인해 주세요."
            elif result == ValidationResult.HARDWARE_MISMATCH:
                message = "이 라이센스 키는 다른 컴퓨터용입니다.\n하드웨어 ID를 확인해 주세요."
            else:
                message = "라이센스 등록에 실패했습니다."

            QMessageBox.warning(self, "등록 실패", message)
