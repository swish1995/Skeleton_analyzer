"""설정 다이얼로그 모듈"""

import os
import urllib.request
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QFileDialog, QDialogButtonBox, QFormLayout, QComboBox,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import TYPE_CHECKING

from ..license import LicenseManager

if TYPE_CHECKING:
    from ..utils.config import Config


class ModelDownloadThread(QThread):
    """모델 다운로드 스레드"""
    progress = pyqtSignal(int, int)  # (current_bytes, total_bytes)
    download_finished = pyqtSignal(bool, str)  # 성공여부, 메시지

    def __init__(self, url: str, save_path: str):
        super().__init__()
        self._url = url
        self._save_path = save_path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            def reporthook(block_num, block_size, total_size):
                if self._cancelled:
                    raise InterruptedError("다운로드 취소됨")
                downloaded = block_num * block_size
                self.progress.emit(downloaded, total_size)

            urllib.request.urlretrieve(self._url, self._save_path, reporthook)
            if not self._cancelled:
                self.download_finished.emit(True, "다운로드 완료")
        except InterruptedError:
            if os.path.exists(self._save_path):
                os.remove(self._save_path)
            self.download_finished.emit(False, "다운로드가 취소되었습니다.")
        except Exception as e:
            if os.path.exists(self._save_path):
                os.remove(self._save_path)
            self.download_finished.emit(False, f"다운로드 실패: {e}")


