"""메인 윈도우 모듈"""
import os
import platform
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence
from typing import Optional, List

from .player_widget import PlayerWidget
from .status_widget import StatusWidget
from .settings_dialog import SettingsDialog
from ..utils.config import Config

# 앱 이름 (환경변수로 변경 가능)
APP_NAME = os.environ.get('SKELETON_ANALYZER_APP_NAME', 'Skeleton Analyzer')


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""

    MAX_RECENT_FILES = 10

    def __init__(self):
        super().__init__()
        self._recent_files: List[str] = []
        self._settings = QSettings("SkeletonAnalyzer", "SkeletonAnalyzer")
        self._config = Config()

        self._init_ui()
        self._init_menu()
        self._init_shortcuts()
        self._load_settings()

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1280, 720)
        self.resize(1600, 900)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 스플리터 (좌우 분할)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setObjectName("mainSplitter")
        self._splitter.setHandleWidth(8)
        self._splitter.setStyleSheet("""
            QSplitter#mainSplitter::handle:horizontal {
                width: 2px;
                margin-left: 1px;
                margin-right: 5px;
                background: qlineargradient(
                    x1: 0, y1: 0.25,
                    x2: 0, y2: 0.75,
                    stop: 0 transparent,
                    stop: 0.001 #888888,
                    stop: 0.999 #888888,
                    stop: 1 transparent
                );
            }
        """)

        # 왼쪽: 플레이어 위젯
        self.player_widget = PlayerWidget()
        self._splitter.addWidget(self.player_widget)

        # 오른쪽: 스테이터스 위젯
        self.status_widget = StatusWidget(config=self._config)
        self._splitter.addWidget(self.status_widget)

        # 50:50 비율 설정
        self._splitter.setSizes([800, 800])

        layout.addWidget(self._splitter)

        # 상태바
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        # 시그널 연결
        self.player_widget.frame_changed.connect(self._on_frame_changed)
        self.player_widget.capture_requested.connect(self._on_capture_requested)
        self.player_widget.video_loaded.connect(self._on_video_loaded)
        self.status_widget.exit_requested.connect(self.close)

    def _init_menu(self):
        """메뉴 초기화"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")

        # 열기
        open_action = QAction("동영상 파일 열기(&O)...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        # 최근 파일 서브메뉴
        self._recent_menu = file_menu.addMenu("최근 파일(&R)")
        self._update_recent_menu()

        file_menu.addSeparator()

        # 설정
        settings_action = QAction("설정(&S)...", self)
        if platform.system() == "Darwin":
            settings_action.setShortcut("Ctrl+,")
        else:
            settings_action.setShortcut("Ctrl+P")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        # 종료
        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 보기 메뉴
        view_menu = menubar.addMenu("보기(&V)")

        # 상태 패널
        self._angle_action = QAction("상태(&A)", self)
        self._angle_action.setCheckable(True)
        self._angle_action.setChecked(True)
        self._angle_action.setShortcut("Ctrl+1")
        self._angle_action.triggered.connect(
            lambda checked: self.status_widget.set_angle_visible(checked)
        )
        view_menu.addAction(self._angle_action)

        # 데이터 패널
        self._spreadsheet_action = QAction("데이터(&D)", self)
        self._spreadsheet_action.setCheckable(True)
        self._spreadsheet_action.setChecked(True)
        self._spreadsheet_action.setShortcut("Ctrl+2")
        self._spreadsheet_action.triggered.connect(
            lambda checked: self.status_widget.set_spreadsheet_visible(checked)
        )
        view_menu.addAction(self._spreadsheet_action)

        # 안전지표 패널
        self._ergonomic_action = QAction("안전지표(&E)", self)
        self._ergonomic_action.setCheckable(True)
        self._ergonomic_action.setChecked(True)
        self._ergonomic_action.setShortcut("Ctrl+3")
        self._ergonomic_action.triggered.connect(
            lambda checked: self.status_widget.set_ergonomic_visible(checked)
        )
        view_menu.addAction(self._ergonomic_action)

        # StatusWidget 가시성 변경 시 메뉴 동기화
        self.status_widget.visibility_changed.connect(self._on_visibility_changed)

    def _init_shortcuts(self):
        """단축키 초기화"""
        # 스페이스바: 재생/일시정지
        # PlayerWidget에서 처리

    def _load_settings(self):
        """설정 로드"""
        # 최근 파일 목록
        self._recent_files = self._settings.value("recent_files", [], type=list)

        # 윈도우 크기/위치
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # 스플리터 상태
        splitter_state = self._settings.value("splitter_state")
        if splitter_state:
            self._splitter.restoreState(splitter_state)

        # 패널 가시성 로드
        angle_visible = self._settings.value("panel_angle", True, type=bool)
        ergonomic_visible = self._settings.value("panel_ergonomic", True, type=bool)
        spreadsheet_visible = self._settings.value("panel_spreadsheet", True, type=bool)
        rula_visible = self._settings.value("panel_rula", True, type=bool)
        reba_visible = self._settings.value("panel_reba", True, type=bool)
        owas_visible = self._settings.value("panel_owas", True, type=bool)

        self.status_widget.set_angle_visible(angle_visible)
        self.status_widget.set_ergonomic_visible(ergonomic_visible)
        self.status_widget.set_spreadsheet_visible(spreadsheet_visible)
        self.status_widget.set_rula_visible(rula_visible)
        self.status_widget.set_reba_visible(reba_visible)
        self.status_widget.set_owas_visible(owas_visible)

        # 메뉴 체크 상태 동기화
        self._angle_action.setChecked(angle_visible)
        self._ergonomic_action.setChecked(ergonomic_visible)
        self._spreadsheet_action.setChecked(spreadsheet_visible)

    def _save_settings(self):
        """설정 저장"""
        self._settings.setValue("recent_files", self._recent_files)
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("splitter_state", self._splitter.saveState())

        # 패널 가시성 저장
        self._settings.setValue("panel_angle", self.status_widget.is_angle_visible())
        self._settings.setValue("panel_ergonomic", self.status_widget.is_ergonomic_visible())
        self._settings.setValue("panel_spreadsheet", self.status_widget.is_spreadsheet_visible())
        self._settings.setValue("panel_rula", self.status_widget.is_rula_visible())
        self._settings.setValue("panel_reba", self.status_widget.is_reba_visible())
        self._settings.setValue("panel_owas", self.status_widget.is_owas_visible())

    def _on_visibility_changed(self, panel: str, visible: bool):
        """패널 가시성 변경 시 메뉴 동기화"""
        if panel == 'angle':
            self._angle_action.setChecked(visible)
        elif panel == 'ergonomic':
            self._ergonomic_action.setChecked(visible)
        elif panel == 'spreadsheet':
            self._spreadsheet_action.setChecked(visible)

    def _open_file(self):
        """파일 열기 다이얼로그"""
        default_dir = self._config.get("directories.video_open", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "동영상 열기",
            default_dir,
            "동영상 파일 (*.mp4 *.avi *.mov *.mkv);;모든 파일 (*.*)"
        )

        if file_path:
            self._load_video(file_path)

    def _open_settings(self):
        """설정 다이얼로그 열기"""
        dialog = SettingsDialog(self._config, self)
        dialog.exec()

    def _load_video(self, file_path: str):
        """비디오 로드"""
        if self.player_widget.load_video(file_path):
            self._add_recent_file(file_path)
            self._status_bar.showMessage(f"로드됨: {file_path}")
        else:
            QMessageBox.warning(self, "오류", f"파일을 열 수 없습니다:\n{file_path}")

    def _add_recent_file(self, file_path: str):
        """최근 파일 목록에 추가"""
        # 이미 있으면 제거
        if file_path in self._recent_files:
            self._recent_files.remove(file_path)

        # 맨 앞에 추가
        self._recent_files.insert(0, file_path)

        # 최대 개수 제한
        self._recent_files = self._recent_files[:self.MAX_RECENT_FILES]

        self._update_recent_menu()

    def _update_recent_menu(self):
        """최근 파일 메뉴 업데이트"""
        self._recent_menu.clear()

        for file_path in self._recent_files:
            action = QAction(file_path, self)
            action.triggered.connect(lambda checked, fp=file_path: self._load_video(fp))
            self._recent_menu.addAction(action)

        self._recent_menu.setEnabled(len(self._recent_files) > 0)

    def _on_video_loaded(self, video_name: str):
        """동영상 로드 시 호출"""
        self.status_widget.set_video_name(video_name)

    def _on_frame_changed(self, frame, frame_number: int):
        """프레임 변경 시 호출"""
        if frame is not None:
            # 현재 위치 정보 업데이트
            timestamp = self.player_widget.get_current_position()
            self.status_widget.set_current_position(timestamp, frame_number)

            # 스테이터스 위젯에 프레임 전달
            self.status_widget.process_frame(frame)

    def _on_capture_requested(self, timestamp: float, frame_number: int):
        """캡처 요청 시 호출"""
        # 현재 상태를 스프레드시트에 캡처
        row_idx = self.status_widget.capture_current_state()

        if row_idx is not None:
            self._status_bar.showMessage(f"캡처됨: {timestamp:.3f}초 (프레임 {frame_number})")
        else:
            self._status_bar.showMessage("캡처 실패: 평가 결과가 없습니다.")

    def keyPressEvent(self, event):
        """키 입력 이벤트"""
        if event.key() == Qt.Key.Key_Space:
            self.player_widget.toggle_play()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.player_widget._on_capture_clicked()
        elif event.key() == Qt.Key.Key_Left:
            self.player_widget.seek_relative(-5)  # 5초 뒤로
        elif event.key() == Qt.Key.Key_Right:
            self.player_widget.seek_relative(5)  # 5초 앞으로
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # 종료 확인 다이얼로그
        from PyQt6.QtWidgets import QStyle
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("종료 확인")
        msg_box.setText("앱을 종료하시겠습니까?")
        # 시스템 표준 물음표 아이콘 사용
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
        msg_box.setIconPixmap(icon.pixmap(64, 64))
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        reply = msg_box.exec()

        if reply != QMessageBox.StandardButton.Yes:
            event.ignore()
            return

        # TODO: 고아 이미지 검사 및 삭제
        # self._cleanup_orphan_images()

        self._save_settings()
        self.player_widget.release()
        super().closeEvent(event)
