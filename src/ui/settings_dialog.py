"""설정 다이얼로그 모듈"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QFileDialog, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..utils.config import Config


class SettingsDialog(QDialog):
    """환경 설정 다이얼로그"""

    def __init__(self, config: "Config", parent=None):
        super().__init__(parent)
        self._config = config
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("설정")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 디렉토리 설정 그룹
        dir_group = QGroupBox("디렉토리 설정")
        dir_layout = QFormLayout(dir_group)

        # 동영상 열기 디렉토리
        self._video_open_edit = QLineEdit()
        self._video_open_edit.setPlaceholderText("기본 디렉토리 (비워두면 현재 디렉토리)")
        video_open_btn = QPushButton("찾아보기...")
        video_open_btn.clicked.connect(lambda: self._browse_directory(self._video_open_edit))
        video_open_row = QHBoxLayout()
        video_open_row.addWidget(self._video_open_edit)
        video_open_row.addWidget(video_open_btn)
        dir_layout.addRow("동영상 열기:", video_open_row)

        # 캡처 저장 디렉토리
        self._capture_save_edit = QLineEdit()
        self._capture_save_edit.setPlaceholderText("기본값: captures")
        capture_save_btn = QPushButton("찾아보기...")
        capture_save_btn.clicked.connect(lambda: self._browse_directory(self._capture_save_edit))
        capture_save_row = QHBoxLayout()
        capture_save_row.addWidget(self._capture_save_edit)
        capture_save_row.addWidget(capture_save_btn)
        dir_layout.addRow("캡처 저장:", capture_save_row)

        # 내보내기 디렉토리
        self._export_edit = QLineEdit()
        self._export_edit.setPlaceholderText("기본 디렉토리 (비워두면 현재 디렉토리)")
        export_btn = QPushButton("찾아보기...")
        export_btn.clicked.connect(lambda: self._browse_directory(self._export_edit))
        export_row = QHBoxLayout()
        export_row.addWidget(self._export_edit)
        export_row.addWidget(export_btn)
        dir_layout.addRow("내보내기:", export_row)

        layout.addWidget(dir_group)

        # 이미지 관리 설정 그룹
        image_group = QGroupBox("이미지 관리")
        image_layout = QVBoxLayout(image_group)

        self._auto_delete_checkbox = QCheckBox("행 삭제 시 이미지도 자동 삭제")
        self._auto_delete_checkbox.setToolTip(
            "스프레드시트에서 행을 삭제할 때 연결된 캡처 이미지도 함께 삭제합니다."
        )
        image_layout.addWidget(self._auto_delete_checkbox)

        self._confirm_delete_checkbox = QCheckBox("이미지 삭제 전 확인")
        self._confirm_delete_checkbox.setToolTip(
            "이미지를 삭제하기 전에 확인 다이얼로그를 표시합니다."
        )
        image_layout.addWidget(self._confirm_delete_checkbox)

        layout.addWidget(image_group)

        # 버튼
        button_box = QDialogButtonBox()
        ok_btn = button_box.addButton("확인", QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_btn = button_box.addButton("취소", QDialogButtonBox.ButtonRole.RejectRole)
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _browse_directory(self, line_edit: QLineEdit):
        """디렉토리 선택 다이얼로그"""
        current_path = line_edit.text() or ""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "디렉토리 선택",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            line_edit.setText(dir_path)

    def _load_settings(self):
        """설정 로드"""
        self._video_open_edit.setText(
            self._config.get("directories.video_open", "")
        )
        self._capture_save_edit.setText(
            self._config.get("directories.capture_save", "")
        )
        self._export_edit.setText(
            self._config.get("directories.export", "")
        )

        self._auto_delete_checkbox.setChecked(
            self._config.get("images.auto_delete_on_row_delete", True)
        )
        self._confirm_delete_checkbox.setChecked(
            self._config.get("images.confirm_before_delete", True)
        )

    def _save_and_accept(self):
        """설정 저장 후 다이얼로그 닫기"""
        # 디렉토리 설정
        self._config.set("directories.video_open", self._video_open_edit.text())
        self._config.set("directories.capture_save", self._capture_save_edit.text())
        self._config.set("directories.export", self._export_edit.text())

        # 이미지 관리 설정
        self._config.set("images.auto_delete_on_row_delete", self._auto_delete_checkbox.isChecked())
        self._config.set("images.confirm_before_delete", self._confirm_delete_checkbox.isChecked())

        self._config.save()
        self.accept()