class ModelDownloadDialog(QDialog):
    """모델 다운로드 진행 다이얼로그"""

    def __init__(self, model_name: str, url: str, save_path: str, parent=None):
        super().__init__(parent)
        self._model_name = model_name
        self._url = url
        self._save_path = save_path
        self._worker = None
        self._success = False

        self._init_ui()
        self._apply_style()

    def _init_ui(self):
        self.setWindowTitle("모델 다운로드")
        self.setModal(True)
        self.setFixedSize(380, 180)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowCloseButtonHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 제목
        self._title_label = QLabel(f"'{self._model_name}' 모델 다운로드 중...")
        self._title_label.setObjectName("titleLabel")
        layout.addWidget(self._title_label)

        # 프로그레스 바
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(0)  # indeterminate로 시작
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setFixedHeight(22)
        layout.addWidget(self._progress_bar)

        # 상태 메시지
        self._status_label = QLabel("연결 중...")
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        layout.addStretch()

        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._action_btn = QPushButton("취소")
        self._action_btn.setObjectName("cancelButton")
        self._action_btn.setFixedSize(100, 36)
        self._action_btn.clicked.connect(self._on_action)
        btn_layout.addWidget(self._action_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLabel#titleLabel {
                font-size: 15px;
                font-weight: bold;
                color: #ffffff;
            }
            QLabel#statusLabel {
                font-size: 12px;
                color: #aaaaaa;
            }
            QProgressBar {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                text-align: center;
                color: #e0e0e0;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a9eff, stop:1 #5aaeFF
                );
                border-radius: 3px;
            }
            QPushButton#cancelButton {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 16px;
            }
            QPushButton#cancelButton:hover {
                background-color: #4a4a4a;
                border-color: #5a5a5a;
            }
            QPushButton#cancelButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton#confirmBtn {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 6px 16px;
            }
            QPushButton#confirmBtn:hover {
                background-color: #5aaeFF;
            }
            QPushButton#confirmBtn:pressed {
                background-color: #3a8eef;
            }
        """)

    @staticmethod
    def _format_size(bytes_val: int) -> str:
        if bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.0f} KB"
        return f"{bytes_val / (1024 * 1024):.1f} MB"

    def start(self):
        """다운로드 시작 - exec() 전에 호출"""
        self._worker = ModelDownloadThread(self._url, self._save_path)
        self._worker.progress.connect(self._on_progress)
        self._worker.download_finished.connect(self._on_finished)
        self._worker.start()

    @property
    def success(self) -> bool:
        return self._success

    def _on_progress(self, downloaded: int, total: int):
        if total > 0:
            self._progress_bar.setMaximum(100)
            percent = int(downloaded * 100 / total)
            self._progress_bar.setValue(min(percent, 100))
            self._status_label.setText(
                f"{self._format_size(downloaded)} / {self._format_size(total)}"
            )
        else:
            self._progress_bar.setMaximum(0)

    def _on_finished(self, success: bool, message: str):
        self._success = success
        if success:
            self._progress_bar.setMaximum(100)
            self._progress_bar.setValue(100)
            self._title_label.setText("다운로드 완료!")
            self._status_label.setText(f"'{self._model_name}' 모델이 준비되었습니다. 재시작 후 적용됩니다.")
        else:
            self._progress_bar.setMaximum(100)
            self._progress_bar.setValue(0)
            self._title_label.setText("다운로드 실패")
            self._status_label.setText(message)

        self._action_btn.setText("확인")
        self._action_btn.setObjectName("confirmBtn")
        self._action_btn.setStyle(self._action_btn.style())  # 스타일 갱신
        self._action_btn.setFocus()

    def _on_action(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._action_btn.setEnabled(False)
            self._action_btn.setText("취소 중...")
        else:
            if self._success:
                self.accept()
            else:
                self.reject()

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)


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

        # 감지 모델 설정 그룹
        model_group = QGroupBox("포즈 감지")
        model_layout = QFormLayout(model_group)

        self._model_combo = QComboBox()
        self._model_combo.addItem("Lite (빠름, 보통 정확도)", "lite")
        self._model_combo.addItem("Full (보통, 좋은 정확도)", "full")
        self._model_combo.addItem("Heavy (느림, 최고 정확도)", "heavy")

        is_licensed = LicenseManager.instance().check_feature('model_change')
        self._model_combo.setEnabled(is_licensed)

        self._model_note = QLabel(
            "※ 모델 변경은 등록 버전에서 사용할 수 있습니다." if not is_licensed
            else "※ 모델 변경 시 자동 다운로드됩니다. 적용은 재시작 후."
        )
        self._model_note.setStyleSheet("color: #888; font-size: 11px;")

        model_layout.addRow("감지 모델:", self._model_combo)
        model_layout.addRow("", self._model_note)

        layout.addWidget(model_group)

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

        model_type = self._config.get("detection.model_type", "lite")
        idx = self._model_combo.findData(model_type)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)
        self._original_model_type = model_type

    def _save_and_accept(self):
        """설정 저장 후 다이얼로그 닫기"""
        # 디렉토리 설정
        self._config.set("directories.video_open", self._video_open_edit.text())
        self._config.set("directories.capture_save", self._capture_save_edit.text() or "captures")
        self._config.set("directories.export", self._export_edit.text())

        # 이미지 관리 설정
        self._config.set("images.auto_delete_on_row_delete", self._auto_delete_checkbox.isChecked())
        self._config.set("images.confirm_before_delete", self._confirm_delete_checkbox.isChecked())

        # 감지 모델 설정 (등록 시에만)
        if self._model_combo.isEnabled():
            new_model = self._model_combo.currentData()
            if new_model != self._original_model_type:
                self._download_model_if_needed(new_model)
                return  # 다운로드 완료 콜백에서 저장/닫기 처리

        self._config.save()
        self.accept()

    def _download_model_if_needed(self, model_type: str):
        """모델 파일이 없으면 다운로드"""
        from ..core.pose_detector import PoseDetector
        import inspect

        info = PoseDetector.MODELS[model_type]
        model_dir = os.path.dirname(inspect.getfile(PoseDetector))
        model_path = os.path.join(model_dir, info['filename'])
        model_name = model_type.upper()

        if os.path.exists(model_path):
            # 이미 다운로드됨
            self._config.set("detection.model_type", model_type)
            self._config.save()
            QMessageBox.information(
                self, "모델 변경",
                f"감지 모델이 '{model_name}'로 변경되었습니다.\n재시작 후 적용됩니다."
            )
            self.accept()
            return

        # 다운로드 다이얼로그
        dialog = ModelDownloadDialog(model_name, info['url'], model_path, self)
        dialog.start()
        result = dialog.exec()

        if dialog.success:
            self._config.set("detection.model_type", model_type)
            self._config.save()
            self.accept()
        else:
            # 콤보박스를 원래 값으로 복원
            idx = self._model_combo.findData(self._original_model_type)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)
