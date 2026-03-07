"""설정 다이얼로그 모듈"""

import os
import urllib.request
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QFileDialog, QDialogButtonBox, QFormLayout, QComboBox,
    QProgressDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import TYPE_CHECKING

from ..license import LicenseManager

if TYPE_CHECKING:
    from ..utils.config import Config


class ModelDownloadThread(QThread):
    """모델 다운로드 스레드"""
    progress = pyqtSignal(int)  # 퍼센트 (0~100)
    finished = pyqtSignal(bool, str)  # 성공여부, 메시지

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
                if total_size > 0:
                    percent = int(block_num * block_size * 100 / total_size)
                    self.progress.emit(min(percent, 100))

            urllib.request.urlretrieve(self._url, self._save_path, reporthook)
            if not self._cancelled:
                self.finished.emit(True, "다운로드 완료")
        except InterruptedError:
            # 취소 시 불완전 파일 삭제
            if os.path.exists(self._save_path):
                os.remove(self._save_path)
            self.finished.emit(False, "다운로드가 취소되었습니다.")
        except Exception as e:
            if os.path.exists(self._save_path):
                os.remove(self._save_path)
            self.finished.emit(False, f"다운로드 실패: {e}")


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

        info = PoseDetector.MODELS[model_type]
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(PoseDetector.__module__.replace('.', '/') + '.py')),
            info['filename']
        )
        # 실제 경로 계산
        import inspect
        model_dir = os.path.dirname(inspect.getfile(PoseDetector))
        model_path = os.path.join(model_dir, info['filename'])

        if os.path.exists(model_path):
            # 이미 다운로드됨
            self._config.set("detection.model_type", model_type)
            self._config.save()
            QMessageBox.information(
                self, "모델 변경",
                f"감지 모델이 '{model_type.upper()}'로 변경되었습니다.\n재시작 후 적용됩니다."
            )
            self.accept()
            return

        # 다운로드 필요
        self._download_thread = ModelDownloadThread(info['url'], model_path)

        progress = QProgressDialog(
            f"'{model_type.upper()}' 모델 다운로드 중...",
            "취소", 0, 100, self
        )
        progress.setWindowTitle("모델 다운로드")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        self._progress_dialog = progress

        def on_progress(percent):
            progress.setValue(percent)

        def on_finished(success, message):
            progress.close()
            self._download_thread.deleteLater()
            if success:
                self._config.set("detection.model_type", model_type)
                self._config.save()
                QMessageBox.information(
                    self, "모델 다운로드 완료",
                    f"'{model_type.upper()}' 모델 다운로드가 완료되었습니다.\n재시작 후 적용됩니다."
                )
                self.accept()
            else:
                # 콤보박스를 원래 값으로 복원
                idx = self._model_combo.findData(self._original_model_type)
                if idx >= 0:
                    self._model_combo.setCurrentIndex(idx)
                QMessageBox.warning(self, "모델 다운로드 실패", message)

        progress.canceled.connect(self._download_thread.cancel)
        self._download_thread.progress.connect(on_progress)
        self._download_thread.finished.connect(on_finished)
        self._download_thread.start()
