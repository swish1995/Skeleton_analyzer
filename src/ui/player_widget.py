"""동영상/이미지 슬라이드 플레이어 위젯 모듈"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSizePolicy, QFileDialog,
    QGraphicsOpacityEffect, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QBrush, QIcon
import numpy as np
from pathlib import Path
from typing import Optional

from ..core.video_player import VideoPlayer
from ..core.image_slide_player import ImageSlidePlayer


def _get_icon_path(icon_name: str) -> str:
    """아이콘 경로 반환"""
    return str(Path(__file__).parent.parent / "resources" / "icons" / f"{icon_name}.svg")


class PlayerWidget(QWidget):
    """동영상/이미지 슬라이드 플레이어 위젯

    두 가지 모드를 지원합니다:
    - video: 동영상 파일 재생 (기존)
    - image: 이미지 슬라이드쇼 (신규)
    """

    MODE_VIDEO = 'video'
    MODE_IMAGE = 'image'

    # 시그널: (frame, frame_number)
    frame_changed = pyqtSignal(object, int)
    # 캡처 요청 시그널: (timestamp, frame_number)
    capture_requested = pyqtSignal(float, int)
    # 동영상 로드 시그널: (video_name)
    video_loaded = pyqtSignal(str)
    # 소스 로드 시그널: (source_name) - 이미지 모드용
    source_loaded = pyqtSignal(str)
    # 동영상 열기 요청 시그널: (file_path)
    video_open_requested = pyqtSignal(str)
    # 이미지 폴더 열기 요청 시그널: (folder_path)
    folder_open_requested = pyqtSignal(str)
    # 압축 파일 열기 요청 시그널: (archive_path)
    archive_open_requested = pyqtSignal(str)

    # 버튼 스타일
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
        'open_folder': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a6a3a, stop:1 #7a5a2a);
                color: white;
                border: none;
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9a7a4a, stop:1 #8a6a3a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a5a2a, stop:1 #6a4a1a);
            }
        """,
        'open_archive': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a5a8a, stop:1 #5a4a7a);
                color: white;
                border: none;
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a6a9a, stop:1 #6a5a8a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a4a7a, stop:1 #4a3a6a);
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
        'nav': """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a8a5a, stop:1 #4a7a4a);
                color: white;
                border: none;
                padding: 5px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a9a6a, stop:1 #5a8a5a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a7a4a, stop:1 #3a6a3a);
            }
            QPushButton:disabled {
                background: #555555;
                color: #888888;
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

    SLIDER_STYLE = """
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
    """

    def __init__(self):
        super().__init__()
        self._video_player = VideoPlayer()
        self._image_player = ImageSlidePlayer()
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer)
        self._current_video_path = None
        self._current_video_name = None
        self._current_source_name = None
        self._mode = self.MODE_VIDEO

        self._init_ui()
        self._setup_drag_drop()

    @property
    def mode(self) -> str:
        """현재 모드 ('video' | 'image')"""
        return self._mode

    @property
    def image_player(self) -> ImageSlidePlayer:
        """이미지 슬라이드 플레이어 인스턴스"""
        return self._image_player

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # === 상단 메뉴바 ===
        menu_container = QWidget()
        menu_container.setStyleSheet("background-color: #333333; border-radius: 4px;")
        menu_container.setFixedHeight(32)
        menu_layout = QHBoxLayout(menu_container)
        menu_layout.setContentsMargins(8, 2, 8, 0)

        # 동영상 파일 열기 버튼
        self._open_btn = QPushButton(" 동영상")
        self._open_btn.setIcon(QIcon(_get_icon_path("video")))
        self._open_btn.setIconSize(QSize(14, 14))
        self._open_btn.setFixedHeight(26)
        self._open_btn.setStyleSheet(self.BUTTON_STYLES['open'])
        self._open_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._open_btn.clicked.connect(self._open_video_dialog)
        menu_layout.addWidget(self._open_btn)

        # 이미지 폴더 열기 버튼
        self._open_folder_btn = QPushButton(" 폴더")
        self._open_folder_btn.setIcon(QIcon(_get_icon_path("folder_open")))
        self._open_folder_btn.setIconSize(QSize(14, 14))
        self._open_folder_btn.setFixedHeight(26)
        self._open_folder_btn.setStyleSheet(self.BUTTON_STYLES['open_folder'])
        self._open_folder_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._open_folder_btn.clicked.connect(self._open_folder_dialog)
        menu_layout.addWidget(self._open_folder_btn)

        # 압축 파일 열기 버튼
        self._open_archive_btn = QPushButton(" 파일")
        self._open_archive_btn.setIcon(QIcon(_get_icon_path("archive")))
        self._open_archive_btn.setIconSize(QSize(14, 14))
        self._open_archive_btn.setFixedHeight(26)
        self._open_archive_btn.setStyleSheet(self.BUTTON_STYLES['open_archive'])
        self._open_archive_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._open_archive_btn.clicked.connect(self._open_archive_dialog)
        menu_layout.addWidget(self._open_archive_btn)

        # 안내 메시지
        self._help_label = QLabel("Space: 재생/정지  |  Enter: 캡처  |  ←/→: 5초 이동")
        self._help_label.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        menu_layout.addWidget(self._help_label)

        menu_layout.addStretch()
        layout.addWidget(menu_container)

        # === 비디오/이미지 표시 영역 ===
        video_container = QWidget()
        video_container.setStyleSheet("background-color: black;")
        video_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        video_container.setMinimumSize(320, 240)

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

        self._flash_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._flash_animation.setDuration(150)
        self._flash_animation.finished.connect(self._on_flash_finished)
        self._was_playing_before_capture = False

        layout.addWidget(video_container)
        self._video_container = video_container

        # === 컨트롤바 (QStackedWidget으로 모드 전환) ===
        self._control_stack = QStackedWidget()
        self._control_stack.setFixedHeight(50)

        # --- 동영상 컨트롤바 (index=0) ---
        video_control = self._create_video_control()
        self._control_stack.addWidget(video_control)

        # --- 이미지 슬라이드 컨트롤바 (index=1) ---
        image_control = self._create_image_control()
        self._control_stack.addWidget(image_control)

        self._control_stack.setCurrentIndex(0)
        layout.addWidget(self._control_stack)

        self._slider_pressed = False
        self._image_slider_pressed = False

    def _create_video_control(self) -> QWidget:
        """동영상 컨트롤바 생성"""
        control_container = QWidget()
        control_container.setStyleSheet("background-color: #404040; border-radius: 6px;")
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
        self._slider.setStyleSheet(self.SLIDER_STYLE)
        self._slider.sliderPressed.connect(self._on_slider_pressed)
        self._slider.sliderReleased.connect(self._on_slider_released)
        self._slider.sliderMoved.connect(self._on_slider_moved)
        control_layout.addWidget(self._slider)

        # 시간 표시 (전체)
        self._total_time_label = QLabel("00:00")
        self._total_time_label.setFixedWidth(45)
        self._total_time_label.setStyleSheet("color: #ccc; font-size: 12px; font-weight: bold; background: transparent;")
        control_layout.addWidget(self._total_time_label)

        return control_container

    def _create_image_control(self) -> QWidget:
        """이미지 슬라이드 컨트롤바 생성"""
        control_container = QWidget()
        control_container.setStyleSheet("background-color: #404040; border-radius: 6px;")
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(10, 5, 10, 5)
        control_layout.setSpacing(8)

        # 이전 버튼
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedSize(40, 32)
        self._prev_btn.setStyleSheet(self.BUTTON_STYLES['nav'])
        self._prev_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._prev_btn.clicked.connect(self._on_prev_image)
        self._prev_btn.setEnabled(False)
        control_layout.addWidget(self._prev_btn)

        # 다음 버튼
        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedSize(40, 32)
        self._next_btn.setStyleSheet(self.BUTTON_STYLES['nav'])
        self._next_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._next_btn.clicked.connect(self._on_next_image)
        self._next_btn.setEnabled(False)
        control_layout.addWidget(self._next_btn)

        # 이미지 캡처 버튼
        self._image_capture_btn = QPushButton()
        self._image_capture_btn.setFixedSize(40, 32)
        self._image_capture_btn.setIcon(self._create_capture_icon())
        self._image_capture_btn.setIconSize(self._image_capture_btn.size() * 0.6)
        self._image_capture_btn.setStyleSheet(self.BUTTON_STYLES['capture'])
        self._image_capture_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._image_capture_btn.clicked.connect(self._on_capture_clicked)
        self._image_capture_btn.setEnabled(False)
        control_layout.addWidget(self._image_capture_btn)

        # 현재/전체 인덱스 표시
        self._image_index_label = QLabel("0 / 0")
        self._image_index_label.setFixedWidth(70)
        self._image_index_label.setStyleSheet("color: #ccc; font-size: 12px; font-weight: bold; background: transparent;")
        self._image_index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(self._image_index_label)

        # 이미지 슬라이더
        self._image_slider = QSlider(Qt.Orientation.Horizontal)
        self._image_slider.setRange(0, 0)
        self._image_slider.setStyleSheet(self.SLIDER_STYLE)
        self._image_slider.sliderPressed.connect(self._on_image_slider_pressed)
        self._image_slider.sliderReleased.connect(self._on_image_slider_released)
        self._image_slider.sliderMoved.connect(self._on_image_slider_moved)
        control_layout.addWidget(self._image_slider)

        # 파일명 표시
        self._image_filename_label = QLabel("")
        self._image_filename_label.setFixedWidth(120)
        self._image_filename_label.setStyleSheet("color: #999; font-size: 10px; background: transparent;")
        self._image_filename_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        control_layout.addWidget(self._image_filename_label)

        return control_container

    # === 모드 전환 ===

    def set_mode(self, mode: str):
        """모드 전환

        Args:
            mode: 'video' 또는 'image'
        """
        self._mode = mode
        if mode == self.MODE_VIDEO:
            self._control_stack.setCurrentIndex(0)
            self._help_label.setText("Space: 재생/정지  |  Enter: 캡처  |  ←/→: 5초 이동")
        elif mode == self.MODE_IMAGE:
            self._control_stack.setCurrentIndex(1)
            self._help_label.setText("Enter: 캡처  |  ←/→: 이전/다음 이미지")

    # === 드래그 앤 드롭 ===

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
            lower = file_path.lower()
            if lower.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.video_open_requested.emit(file_path)
            elif lower.endswith('.zip'):
                self.archive_open_requested.emit(file_path)
            elif Path(file_path).is_dir():
                self.folder_open_requested.emit(file_path)

    # === 동영상 모드 ===

    def load_video(self, file_path: str) -> bool:
        """비디오 로드"""
        self.stop()
        self._image_player.release()

        if self._video_player.load(file_path):
            self.set_mode(self.MODE_VIDEO)

            self._slider.setRange(0, self._video_player.frame_count - 1)
            self._total_time_label.setText(self._format_time(self._video_player.duration))

            frame = self._video_player.read_frame()
            if frame is not None:
                self._display_frame(frame)
                self._video_player.seek(0)

            self._capture_btn.setEnabled(True)

            import os
            self._current_video_path = file_path
            self._current_video_name = os.path.splitext(os.path.basename(file_path))[0]
            self._current_source_name = self._current_video_name
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
        if self._mode == self.MODE_VIDEO and self._video_player.is_loaded:
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

    # === 이미지 슬라이드 모드 ===

    def load_images(self, folder_path: str) -> bool:
        """이미지 폴더 로드"""
        self.stop()
        self._video_player.release()

        if self._image_player.load_folder(folder_path):
            self._setup_image_mode(Path(folder_path).name)
            return True
        return False

    def load_archive(self, archive_path: str) -> bool:
        """압축 파일 로드"""
        self.stop()
        self._video_player.release()

        if self._image_player.load_archive(archive_path):
            self._setup_image_mode(Path(archive_path).stem)
            return True
        return False

    def _setup_image_mode(self, source_name: str):
        """이미지 모드 설정"""
        self.set_mode(self.MODE_IMAGE)

        count = self._image_player.image_count
        self._image_slider.setRange(0, count - 1)
        self._image_slider.setValue(0)
        self._update_image_index_display()

        # 첫 이미지 표시
        frame = self._image_player.read_frame()
        if frame is not None:
            self._display_frame(frame)
            self.frame_changed.emit(frame, 0)

        # 버튼 활성화
        self._image_capture_btn.setEnabled(True)
        self._update_image_nav_buttons()

        # 소스 이름 저장 및 시그널
        self._current_source_name = source_name
        self._current_video_name = None
        self._current_video_path = None
        self.source_loaded.emit(source_name)

    def _on_prev_image(self):
        """이전 이미지"""
        if self._image_player.is_loaded:
            frame = self._image_player.prev()
            if frame is not None:
                self._display_frame(frame)
                idx = self._image_player.current_index
                self._image_slider.setValue(idx)
                self._update_image_index_display()
                self._update_image_nav_buttons()
                self.frame_changed.emit(frame, idx)

    def _on_next_image(self):
        """다음 이미지"""
        if self._image_player.is_loaded:
            frame = self._image_player.next()
            if frame is not None:
                self._display_frame(frame)
                idx = self._image_player.current_index
                self._image_slider.setValue(idx)
                self._update_image_index_display()
                self._update_image_nav_buttons()
                self.frame_changed.emit(frame, idx)

    def navigate_prev(self):
        """외부에서 호출: 이전 이미지 (키보드 단축키용)"""
        if self._mode == self.MODE_IMAGE:
            self._on_prev_image()

    def navigate_next(self):
        """외부에서 호출: 다음 이미지 (키보드 단축키용)"""
        if self._mode == self.MODE_IMAGE:
            self._on_next_image()

    def _update_image_nav_buttons(self):
        """이미지 네비게이션 버튼 상태 업데이트"""
        if not self._image_player.is_loaded:
            self._prev_btn.setEnabled(False)
            self._next_btn.setEnabled(False)
            return
        self._prev_btn.setEnabled(self._image_player.current_index > 0)
        self._next_btn.setEnabled(
            self._image_player.current_index < self._image_player.image_count - 1
        )

    def _update_image_index_display(self):
        """이미지 인덱스 표시 업데이트"""
        if self._image_player.is_loaded:
            idx = self._image_player.current_index + 1
            total = self._image_player.image_count
            self._image_index_label.setText(f"{idx} / {total}")

            # 파일명 표시
            img_path = self._image_player.current_image_path
            if img_path:
                self._image_filename_label.setText(Path(img_path).name)
        else:
            self._image_index_label.setText("0 / 0")
            self._image_filename_label.setText("")

    def _on_image_slider_pressed(self):
        """이미지 슬라이더 누름"""
        self._image_slider_pressed = True

    def _on_image_slider_released(self):
        """이미지 슬라이더 해제"""
        self._image_slider_pressed = False
        idx = self._image_slider.value()
        frame = self._image_player.seek(idx)
        if frame is not None:
            self._display_frame(frame)
            self._update_image_index_display()
            self._update_image_nav_buttons()
            self.frame_changed.emit(frame, idx)

    def _on_image_slider_moved(self, value: int):
        """이미지 슬라이더 이동 (미리보기)"""
        frame = self._image_player.get_frame(value)
        if frame is not None:
            self._display_frame(frame)

    # === 캡처 (공통) ===

    def _on_capture_clicked(self):
        """캡처 버튼 클릭 핸들러"""
        if self._mode == self.MODE_VIDEO and self._video_player.is_loaded:
            timestamp = self._video_player.current_time
            frame_number = self._video_player.current_frame
            self.flash_effect()
            self.capture_requested.emit(timestamp, frame_number)
        elif self._mode == self.MODE_IMAGE and self._image_player.is_loaded:
            idx = self._image_player.current_index
            self.flash_effect()
            self.capture_requested.emit(0.0, idx)

    def flash_effect(self):
        """플래시 효과 실행"""
        if self._mode == self.MODE_VIDEO:
            self._was_playing_before_capture = self._video_player.is_playing
            if self._was_playing_before_capture:
                self.pause()
        else:
            self._was_playing_before_capture = False

        self._flash_overlay.show()
        self._flash_overlay.raise_()
        self._flash_animation.setStartValue(0.7)
        self._flash_animation.setEndValue(0)
        self._flash_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._flash_animation.start()

    def _on_flash_finished(self):
        """플래시 효과 완료 후"""
        self._flash_overlay.hide()
        if self._was_playing_before_capture:
            self.play()

    # === 공통 메서드 ===

    def resizeEvent(self, event):
        """크기 변경 시 오버레이 크기 조정"""
        super().resizeEvent(event)
        if hasattr(self, '_video_container'):
            size = self._video_container.size()
            self._video_label.setGeometry(0, 0, size.width(), size.height())
            self._flash_overlay.setGeometry(0, 0, size.width(), size.height())

    def seek_relative(self, seconds: float):
        """상대적 시크 (초 단위) - 동영상 모드 전용"""
        if self._mode == self.MODE_VIDEO and self._video_player.is_loaded:
            fps = self._video_player.fps or 30
            current_frame = self._video_player.current_frame
            target_frame = int(current_frame + seconds * fps)
            self._video_player.seek(target_frame)
            self._update_display()

    def get_current_position(self) -> float:
        """현재 재생 위치 (초 단위) 반환"""
        if self._mode == self.MODE_VIDEO:
            return self._video_player.current_time if self._video_player.is_loaded else 0.0
        return 0.0

    def get_current_frame_number(self) -> int:
        """현재 프레임/이미지 번호 반환"""
        if self._mode == self.MODE_VIDEO:
            return self._video_player.current_frame if self._video_player.is_loaded else 0
        elif self._mode == self.MODE_IMAGE:
            return self._image_player.current_index if self._image_player.is_loaded else 0
        return 0

    def get_video_path(self) -> Optional[str]:
        """현재 로드된 동영상 경로 반환"""
        if self._mode == self.MODE_VIDEO:
            return self._video_player.video_path if self._video_player.is_loaded else None
        return None

    def get_source_path(self) -> Optional[str]:
        """현재 소스 경로 반환 (동영상 또는 폴더/압축파일)"""
        if self._mode == self.MODE_VIDEO:
            return self.get_video_path()
        elif self._mode == self.MODE_IMAGE:
            return self._image_player.source_path
        return None

    def get_fps(self) -> float:
        """동영상 FPS 반환"""
        if self._mode == self.MODE_VIDEO:
            return self._video_player.fps if self._video_player.is_loaded else 30.0
        return 30.0

    def seek_to_frame(self, frame_number: int):
        """특정 프레임/이미지로 이동"""
        if self._mode == self.MODE_VIDEO and self._video_player.is_loaded:
            self._video_player.seek(frame_number)
            self._update_display()
        elif self._mode == self.MODE_IMAGE and self._image_player.is_loaded:
            frame = self._image_player.seek(frame_number)
            if frame is not None:
                self._display_frame(frame)
                self._image_slider.setValue(frame_number)
                self._update_image_index_display()
                self._update_image_nav_buttons()

    @property
    def video_name(self) -> Optional[str]:
        """현재 로드된 동영상 파일명 (확장자 제외)"""
        return self._current_video_name

    @property
    def source_name(self) -> Optional[str]:
        """현재 소스 이름 (동영상명 또는 폴더/압축파일명)"""
        return self._current_source_name

    def release(self):
        """리소스 해제"""
        self._timer.stop()
        self._video_player.release()
        self._image_player.release()

    # === 내부 메서드 ===

    def _on_timer(self):
        """타이머 콜백 (동영상 모드)"""
        frame = self._video_player.read_frame()
        if frame is not None:
            self._display_frame(frame)
            self._update_time_display()

            if not self._slider_pressed:
                self._slider.setValue(self._video_player.current_frame)

            self.frame_changed.emit(frame, self._video_player.current_frame)
        else:
            self.pause()
            self._update_play_button_state()

    def _display_frame(self, frame: np.ndarray):
        """프레임 표시"""
        rgb_frame = frame[:, :, ::-1].copy()
        h, w, ch = rgb_frame.shape

        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        label_size = self._video_label.size()
        scaled_pixmap = QPixmap.fromImage(q_img).scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self._video_label.setPixmap(scaled_pixmap)

    def _update_time_display(self):
        """시간 표시 업데이트 (동영상 모드)"""
        current_time = self._video_player.current_time
        self._current_time_label.setText(self._format_time(current_time))

    def _update_display(self):
        """화면 업데이트 (동영상 모드)"""
        if self._mode == self.MODE_VIDEO and self._video_player.is_loaded:
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
        pass

    def _open_video_dialog(self):
        """동영상 파일 열기 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "동영상 파일 열기",
            "",
            "동영상 파일 (*.mp4 *.avi *.mov *.mkv);;모든 파일 (*.*)"
        )
        if file_path:
            self.video_open_requested.emit(file_path)

    def _open_folder_dialog(self):
        """이미지 폴더 열기 다이얼로그"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "이미지 폴더 열기",
            "",
        )
        if folder_path:
            self.folder_open_requested.emit(folder_path)

    def _open_archive_dialog(self):
        """압축 파일 열기 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "압축 파일 열기",
            "",
            "압축 파일 (*.zip);;모든 파일 (*.*)"
        )
        if file_path:
            self.archive_open_requested.emit(file_path)

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

        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(2)
        painter.setPen(pen)

        corner_len = 6
        margin = 2

        painter.drawLine(margin, margin, margin + corner_len, margin)
        painter.drawLine(margin, margin, margin, margin + corner_len)

        painter.drawLine(size - margin - corner_len, margin, size - margin, margin)
        painter.drawLine(size - margin, margin, size - margin, margin + corner_len)

        painter.drawLine(margin, size - margin - corner_len, margin, size - margin)
        painter.drawLine(margin, size - margin, margin + corner_len, size - margin)

        painter.drawLine(size - margin, size - margin - corner_len, size - margin, size - margin)
        painter.drawLine(size - margin - corner_len, size - margin, size - margin, size - margin)

        center = size // 2
        radius = 4
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)

        painter.end()
        return QIcon(pixmap)
