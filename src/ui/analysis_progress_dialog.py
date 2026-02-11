"""분석 진행 모달 다이얼로그"""
import time

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QHBoxLayout, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer

from src.core.analysis_worker import AnalysisWorker
from src.core.movement_analyzer import MovementAnalysisResult


class AnalysisProgressDialog(QDialog):
    """동영상 분석 진행 상태를 보여주는 모달 다이얼로그"""

    def __init__(self, video_path: str, sample_interval: int = 1,
                 resume_state: dict = None, resume_frame: int = 0,
                 resume_skipped: int = 0, resume_elapsed: float = 0.0,
                 parent=None):
        super().__init__(parent)
        self._video_path = video_path
        self._sample_interval = sample_interval
        self._resume_state = resume_state
        self._resume_frame = resume_frame
        self._resume_skipped = resume_skipped
        self._resume_elapsed = resume_elapsed
        self._result: MovementAnalysisResult = None
        self._worker: AnalysisWorker = None
        self._start_time = 0.0
        self._skipped_frames = 0
        self._finished = False

        # 취소 시 부분 상태
        self._partial_state = None

        self._init_ui()
        self._apply_style()

    def _init_ui(self):
        self.setWindowTitle("동영상 분석")
        self.setModal(True)
        self.setFixedSize(420, 260)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowCloseButtonHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 제목
        title = "동영상 분석 재개 중..." if self._resume_frame > 0 else "동영상 분석 중..."
        self._title_label = QLabel(title)
        self._title_label.setObjectName("titleLabel")
        layout.addWidget(self._title_label)

        # 프로그레스 바
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setFixedHeight(22)
        layout.addWidget(self._progress_bar)

        # 프레임 카운트
        self._frame_label = QLabel("0 / 0 프레임")
        self._frame_label.setObjectName("frameLabel")
        layout.addWidget(self._frame_label)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # 시간 정보
        self._time_label = QLabel("경과: 00:00  |  예상 남은: --:--")
        self._time_label.setObjectName("timeLabel")
        layout.addWidget(self._time_label)

        # 감지 실패 정보
        self._skip_label = QLabel("감지 실패: 0 프레임")
        self._skip_label.setObjectName("skipLabel")
        layout.addWidget(self._skip_label)

        layout.addStretch()

        # 취소 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._cancel_btn = QPushButton("취소")
        self._cancel_btn.setObjectName("cancelButton")
        self._cancel_btn.setFixedSize(100, 36)
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self._cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 타이머: 경과 시간 / 예상 남은 시간 업데이트
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._update_time_display)

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
            QLabel#frameLabel {
                font-size: 12px;
                color: #aaaaaa;
            }
            QLabel#timeLabel {
                font-size: 12px;
                color: #aaaaaa;
            }
            QLabel#skipLabel {
                font-size: 12px;
                color: #888888;
            }
            QFrame#separator {
                background-color: #3a3a3a;
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
        """)

    def start_analysis(self):
        """분석 시작 - exec() 전에 호출"""
        self._start_time = time.time()
        self._skipped_frames = self._resume_skipped

        self._worker = AnalysisWorker(
            video_path=self._video_path,
            sample_interval=self._sample_interval,
            resume_state=self._resume_state,
            resume_frame=self._resume_frame,
            resume_skipped=self._resume_skipped,
            resume_elapsed=self._resume_elapsed,
        )
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.analysis_completed.connect(self._on_completed)
        self._worker.analysis_cancelled.connect(self._on_cancelled)
        self._worker.skipped_updated.connect(self._on_skipped)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
        self._timer.start()

    def get_result(self) -> MovementAnalysisResult:
        """분석 결과 반환 (완료 시), 취소/실패 시 None"""
        return self._result

    def get_partial_state(self) -> dict:
        """취소 시 부분 상태 반환 (재개용)"""
        return self._partial_state

    def _on_progress(self, current: int, total: int):
        """진행률 업데이트"""
        if total > 0:
            percent = int(current / total * 100)
            self._progress_bar.setValue(percent)
            self._frame_label.setText(f"{current:,} / {total:,} 프레임")

    def _on_skipped(self, count: int):
        """감지 실패 수 업데이트"""
        self._skipped_frames = count
        self._skip_label.setText(f"감지 실패: {count} 프레임")

    def _on_completed(self, result: MovementAnalysisResult):
        """분석 완료"""
        self._result = result
        self._skipped_frames = result.skipped_frames
        self._progress_bar.setValue(100)
        self._title_label.setText("분석 완료!")

    def _on_cancelled(self, partial_result, analyzer_state: dict,
                      frame_index: int, skipped_frames: int):
        """분석 취소 - 부분 상태 저장"""
        self._partial_state = {
            'analyzer_state': analyzer_state,
            'frame_index': frame_index,
            'skipped_frames': skipped_frames,
            'elapsed_seconds': partial_result.duration_seconds if partial_result else 0.0,
        }

    def _on_error(self, error_msg: str):
        """분석 오류"""
        self._timer.stop()
        if self._finished:
            return
        self._finished = True
        self._title_label.setText("분석 오류!")
        QMessageBox.critical(self, "분석 오류", f"분석 중 오류가 발생했습니다:\n{error_msg}")
        self.reject()

    def _on_worker_finished(self):
        """워커 스레드 종료 시"""
        self._timer.stop()
        if self._finished:
            return
        self._finished = True
        if self._result is not None:
            self.accept()
        else:
            self.reject()

    def _on_cancel(self):
        """취소 버튼 클릭 - 확인 모달"""
        confirm = _ConfirmDialog(
            title="분석 취소",
            message="분석을 취소하시겠습니까?\n현재까지의 진행 상태가 저장됩니다.",
            parent=self,
        )
        if confirm.exec() != QDialog.DialogCode.Accepted:
            return

        if self._worker and self._worker.isRunning():
            self._cancel_btn.setEnabled(False)
            self._cancel_btn.setText("중단 중...")
            self._worker.stop()
            # _on_worker_finished에서 reject() 처리

    def _update_time_display(self):
        """경과 시간 / 예상 남은 시간 업데이트"""
        elapsed = time.time() - self._start_time
        elapsed_str = self._format_time(elapsed)

        progress = self._progress_bar.value()
        if progress > 0:
            estimated_total = elapsed / progress * 100
            remaining = max(0, estimated_total - elapsed)
            remaining_str = self._format_time(remaining)
        else:
            remaining_str = "--:--"

        self._time_label.setText(f"경과: {elapsed_str}  |  예상 남은: {remaining_str}")

    @staticmethod
    def _format_time(seconds: float) -> str:
        """초를 MM:SS 형식으로 변환"""
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m:02d}:{s:02d}"

    def closeEvent(self, event):
        """창 닫기 이벤트 - 분석 중이면 무시"""
        if self._worker and self._worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)


class _ConfirmDialog(QDialog):
    """앱 테마에 맞는 확인 다이얼로그"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(340, 160)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowCloseButtonHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(16)

        # 메시지
        msg_label = QLabel(message)
        msg_label.setObjectName("confirmMessage")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        layout.addStretch()

        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        no_btn = QPushButton("아니오")
        no_btn.setObjectName("confirmNoBtn")
        no_btn.setFixedSize(90, 34)
        no_btn.clicked.connect(self.reject)
        no_btn.setDefault(True)
        btn_layout.addWidget(no_btn)

        yes_btn = QPushButton("예")
        yes_btn.setObjectName("confirmYesBtn")
        yes_btn.setFixedSize(90, 34)
        yes_btn.clicked.connect(self.accept)
        btn_layout.addWidget(yes_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel#confirmMessage {
                color: #e0e0e0;
                font-size: 13px;
            }
            QPushButton#confirmNoBtn {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 16px;
            }
            QPushButton#confirmNoBtn:hover {
                background-color: #4a4a4a;
                border-color: #5a5a5a;
            }
            QPushButton#confirmNoBtn:pressed {
                background-color: #2a2a2a;
            }
            QPushButton#confirmYesBtn {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 6px 16px;
            }
            QPushButton#confirmYesBtn:hover {
                background-color: #5aaeFF;
            }
            QPushButton#confirmYesBtn:pressed {
                background-color: #3a8eef;
            }
        """)
