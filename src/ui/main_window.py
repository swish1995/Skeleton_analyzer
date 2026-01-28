"""메인 윈도우 모듈"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence
from typing import Optional, List

from .player_widget import PlayerWidget
from .status_widget import StatusWidget


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""

    MAX_RECENT_FILES = 10

    def __init__(self):
        super().__init__()
        self._recent_files: List[str] = []
        self._settings = QSettings("SkeletonAnalyzer", "SkeletonAnalyzer")

        self._init_ui()
        self._init_menu()
        self._init_shortcuts()
        self._load_settings()

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Skeleton Analyzer")
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

        # 왼쪽: 플레이어 위젯
        self.player_widget = PlayerWidget()
        self._splitter.addWidget(self.player_widget)

        # 오른쪽: 스테이터스 위젯
        self.status_widget = StatusWidget()
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

    def _init_menu(self):
        """메뉴 초기화"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")

        # 열기
        open_action = QAction("열기(&O)...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        # 최근 파일 서브메뉴
        self._recent_menu = file_menu.addMenu("최근 파일(&R)")
        self._update_recent_menu()

        file_menu.addSeparator()

        # 종료
        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

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

    def _save_settings(self):
        """설정 저장"""
        self._settings.setValue("recent_files", self._recent_files)
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("splitter_state", self._splitter.saveState())

    def _open_file(self):
        """파일 열기 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "동영상 열기",
            "",
            "동영상 파일 (*.mp4 *.avi *.mov *.mkv);;모든 파일 (*.*)"
        )

        if file_path:
            self._load_video(file_path)

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

    def _on_frame_changed(self, frame, frame_number: int):
        """프레임 변경 시 호출"""
        if frame is not None:
            # 스테이터스 위젯에 프레임 전달
            self.status_widget.process_frame(frame)

    def keyPressEvent(self, event):
        """키 입력 이벤트"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.player_widget.toggle_play()
        elif event.key() == Qt.Key.Key_Space:
            # 스페이스바 이벤트 무시 (기본 동작 방지)
            event.accept()
        elif event.key() == Qt.Key.Key_Left:
            self.player_widget.seek_relative(-5)  # 5초 뒤로
        elif event.key() == Qt.Key.Key_Right:
            self.player_widget.seek_relative(5)  # 5초 앞으로
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """창 닫기 이벤트"""
        self._save_settings()
        self.player_widget.release()
        super().closeEvent(event)
