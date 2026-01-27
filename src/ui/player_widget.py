"""동영상 플레이어 위젯 모듈"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import numpy as np
from typing import Optional

from ..core.video_player import VideoPlayer


class PlayerWidget(QWidget):
    """동영상 플레이어 위젯"""

    # 시그널: (frame, frame_number)
    frame_changed = pyqtSignal(object, int)

    # 버튼 스타일 (ai-generate 스타일)
    BUTTON_STYLES = {
        'open': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a9a8a, stop:1 #2a8a7a);
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4aaa9a, stop:1 #3a9a8a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a8a7a, stop:1 #1a7a6a);
            }
        """,
        'play': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a9a6a, stop:1 #2a8a5a);
                color: white;
                border: none;
                padding: 5px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4aaa7a, stop:1 #3a9a6a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a8a5a, stop:1 #1a7a4a);
            }
        """,
        'pause': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #b8863a, stop:1 #a8762a);
                color: white;
                border: none;
                padding: 5px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c8964a, stop:1 #b8863a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a8762a, stop:1 #98661a);
            }
        """,
        'stop': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a85a5a, stop:1 #984a4a);
                color: white;
                border: none;
                padding: 5px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #b86a6a, stop:1 #a85a5a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #984a4a, stop:1 #883a3a);
            }
        """,
    }

    def __init__(self):
        super().__init__()
        self._video_player = VideoPlayer()
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer)

        self._init_ui()
        self._setup_drag_drop()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 상단 메뉴바 컨테이너
        menu_container = QWidget()
        menu_container.setStyleSheet("background-color: #333333; border-radius: 6px;")
        menu_container.setFixedHeight(42)
        menu_layout = QHBoxLayout(menu_container)
        menu_layout.setContentsMargins(10, 6, 10, 6)

        # 파일 열기 버튼
        self._open_btn = QPushButton("파일 열기")
        self._open_btn.setFixedHeight(28)
        self._open_btn.setStyleSheet(self.BUTTON_STYLES['open'])
        self._open_btn.clicked.connect(self._open_file_dialog)
        menu_layout.addWidget(self._open_btn)

        menu_layout.addStretch()
        layout.addWidget(menu_container)

        # 비디오 표시 영역
        self._video_label = QLabel()
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setStyleSheet("background-color: black;")
        self._video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self._video_label.setMinimumSize(320, 240)
        layout.addWidget(self._video_label)

        # 컨트롤바 컨테이너
        control_container = QWidget()
        control_container.setStyleSheet("background-color: #404040; border-radius: 6px;")
        control_container.setFixedHeight(50)
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(10, 5, 10, 5)
        control_layout.setSpacing(8)

        # 재생 버튼
        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(40, 32)
        self._play_btn.setStyleSheet(self.BUTTON_STYLES['play'])
        self._play_btn.clicked.connect(self.play)
        control_layout.addWidget(self._play_btn)

        # 일시정지 버튼
        self._pause_btn = QPushButton("⏸")
        self._pause_btn.setFixedSize(40, 32)
        self._pause_btn.setStyleSheet(self.BUTTON_STYLES['pause'])
        self._pause_btn.clicked.connect(self.pause)
        control_layout.addWidget(self._pause_btn)

        # 정지 버튼
        self._stop_btn = QPushButton("■")
        self._stop_btn.setFixedSize(40, 32)
        self._stop_btn.setStyleSheet(self.BUTTON_STYLES['stop'])
        self._stop_btn.clicked.connect(self.stop)
        control_layout.addWidget(self._stop_btn)

        # 시간 표시 (현재)
        self._current_time_label = QLabel("00:00")
        self._current_time_label.setFixedWidth(45)
        self._current_time_label.setStyleSheet("color: #ccc; font-size: 12px; font-weight: bold; background: transparent;")
        control_layout.addWidget(self._current_time_label)

        # 슬라이더 (시크바)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 100)
        self._slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #555;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4aaa9a, stop:1 #3a9a8a);
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5abaaa, stop:1 #4aaa9a);
            }
            QSlider::sub-page:horizontal {
                background: #3a9a8a;
                border-radius: 3px;
            }
        """)
        self._slider.sliderPressed.connect(self._on_slider_pressed)
        self._slider.sliderReleased.connect(self._on_slider_released)
        self._slider.sliderMoved.connect(self._on_slider_moved)
        control_layout.addWidget(self._slider)

        # 시간 표시 (전체)
        self._total_time_label = QLabel("00:00")
        self._total_time_label.setFixedWidth(45)
        self._total_time_label.setStyleSheet("color: #ccc; font-size: 12px; font-weight: bold; background: transparent;")
        control_layout.addWidget(self._total_time_label)

        layout.addWidget(control_container)

        self._slider_pressed = False

    def _setup_drag_drop(self):
        """드래그 앤 드롭 설정"""
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """드래그 진입 이벤트"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """드롭 이벤트"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.load_video(file_path)

    def load_video(self, file_path: str) -> bool:
        """비디오 로드"""
        self.stop()

        if self._video_player.load(file_path):
            # 슬라이더 범위 설정
            self._slider.setRange(0, self._video_player.frame_count - 1)

            # 전체 시간 표시
            self._total_time_label.setText(self._format_time(self._video_player.duration))

            # 첫 프레임 표시
            frame = self._video_player.read_frame()
            if frame is not None:
                self._display_frame(frame)
                self._video_player.seek(0)

            return True
        return False

    def toggle_play(self):
        """재생/일시정지 토글"""
        if self._video_player.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        """재생"""
        if self._video_player.is_loaded:
            self._video_player.play()
            fps = self._video_player.fps or 30
            self._timer.start(int(1000 / fps))

    def pause(self):
        """일시정지"""
        self._video_player.pause()
        self._timer.stop()

    def stop(self):
        """정지"""
        self._video_player.stop()
        self._timer.stop()
        self._update_time_display()
        self._slider.setValue(0)

    def seek_relative(self, seconds: float):
        """상대적 시크 (초 단위)"""
        if self._video_player.is_loaded:
            fps = self._video_player.fps or 30
            current_frame = self._video_player.current_frame
            target_frame = int(current_frame + seconds * fps)
            self._video_player.seek(target_frame)
            self._update_display()

    def release(self):
        """리소스 해제"""
        self._timer.stop()
        self._video_player.release()

    def _on_timer(self):
        """타이머 콜백"""
        frame = self._video_player.read_frame()
        if frame is not None:
            self._display_frame(frame)
            self._update_time_display()

            if not self._slider_pressed:
                self._slider.setValue(self._video_player.current_frame)

            # 시그널 발생
            self.frame_changed.emit(frame, self._video_player.current_frame)
        else:
            # 영상 끝
            self.pause()

    def _display_frame(self, frame: np.ndarray):
        """프레임 표시"""
        # BGR → RGB 변환
        rgb_frame = frame[:, :, ::-1].copy()
        h, w, ch = rgb_frame.shape

        # QImage 생성
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # 라벨 크기에 맞게 스케일
        label_size = self._video_label.size()
        scaled_pixmap = QPixmap.fromImage(q_img).scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self._video_label.setPixmap(scaled_pixmap)

    def _update_time_display(self):
        """시간 표시 업데이트"""
        current_time = self._video_player.current_time
        self._current_time_label.setText(self._format_time(current_time))

    def _update_display(self):
        """화면 업데이트"""
        if self._video_player.is_loaded:
            # 현재 위치의 프레임 읽기
            frame = self._video_player.read_frame()
            if frame is not None:
                self._display_frame(frame)
                self.frame_changed.emit(frame, self._video_player.current_frame)
            self._update_time_display()
            self._slider.setValue(self._video_player.current_frame)

    def _on_slider_pressed(self):
        """슬라이더 누름"""
        self._slider_pressed = True

    def _on_slider_released(self):
        """슬라이더 해제"""
        self._slider_pressed = False
        self._video_player.seek(self._slider.value())
        self._update_display()

    def _on_slider_moved(self, value: int):
        """슬라이더 이동"""
        # 미리보기 (선택적)
        pass

    def _open_file_dialog(self):
        """파일 열기 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "동영상 파일 열기",
            "",
            "동영상 파일 (*.mp4 *.avi *.mov *.mkv);;모든 파일 (*.*)"
        )
        if file_path:
            self.load_video(file_path)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """초를 MM:SS 형식으로 변환"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
