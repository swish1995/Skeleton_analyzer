"""파일 로딩 진행 모달 다이얼로그

동영상/폴더/압축파일 로드 시 진행률을 표시합니다.
"""
import zipfile
from pathlib import Path
from typing import Optional, List

import numpy as np

from src.utils.cv_unicode import VideoCapture as CvVideoCapture

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ..core.image_slide_player import ImageSlidePlayer, SUPPORTED_IMAGE_EXTENSIONS, _natural_sort_key


class LoadWorker(QThread):
    """파일 로딩 워커 스레드

    3가지 모드를 지원합니다:
    - video: 동영상 파일 로드
    - folder: 이미지 폴더 스캔
    - archive: 압축 파일 해제 + 이미지 스캔
    """

    progress = pyqtSignal(int, int)        # (current, total)
    status_changed = pyqtSignal(str)        # 상태 메시지
    finished_ok = pyqtSignal(object)        # 성공 시 결과 데이터
    finished_err = pyqtSignal(str)          # 실패 시 에러 메시지

    def __init__(self, mode: str, path: str, parent=None):
        super().__init__(parent)
        self._mode = mode
        self._path = path
        # 결과 저장용
        self.image_paths: List[Path] = []
        self.temp_dir: Optional[Path] = None

    def run(self):
        try:
            if self._mode == 'video':
                self._load_video()
            elif self._mode == 'folder':
                self._load_folder()
            elif self._mode == 'archive':
                self._load_archive()
        except Exception as e:
            self.finished_err.emit(str(e))

    def _load_video(self):
        """동영상 로드 (cv2.VideoCapture로 검증)"""
        self.status_changed.emit("동영상 파일 로드 중...")
        self.progress.emit(0, 0)  # indeterminate

        cap = CvVideoCapture(self._path)
        if not cap.isOpened():
            cap.release()
            self.finished_err.emit("동영상 파일을 열 수 없습니다.")
            return

        cap.release()
        self.finished_ok.emit(self._path)

    def _load_folder(self):
        """이미지 폴더 스캔"""
        self.status_changed.emit("이미지 파일 검색 중...")
        self.progress.emit(0, 0)

        folder = Path(self._path)
        if not folder.exists() or not folder.is_dir():
            self.finished_err.emit("폴더가 존재하지 않습니다.")
            return

        # 1뎁스 파일 목록 수집
        all_files = list(folder.iterdir())
        total = len(all_files)

        images = []
        for i, f in enumerate(all_files):
            if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                images.append(f)
            if total > 0:
                self.progress.emit(i + 1, total)

        if not images:
            self.finished_err.emit("이미지 파일을 찾을 수 없습니다.")
            return

        images.sort(key=_natural_sort_key)
        self.image_paths = images
        self.status_changed.emit(f"{len(images)}개 이미지 발견")
        self.finished_ok.emit(self._path)

    def _load_archive(self):
        """압축 파일 해제 + 이미지 스캔"""
        archive = Path(self._path)
        if not archive.exists() or not zipfile.is_zipfile(archive):
            self.finished_err.emit("유효하지 않은 압축 파일입니다.")
            return

        import shutil

        temp_dir = Path(ImageSlidePlayer.TEMP_BASE_DIR) / archive.stem
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(archive, 'r') as zf:
                entries = zf.namelist()
                total = len(entries)
                self.status_changed.emit("압축 해제 중...")

                for i, entry in enumerate(entries):
                    zf.extract(entry, temp_dir)
                    self.progress.emit(i + 1, total)

            # 이미지 스캔
            self.status_changed.emit("이미지 파일 검색 중...")
            images = []
            for f in temp_dir.rglob('*'):
                if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                    images.append(f)

            if not images:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.finished_err.emit("압축 파일에 이미지가 없습니다.")
                return

            images.sort(key=_natural_sort_key)
            self.image_paths = images
            self.temp_dir = temp_dir
            self.status_changed.emit(f"{len(images)}개 이미지 발견")
            self.finished_ok.emit(self._path)

        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            self.finished_err.emit(f"압축 해제 실패: {e}")


class LoadingDialog(QDialog):
    """파일 로딩 진행 모달 다이얼로그

    AnalysisProgressDialog 스타일을 따른 다크 테마 모달입니다.
    """

    def __init__(self, mode: str, path: str, parent=None):
        """
        Args:
            mode: 'video', 'folder', 'archive'
            path: 파일/폴더 경로
        """
        super().__init__(parent)
        self._mode = mode
        self._path = path
        self._worker: Optional[LoadWorker] = None
        self._success = False
        self._error_msg = ""

        self._init_ui()
        self._apply_style()

    def _init_ui(self):
        titles = {
            'video': '동영상 로드 중...',
            'folder': '이미지 폴더 로드 중...',
            'archive': '압축 파일 로드 중...',
        }

        self.setWindowTitle("파일 로드")
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
        self._title_label = QLabel(titles.get(self._mode, '로드 중...'))
        self._title_label.setObjectName("titleLabel")
        layout.addWidget(self._title_label)

        # 프로그레스 바
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(0)  # indeterminate 모드로 시작
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setFixedHeight(22)
        layout.addWidget(self._progress_bar)

        # 상태 메시지
        self._status_label = QLabel("준비 중...")
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        layout.addStretch()

        # 확인 버튼 (완료 후 표시)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._confirm_btn = QPushButton("확인")
        self._confirm_btn.setObjectName("confirmBtn")
        self._confirm_btn.setFixedSize(100, 36)
        self._confirm_btn.hide()
        self._confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self._confirm_btn)
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

    def start(self):
        """로딩 시작 - exec() 전에 호출"""
        self._worker = LoadWorker(self._mode, self._path)
        self._worker.progress.connect(self._on_progress)
        self._worker.status_changed.connect(self._on_status)
        self._worker.finished_ok.connect(self._on_success)
        self._worker.finished_err.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    @property
    def success(self) -> bool:
        return self._success

    @property
    def error_msg(self) -> str:
        return self._error_msg

    @property
    def worker(self) -> Optional[LoadWorker]:
        return self._worker

    def _on_progress(self, current: int, total: int):
        if total <= 0:
            # indeterminate 모드
            self._progress_bar.setMaximum(0)
        else:
            self._progress_bar.setMaximum(total)
            self._progress_bar.setValue(current)

    def _on_status(self, msg: str):
        self._status_label.setText(msg)

    def _on_success(self, result):
        self._success = True

    def _on_error(self, msg: str):
        self._success = False
        self._error_msg = msg

    def _on_worker_finished(self):
        self._confirm_btn.show()
        self._confirm_btn.setFocus()

        if self._success:
            self._progress_bar.setMaximum(100)
            self._progress_bar.setValue(100)

            count_msg = ""
            if self._worker and self._worker.image_paths:
                count_msg = f" ({len(self._worker.image_paths)}개 이미지)"

            titles = {
                'video': '동영상 로드 완료!',
                'folder': f'이미지 폴더 로드 완료!{count_msg}',
                'archive': f'압축 파일 로드 완료!{count_msg}',
            }
            self._title_label.setText(titles.get(self._mode, '로드 완료!'))
            self._status_label.hide()
        else:
            self._progress_bar.setMaximum(100)
            self._progress_bar.setValue(0)
            self._title_label.setText("로드 실패")
            self._status_label.setText(self._error_msg or "알 수 없는 오류")

    def _on_confirm(self):
        if self._success:
            self.accept()
        else:
            self.reject()

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)
