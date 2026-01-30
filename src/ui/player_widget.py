"""동영상 플레이어 위젯 모듈"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSizePolicy, QFileDialog,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QBrush, QIcon
import numpy as np
from typing import Optional

from ..core.video_player import VideoPlayer


class PlayerWidget(QWidget):
    """동영상 플레이어 위젯"""

    # 시그널: (frame, frame_number)
    frame_changed = pyqtSignal(object, int)
    # 캡처 요청 시그널: (timestamp, frame_number)
    capture_requested = pyqtSignal(float, int)
    # 동영상 로드 시그널: (video_name)
    video_loaded = pyqtSignal(str)

    # 버튼 스타일 (ai-generate 스타일)
    BUTTON_STYLES = {
        'open': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a9a8a, stop:1 #2a8a7a);
                color: white;
                border: none;
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 11px;
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
        'capture': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a7ab8, stop:1 #4a6aa8);
                color: white;
                border: none;
                padding: 5px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a8ac8, stop:1 #5a7ab8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a6aa8, stop:1 #3a5a98);
            }
            QPushButton:disabled {
                background: #555555;
                color: #888888;
            }
        """,
    }

    def __init__(self):
        super().__init__()
        self._video_player = VideoPlayer()
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer)
        self._current_video_path = None
        self._current_video_name = None

        self._init_ui()
        self._setup_drag_drop()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 상단 메뉴바 컨테이너
        menu_container = QWidget()
        menu_container.setStyleSheet("background-color: #333333; border-radius: 4px;")
        menu_container.setFixedHeight(32)
        menu_layout = QHBoxLayout(menu_container)
        menu_layout.setContentsMargins(8, 2, 8, 0)

        # 파일 열기 버튼
        self._open_btn = QPushButton("동영상 파일 열기")
        self._open_btn.setFixedHeight(26)
        self._open_btn.setStyleSheet(self.BUTTON_STYLES['open'])
        self._open_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._open_btn.clicked.connect(self._open_file_dialog)
        menu_layout.addWidget(self._open_btn)

        # 안내 메시지
        help_label = QLabel("Space: 재생/일시정지  |  Enter: 캡처  |  ←/→: 5초 이동")
        help_label.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        menu_layout.addWidget(help_label)

        menu_layout.addStretch()
        layout.addWidget(menu_container)

        # 비디오 컨테이너 (비디오 + 플래시 오버레이)
        video_container = QWidget()
        video_container.setStyleSheet("background-color: black;")
        video_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        video_container.setMinimumSize(320, 240)

        # 비디오 표시 영역
        self._video_label = QLabel(video_container)
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setStyleSheet("background-color: black;")

        # 플래시 오버레이
        self._flash_overlay = QLabel(video_container)
        self._flash_overlay.setStyleSheet("background-color: white;")
        self._flash_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._opacity_effect = QGraphicsOpacityEffect(self._flash_overlay)
        self._opacity_effect.setOpacity(0)
        self._flash_overlay.setGraphicsEffect(self._opacity_effect)
        self._flash_overlay.hide()

        # 플래시 애니메이션
        self._flash_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._flash_animation.setDuration(150)
        self._flash_animation.finished.connect(self._on_flash_finished)
        self._was_playing_before_capture = False

        layout.addWidget(video_container)
        self._video_container = video_container

        # 컨트롤바 컨테이너
        control_container = QWidget()
        control_container.setStyleSheet("background-color: #404040; border-radius: 6px;")
        control_container.setFixedHeight(50)
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(10, 5, 10, 5)
        control_layout.setSpacing(8)

        # 재생/일시정지 토글 버튼
        self._play_toggle_btn = QPushButton("▶")
        self._play_toggle_btn.setFixedSize(40, 32)
        self._play_toggle_btn.setStyleSheet(self.BUTTON_STYLES['play'])
        self._play_toggle_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._play_toggle_btn.clicked.connect(self.toggle_play)
        control_layout.addWidget(self._play_toggle_btn)

        # 캡처 버튼
        self._capture_btn = QPushButton()
        self._capture_btn.setFixedSize(40, 32)
        self._capture_btn.setIcon(self._create_capture_icon())
        self._capture_btn.setIconSize(self._capture_btn.size() * 0.6)
        self._capture_btn.setStyleSheet(self.BUTTON_STYLES['capture'])
        self._capture_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._capture_btn.clicked.connect(self._on_capture_clicked)
        self._capture_btn.setEnabled(False)
        control_layout.addWidget(self._capture_btn)

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

            # 캡처 버튼 활성화
            self._capture_btn.setEnabled(True)

            # 파일명 저장 및 시그널 발생
            import os
            self._current_video_path = file_path
            self._current_video_name = os.path.splitext(os.path.basename(file_path))[0]
            self.video_loaded.emit(self._current_video_name)

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
            self._update_play_button_state()

    def pause(self):
        """일시정지"""
        self._video_player.pause()
        self._timer.stop()
        self._update_play_button_state()

    def stop(self):
        """정지"""
        self._video_player.stop()
        self._timer.stop()
        self._update_time_display()
        self._slider.setValue(0)
        self._update_play_button_state()

    def _update_play_button_state(self):
        """재생/일시정지 버튼 상태 업데이트"""
        if self._video_player.is_playing:
            self._play_toggle_btn.setText("⏸")
        else:
            self._play_toggle_btn.setText("▶")

    def _on_capture_clicked(self):
        """캡처 버튼 클릭 핸들러"""
        if self._video_player.is_loaded:
            timestamp = self._video_player.current_time
            frame_number = self._video_player.current_frame
            self.flash_effect()  # 플래시 효과 + 잠깐 멈춤
            self.capture_requested.emit(timestamp, frame_number)

    def flash_effect(self):
        """플래시 효과 실행"""
        # 재생 중이었는지 저장 후 일시정지
        self._was_playing_before_capture = self._video_player.is_playing
        if self._was_playing_before_capture:
            self.pause()

        # 플래시 효과
        self._flash_overlay.show()
        self._flash_overlay.raise_()
        self._flash_animation.setStartValue(0.7)
        self._flash_animation.setEndValue(0)
        self._flash_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._flash_animation.start()

    def _on_flash_finished(self):
        """플래시 효과 완료 후"""
        self._flash_overlay.hide()
        # 이전에 재생 중이었으면 다시 재생
        if self._was_playing_before_capture:
            self.play()

    def resizeEvent(self, event):
        """크기 변경 시 오버레이 크기 조정"""
        super().resizeEvent(event)
        if hasattr(self, '_video_container'):
            size = self._video_container.size()
            self._video_label.setGeometry(0, 0, size.width(), size.height())
            self._flash_overlay.setGeometry(0, 0, size.width(), size.height())

    def seek_relative(self, seconds: float):
        """상대적 시크 (초 단위)"""
        if self._video_player.is_loaded:
            fps = self._video_player.fps or 30
            current_frame = self._video_player.current_frame
            target_frame = int(current_frame + seconds * fps)
            self._video_player.seek(target_frame)
            self._update_display()

    def get_current_position(self) -> float:
        """현재 재생 위치 (초 단위) 반환"""
        return self._video_player.current_time if self._video_player.is_loaded else 0.0

    def get_current_frame_number(self) -> int:
        """현재 프레임 번호 반환"""
        return self._video_player.current_frame if self._video_player.is_loaded else 0

    def get_video_path(self) -> Optional[str]:
        """현재 로드된 동영상 경로 반환"""
        return self._video_player.video_path if self._video_player.is_loaded else None

    def get_fps(self) -> float:
        """동영상 FPS 반환"""
        return self._video_player.fps if self._video_player.is_loaded else 30.0

    def seek_to_frame(self, frame_number: int):
        """특정 프레임으로 이동"""
        if self._video_player.is_loaded:
            self._video_player.seek(frame_number)
            self._update_display()

    @property
    def video_name(self) -> Optional[str]:
        """현재 로드된 동영상 파일명 (확장자 제외)"""
        return self._current_video_name

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
            self._update_play_button_state()

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

    @staticmethod
    def _create_capture_icon() -> QIcon:
        """캡처 버튼 아이콘 생성 (뷰파인더 + 원형)"""
        size = 24
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 펜 설정 (흰색, 두께 2)
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(2)
        painter.setPen(pen)

        # 모서리 길이
        corner_len = 6
        margin = 2

        # 좌상단 모서리
        painter.drawLine(margin, margin, margin + corner_len, margin)
        painter.drawLine(margin, margin, margin, margin + corner_len)

        # 우상단 모서리
        painter.drawLine(size - margin - corner_len, margin, size - margin, margin)
        painter.drawLine(size - margin, margin, size - margin, margin + corner_len)

        # 좌하단 모서리
        painter.drawLine(margin, size - margin - corner_len, margin, size - margin)
        painter.drawLine(margin, size - margin, margin + corner_len, size - margin)

        # 우하단 모서리
        painter.drawLine(size - margin, size - margin - corner_len, size - margin, size - margin)
        painter.drawLine(size - margin - corner_len, size - margin, size - margin, size - margin)

        # 중앙 원 (채워진 원)
        center = size // 2
        radius = 4
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)

        painter.end()
        return QIcon(pixmap)
