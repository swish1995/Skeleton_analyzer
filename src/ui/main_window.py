"""메인 윈도우 모듈"""
import os
import platform
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox,
    QToolBar, QToolButton
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QPixmap, QPainter
from typing import Optional, List

from .player_widget import PlayerWidget
from .status_widget import StatusWidget
from .settings_dialog import SettingsDialog
from ..utils.config import Config
from ..core.project_manager import ProjectManager, ProjectLoadError, LoadResult
from ..core.logger import get_logger

# 앱 이름 (환경변수로 변경 가능)
APP_NAME = os.environ.get('SKELETON_ANALYZER_APP_NAME', 'Skeleton Analyzer')


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""

    MAX_RECENT_FILES = 10

    def __init__(self):
        super().__init__()
        self._logger = get_logger('main_window')
        self._logger.debug("MainWindow 초기화 시작")

        self._recent_files: List[str] = []
        self._recent_projects: List[str] = []
        self._settings = QSettings("SkeletonAnalyzer", "SkeletonAnalyzer")
        self._config = Config()
        self._project_manager = ProjectManager()

        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_shortcuts()
        self._load_settings()

        # 앱 시작 시 captures 디렉토리 전체 정리 (고아 이미지 삭제)
        self._cleanup_all_captures()

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
        self.player_widget.video_open_requested.connect(self._load_video)
        self.status_widget.exit_requested.connect(self.close)
        # 캡처 추가/변경 시 dirty 표시
        self.status_widget.capture_added.connect(self._mark_project_dirty)

    def _init_menu(self):
        """메뉴 초기화"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")

        # 새 프로젝트
        new_project_action = QAction("새 프로젝트(&N)", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self._new_project)
        file_menu.addAction(new_project_action)

        # 프로젝트 열기
        open_project_action = QAction("프로젝트 열기(&P)...", self)
        open_project_action.setShortcut("Ctrl+Shift+O")
        open_project_action.triggered.connect(self._open_project)
        file_menu.addAction(open_project_action)

        # 프로젝트 저장
        self._save_project_action = QAction("프로젝트 저장(&S)", self)
        self._save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        self._save_project_action.triggered.connect(self._save_project)
        file_menu.addAction(self._save_project_action)

        # 다른 이름으로 저장
        save_as_action = QAction("다른 이름으로 저장(&A)...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # 동영상 열기
        open_action = QAction("동영상 파일 열기(&O)...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # 최근 프로젝트 서브메뉴
        self._recent_projects_menu = file_menu.addMenu("최근 프로젝트")
        self._update_recent_projects_menu()

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

    # 툴바 버튼 색상 정의
    TOOLBAR_BUTTON_COLORS = {
        'open': ('#b8a25a', '#a8924a', '#c8b26a'),     # 골드/노란색
        'save': ('#5ab87a', '#4aa86a', '#6ac88a'),     # 초록색
        '상태': ('#3a9a8a', '#2a8a7a', '#4aaa9a'),      # 틸색
        '데이터': ('#5a7ab8', '#4a6aa8', '#6a8ac8'),    # 파란색
        '안전지표': ('#8a5ab8', '#7a4aa8', '#9a6ac8'),  # 보라색
        'RULA': ('#b8825a', '#a8724a', '#c8926a'),      # 주황색
        'REBA': ('#5ab87a', '#4aa86a', '#6ac88a'),      # 초록색
        'OWAS': ('#b85a6a', '#a84a5a', '#c86a7a'),      # 빨간색
        '설정': ('#7a7a7a', '#6a6a6a', '#8a8a8a'),      # 회색
        '종료': ('#c55a5a', '#b54a4a', '#d56a6a'),      # 진한 빨간색
    }

    def _get_toolbar_button_style(self, color_key: str, is_on: bool = True, is_sub: bool = False) -> str:
        """툴바 버튼 스타일 생성"""
        colors = self.TOOLBAR_BUTTON_COLORS.get(color_key, self.TOOLBAR_BUTTON_COLORS['open'])
        base, dark, light = colors
        padding = "5px 8px" if is_sub else "5px 12px"
        font_size = "10px" if is_sub else "11px"
        text_color = "white" if is_on else "rgba(255, 255, 255, 0.6)"

        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {base}, stop:1 {dark});
                color: {text_color};
                border: none;
                padding: {padding};
                border-radius: 4px;
                font-size: {font_size};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {light}, stop:1 {base});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {dark}, stop:1 {base});
            }}
            QPushButton:disabled {{
                background: #444444;
                color: #555555;
            }}
        """

    def _get_icon_path(self, icon_name: str) -> str:
        """아이콘 경로 반환"""
        return str(Path(__file__).parent.parent / "resources" / "icons" / f"{icon_name}.svg")

    def _get_icon_with_opacity(self, icon_name: str, opacity: float = 1.0) -> QIcon:
        """투명도가 적용된 아이콘 반환"""
        pixmap = QPixmap(self._get_icon_path(icon_name))
        if opacity < 1.0:
            transparent = QPixmap(pixmap.size())
            transparent.fill(Qt.GlobalColor.transparent)
            painter = QPainter(transparent)
            painter.setOpacity(opacity)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            return QIcon(transparent)
        return QIcon(pixmap)

    def _init_toolbar(self):
        """메인 툴바 초기화"""
        from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout

        # 단축키 표시 접두사 (macOS: ⌘, 기타: Ctrl+)
        shortcut_prefix = "⌘" if platform.system() == "Darwin" else "Ctrl+"

        self._toolbar = QToolBar("메인 툴바")
        self._toolbar.setMovable(False)
        self._toolbar.setFloatable(False)
        self._toolbar.setStyleSheet("""
            QToolBar {
                background-color: #333333;
                border: none;
                padding: 8px 10px;
                spacing: 8px;
            }
        """)
        self.addToolBar(self._toolbar)

        # 프로젝트 열기 버튼
        self._open_btn = QPushButton(" 열기")
        self._open_btn.setIcon(QIcon(self._get_icon_path("folder_open")))
        self._open_btn.setIconSize(QSize(14, 14))
        self._open_btn.setFixedHeight(28)
        self._open_btn.setToolTip("프로젝트 열기 (Ctrl+Shift+O)")
        self._open_btn.setStyleSheet(self._get_toolbar_button_style('open'))
        self._open_btn.clicked.connect(self._open_project)
        self._toolbar.addWidget(self._open_btn)

        # 프로젝트 저장 버튼
        self._save_btn = QPushButton(" 저장")
        self._save_btn.setIcon(QIcon(self._get_icon_path("save")))
        self._save_btn.setIconSize(QSize(14, 14))
        self._save_btn.setFixedHeight(28)
        self._save_btn.setToolTip("프로젝트 저장 (Ctrl+S)")
        self._save_btn.setStyleSheet(self._get_toolbar_button_style('save'))
        self._save_btn.clicked.connect(self._save_project)
        self._toolbar.addWidget(self._save_btn)

        # 프로젝트 버튼과 보기 토글 버튼 사이 간격 (동영상 플레이어 최소 너비에 맞춤)
        project_spacer = QWidget()
        project_spacer.setFixedWidth(260)
        self._toolbar.addWidget(project_spacer)

        # 보기 라벨
        from PyQt6.QtWidgets import QLabel
        view_label = QLabel("보기:")
        view_label.setStyleSheet("color: #999999; font-size: 12px; margin-right: 4px;")
        self._toolbar.addWidget(view_label)

        # 상태 버튼 (토글)
        self._status_btn = QPushButton(f" 상태 ({shortcut_prefix}1)")
        self._status_btn.setIcon(QIcon(self._get_icon_path("status")))
        self._status_btn.setIconSize(QSize(14, 14))
        self._status_btn.setFixedHeight(28)
        self._status_btn.setCheckable(True)
        self._status_btn.setChecked(True)
        self._status_btn.setStyleSheet(self._get_toolbar_button_style('상태', True))
        self._status_btn.toggled.connect(self._on_status_toggled)
        self._toolbar.addWidget(self._status_btn)

        # 데이터 버튼 (토글)
        self._data_btn = QPushButton(f" 데이터 ({shortcut_prefix}2)")
        self._data_btn.setIcon(QIcon(self._get_icon_path("data")))
        self._data_btn.setIconSize(QSize(14, 14))
        self._data_btn.setFixedHeight(28)
        self._data_btn.setCheckable(True)
        self._data_btn.setChecked(True)
        self._data_btn.setStyleSheet(self._get_toolbar_button_style('데이터', True))
        self._data_btn.toggled.connect(self._on_data_toggled)
        self._toolbar.addWidget(self._data_btn)

        # 구분선
        self._toolbar.addSeparator()

        # 안전지표 버튼 (토글)
        self._safety_btn = QPushButton(f" 안전지표 ({shortcut_prefix}3)")
        self._safety_btn.setIcon(QIcon(self._get_icon_path("safety")))
        self._safety_btn.setIconSize(QSize(14, 14))
        self._safety_btn.setFixedHeight(28)
        self._safety_btn.setCheckable(True)
        self._safety_btn.setChecked(True)
        self._safety_btn.setStyleSheet(self._get_toolbar_button_style('안전지표', True))
        self._safety_btn.toggled.connect(self._on_safety_toggled)
        self._toolbar.addWidget(self._safety_btn)

        # RULA 버튼 (서브 토글)
        self._rula_btn = QPushButton("RULA")
        self._rula_btn.setFixedHeight(28)
        self._rula_btn.setCheckable(True)
        self._rula_btn.setChecked(True)
        self._rula_btn.setStyleSheet(self._get_toolbar_button_style('RULA', True, True))
        self._rula_btn.toggled.connect(self._on_rula_toggled)
        self._toolbar.addWidget(self._rula_btn)

        # REBA 버튼 (서브 토글)
        self._reba_btn = QPushButton("REBA")
        self._reba_btn.setFixedHeight(28)
        self._reba_btn.setCheckable(True)
        self._reba_btn.setChecked(True)
        self._reba_btn.setStyleSheet(self._get_toolbar_button_style('REBA', True, True))
        self._reba_btn.toggled.connect(self._on_reba_toggled)
        self._toolbar.addWidget(self._reba_btn)

        # OWAS 버튼 (서브 토글)
        self._owas_btn = QPushButton("OWAS")
        self._owas_btn.setFixedHeight(28)
        self._owas_btn.setCheckable(True)
        self._owas_btn.setChecked(True)
        self._owas_btn.setStyleSheet(self._get_toolbar_button_style('OWAS', True, True))
        self._owas_btn.toggled.connect(self._on_owas_toggled)
        self._toolbar.addWidget(self._owas_btn)

        # 늘어나는 공간 (spacer)
        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy().Expanding,
            spacer.sizePolicy().verticalPolicy().Preferred
        )
        self._toolbar.addWidget(spacer)

        # 설정 버튼
        settings_shortcut = "⌘," if platform.system() == "Darwin" else "Ctrl+P"
        self._settings_btn = QPushButton(f" 설정 ({settings_shortcut})")
        self._settings_btn.setIcon(QIcon(self._get_icon_path("settings")))
        self._settings_btn.setIconSize(QSize(14, 14))
        self._settings_btn.setFixedHeight(28)
        self._settings_btn.setStyleSheet(self._get_toolbar_button_style('설정', True))
        self._settings_btn.clicked.connect(self._open_settings)
        self._toolbar.addWidget(self._settings_btn)

        # 종료 버튼
        self._exit_btn = QPushButton(" 종료")
        self._exit_btn.setIcon(QIcon(self._get_icon_path("exit")))
        self._exit_btn.setIconSize(QSize(14, 14))
        self._exit_btn.setFixedHeight(28)
        self._exit_btn.setStyleSheet(self._get_toolbar_button_style('종료', True))
        self._exit_btn.clicked.connect(self.close)
        self._toolbar.addWidget(self._exit_btn)

    # === 툴바 버튼 토글 핸들러 ===

    def _on_status_toggled(self, checked: bool):
        """상태 패널 토글"""
        self.status_widget.set_angle_visible(checked)
        self._status_btn.setStyleSheet(self._get_toolbar_button_style('상태', checked))
        self._status_btn.setIcon(self._get_icon_with_opacity("status", 1.0 if checked else 0.6))
        self._angle_action.setChecked(checked)

    def _on_data_toggled(self, checked: bool):
        """데이터 패널 토글"""
        self.status_widget.set_spreadsheet_visible(checked)
        self._data_btn.setStyleSheet(self._get_toolbar_button_style('데이터', checked))
        self._data_btn.setIcon(self._get_icon_with_opacity("data", 1.0 if checked else 0.6))
        self._spreadsheet_action.setChecked(checked)

    def _on_safety_toggled(self, checked: bool):
        """안전지표 패널 토글"""
        self.status_widget.set_ergonomic_visible(checked)
        self._safety_btn.setStyleSheet(self._get_toolbar_button_style('안전지표', checked))
        self._safety_btn.setIcon(self._get_icon_with_opacity("safety", 1.0 if checked else 0.6))
        self._ergonomic_action.setChecked(checked)
        # RULA/REBA/OWAS 버튼 활성/비활성
        self._rula_btn.setEnabled(checked)
        self._reba_btn.setEnabled(checked)
        self._owas_btn.setEnabled(checked)

    def _on_rula_toggled(self, checked: bool):
        """RULA 패널 토글"""
        self.status_widget.set_rula_visible(checked)
        self._rula_btn.setStyleSheet(self._get_toolbar_button_style('RULA', checked, True))

    def _on_reba_toggled(self, checked: bool):
        """REBA 패널 토글"""
        self.status_widget.set_reba_visible(checked)
        self._reba_btn.setStyleSheet(self._get_toolbar_button_style('REBA', checked, True))

    def _on_owas_toggled(self, checked: bool):
        """OWAS 패널 토글"""
        self.status_widget.set_owas_visible(checked)
        self._owas_btn.setStyleSheet(self._get_toolbar_button_style('OWAS', checked, True))

    def _init_shortcuts(self):
        """단축키 초기화"""
        # 스페이스바: 재생/일시정지
        # PlayerWidget에서 처리

    def _load_settings(self):
        """설정 로드"""
        # 최근 파일 목록
        self._recent_files = self._settings.value("recent_files", [], type=list)
        self._recent_projects = self._settings.value("recent_projects", [], type=list)

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

        # 툴바 버튼 상태 동기화
        self._status_btn.setChecked(angle_visible)
        self._status_btn.setStyleSheet(self._get_toolbar_button_style('상태', angle_visible))
        self._data_btn.setChecked(spreadsheet_visible)
        self._data_btn.setStyleSheet(self._get_toolbar_button_style('데이터', spreadsheet_visible))
        self._safety_btn.setChecked(ergonomic_visible)
        self._safety_btn.setStyleSheet(self._get_toolbar_button_style('안전지표', ergonomic_visible))
        self._rula_btn.setChecked(rula_visible)
        self._rula_btn.setStyleSheet(self._get_toolbar_button_style('RULA', rula_visible, True))
        self._reba_btn.setChecked(reba_visible)
        self._reba_btn.setStyleSheet(self._get_toolbar_button_style('REBA', reba_visible, True))
        self._owas_btn.setChecked(owas_visible)
        self._owas_btn.setStyleSheet(self._get_toolbar_button_style('OWAS', owas_visible, True))
        # 안전지표 비활성 시 RULA/REBA/OWAS 버튼도 비활성
        if not ergonomic_visible:
            self._rula_btn.setEnabled(False)
            self._reba_btn.setEnabled(False)
            self._owas_btn.setEnabled(False)

    def _save_settings(self):
        """설정 저장"""
        self._settings.setValue("recent_files", self._recent_files)
        self._settings.setValue("recent_projects", self._recent_projects)
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
        """패널 가시성 변경 시 메뉴 및 툴바 동기화"""
        if panel == 'angle':
            self._angle_action.setChecked(visible)
            self._status_btn.setChecked(visible)
            self._status_btn.setStyleSheet(self._get_toolbar_button_style('상태', visible))
        elif panel == 'ergonomic':
            self._ergonomic_action.setChecked(visible)
            self._safety_btn.setChecked(visible)
            self._safety_btn.setStyleSheet(self._get_toolbar_button_style('안전지표', visible))
        elif panel == 'spreadsheet':
            self._spreadsheet_action.setChecked(visible)
            self._data_btn.setChecked(visible)
            self._data_btn.setStyleSheet(self._get_toolbar_button_style('데이터', visible))

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

    def _load_video(self, file_path: str, from_project_load: bool = False):
        """
        비디오 로드

        Args:
            file_path: 비디오 파일 경로
            from_project_load: 프로젝트 로드에서 호출된 경우 True (경고 건너뜀)
        """
        self._logger.info(f"비디오 로드 요청: {file_path} (프로젝트 로드: {from_project_load})")

        # 프로젝트 로드에서 호출된 경우가 아닐 때 초기화 처리
        if not from_project_load:
            # 기존 캡처 데이터가 있는 경우 확인
            record_count = self.status_widget.spreadsheet_widget.get_record_count()
            if record_count > 0:
                from PyQt6.QtWidgets import QStyle
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("기존 데이터 확인")
                msg_box.setText(
                    f"현재 {record_count}개의 캡처 데이터가 있습니다.\n\n"
                    "새 동영상을 로드하면 기존 데이터가 삭제됩니다.\n"
                    "계속하시겠습니까?"
                )
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
                msg_box.setIconPixmap(icon.pixmap(64, 64))
                save_btn = msg_box.addButton("저장 후 진행", QMessageBox.ButtonRole.AcceptRole)
                discard_btn = msg_box.addButton("삭제 후 진행", QMessageBox.ButtonRole.DestructiveRole)
                cancel_btn = msg_box.addButton("취소", QMessageBox.ButtonRole.RejectRole)
                msg_box.setDefaultButton(save_btn)
                msg_box.exec()

                if msg_box.clickedButton() == cancel_btn:
                    return
                elif msg_box.clickedButton() == save_btn:
                    if not self._save_project():
                        return

            # 기존 데이터 정리
            self._cleanup_capture_images()
            self.status_widget.spreadsheet_widget.clear_all()
            self.player_widget.stop()

        if self.player_widget.load_video(file_path):
            self._add_recent_file(file_path)
            self._status_bar.showMessage(f"로드됨: {file_path}")

            # 새 동영상이므로 프로젝트 상태 초기화
            if not from_project_load:
                self._project_manager.new_project()
                self._update_window_title()
        else:
            self._logger.error(f"비디오 로드 실패: {file_path}")
            QMessageBox.warning(self, "오류", f"파일을 열 수 없습니다:\n{file_path}")

    def _cleanup_capture_images(self, silent: bool = False):
        """
        캡처 이미지 디렉토리 정리 (삭제)

        프로젝트 경로 또는 비디오 이름 기반으로 캡처 디렉토리를 찾아 삭제합니다.

        Args:
            silent: True이면 에러 무시, False이면 상태바에 에러 표시
        """
        import shutil

        capture_base = Path(self._config.get(
            "directories.capture_save",
            "captures"
        ))

        # 정리할 디렉토리 목록
        dirs_to_clean = []

        # 1. 프로젝트 경로 기반 (captures/{project_name}/)
        if self._project_manager.current_path:
            project_dir = capture_base / self._project_manager.current_path.stem
            dirs_to_clean.append(('project', project_dir))
            self._logger.debug(f"프로젝트 기반 정리 대상: {project_dir}")

        # 2. 비디오 이름 기반 (captures/{video_name}/)
        if self._video_name:
            video_dir = capture_base / self._video_name
            # 프로젝트 디렉토리와 다른 경우에만 추가
            if not dirs_to_clean or dirs_to_clean[0][1] != video_dir:
                dirs_to_clean.append(('video', video_dir))
                self._logger.debug(f"비디오 기반 정리 대상: {video_dir}")

        # 디렉토리 정리
        for source, capture_dir in dirs_to_clean:
            if capture_dir.exists():
                try:
                    shutil.rmtree(capture_dir)
                    self._logger.info(f"캡처 이미지 삭제 완료 ({source}): {capture_dir}")
                except Exception as e:
                    self._logger.error(f"캡처 이미지 삭제 실패 ({source}): {capture_dir}, 오류: {e}")
                    if not silent:
                        self._status_bar.showMessage(f"이미지 삭제 실패: {e}")

    def _cleanup_all_captures(self):
        """
        captures 디렉토리 전체 정리

        앱 시작 시 또는 정상 종료 시 호출하여 모든 캡처 이미지를 삭제합니다.
        - 앱 시작 시: 비정상 종료로 남은 고아 이미지 정리
        - 정상 종료 시: 저장되지 않은 이미지 정리
        """
        import shutil

        capture_base = Path(self._config.get(
            "directories.capture_save",
            "captures"
        ))

        if capture_base.exists():
            try:
                shutil.rmtree(capture_base)
                self._logger.info(f"captures 전체 삭제 완료: {capture_base}")
            except Exception as e:
                self._logger.error(f"captures 전체 삭제 실패: {capture_base}, 오류: {e}")

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
        from PyQt6.QtWidgets import QStyle

        self._logger.info("앱 종료 요청")

        # 저장되지 않은 변경사항 확인
        if self._project_manager.is_dirty:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("저장되지 않은 변경사항")
            msg_box.setText(
                "저장되지 않은 변경사항이 있습니다.\n\n"
                "저장하지 않으면 캡처 이미지도 함께 삭제됩니다.\n"
                "저장하시겠습니까?"
            )
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
            msg_box.setIconPixmap(icon.pixmap(64, 64))
            save_btn = msg_box.addButton("저장", QMessageBox.ButtonRole.AcceptRole)
            discard_btn = msg_box.addButton("저장 안 함", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg_box.addButton("취소", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(save_btn)
            msg_box.exec()

            if msg_box.clickedButton() == cancel_btn:
                event.ignore()
                return
            elif msg_box.clickedButton() == save_btn:
                if not self._save_project():
                    event.ignore()
                    return
            # 저장 안 함: 저장 안 하고 종료 진행 (정리는 종료 시 일괄 처리)

        # 종료 확인 다이얼로그
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("종료 확인")
        msg_box.setText("앱을 종료하시겠습니까?")
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
        msg_box.setIconPixmap(icon.pixmap(64, 64))
        yes_btn = msg_box.addButton("예", QMessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton("아니오", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(no_btn)
        msg_box.exec()

        if msg_box.clickedButton() != yes_btn:
            self._logger.debug("사용자가 종료 취소")
            event.ignore()
            return

        self._logger.info("앱 종료 진행")
        self._save_settings()
        self.player_widget.release()

        # 정상 종료 시 captures 전체 정리
        self._cleanup_all_captures()

        self._logger.info("앱 종료 완료")
        super().closeEvent(event)

    # === 프로젝트 관련 메서드 ===

    def _update_window_title(self):
        """윈도우 타이틀 업데이트"""
        title = APP_NAME
        if self._project_manager.project_name:
            title = f"{self._project_manager.project_name} - {APP_NAME}"
            if self._project_manager.is_dirty:
                title = f"*{title}"
        self.setWindowTitle(title)

    def _update_recent_projects_menu(self):
        """최근 프로젝트 메뉴 업데이트"""
        self._recent_projects_menu.clear()

        for project_path in self._recent_projects:
            action = QAction(project_path, self)
            action.triggered.connect(
                lambda checked, fp=project_path: self._load_project(fp)
            )
            self._recent_projects_menu.addAction(action)

        self._recent_projects_menu.setEnabled(len(self._recent_projects) > 0)

    def _add_recent_project(self, project_path: str):
        """최근 프로젝트 목록에 추가"""
        if project_path in self._recent_projects:
            self._recent_projects.remove(project_path)
        self._recent_projects.insert(0, project_path)
        self._recent_projects = self._recent_projects[:self.MAX_RECENT_FILES]
        self._update_recent_projects_menu()

    def _new_project(self):
        """새 프로젝트"""
        # 저장되지 않은 변경사항 확인
        if self._project_manager.is_dirty:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("저장되지 않은 변경사항")
            msg_box.setText("저장되지 않은 변경사항이 있습니다.\n저장하시겠습니까?")
            save_btn = msg_box.addButton("저장", QMessageBox.ButtonRole.AcceptRole)
            discard_btn = msg_box.addButton("저장 안 함", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg_box.addButton("취소", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(save_btn)
            msg_box.exec()

            if msg_box.clickedButton() == cancel_btn:
                return
            elif msg_box.clickedButton() == save_btn:
                if not self._save_project():
                    return

        # 상태 초기화
        self._project_manager.new_project()
        self.status_widget.spreadsheet_widget.clear_all()
        self.player_widget.release()
        self._update_window_title()
        self._status_bar.showMessage("새 프로젝트")

    def _open_project(self):
        """프로젝트 열기 다이얼로그"""
        # 저장되지 않은 변경사항 확인
        if self._project_manager.is_dirty:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("저장되지 않은 변경사항")
            msg_box.setText("저장되지 않은 변경사항이 있습니다.\n저장하시겠습니까?")
            save_btn = msg_box.addButton("저장", QMessageBox.ButtonRole.AcceptRole)
            discard_btn = msg_box.addButton("저장 안 함", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg_box.addButton("취소", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(save_btn)
            msg_box.exec()

            if msg_box.clickedButton() == cancel_btn:
                return
            elif msg_box.clickedButton() == save_btn:
                if not self._save_project():
                    return

        default_dir = self._config.get("directories.project_open", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "프로젝트 열기",
            default_dir,
            "Skeleton Analyzer 프로젝트 (*.skpx);;모든 파일 (*.*)"
        )

        if file_path:
            self._load_project(file_path)

    def _load_project(self, file_path: str):
        """프로젝트 로드"""
        self._logger.info(f"프로젝트 로드 시작: {file_path}")
        try:
            # 캡처 디렉토리 설정
            capture_dir = Path(self._config.get(
                "directories.capture_save",
                "captures"
            ))
            self._logger.info(f"[썸네일] capture_dir 설정값: {capture_dir}, 절대경로: {capture_dir.absolute()}")

            info = self._project_manager.load(
                Path(file_path),
                check_video=True,
                capture_dir=capture_dir,
            )
            self._logger.info(f"[썸네일] 프로젝트 로드 결과: capture_count={info.capture_count}, image_count={info.image_count}")

            state = self._project_manager.get_state()
            self._logger.info(f"[썸네일] capture_model 존재 여부: {state['capture_model'] is not None}")

            # 동영상 누락 시 처리
            if info.video_missing:
                from PyQt6.QtWidgets import QStyle
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("동영상 파일 없음")
                msg_box.setText(
                    f"동영상 파일을 찾을 수 없습니다:\n{info.video_path}\n\n"
                    f"복원 가능한 항목:\n"
                    f"• 캡처 데이터: {info.capture_count}개\n"
                    f"• 이미지: {info.image_count}개\n\n"
                    "동영상 없이 데이터만 복원하시겠습니까?"
                )
                # 물음표 아이콘 사용
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
                msg_box.setIconPixmap(icon.pixmap(64, 64))
                yes_btn = msg_box.addButton("예", QMessageBox.ButtonRole.YesRole)
                cancel_btn = msg_box.addButton("취소", QMessageBox.ButtonRole.RejectRole)
                msg_box.setDefaultButton(yes_btn)
                msg_box.exec()

                if msg_box.clickedButton() != yes_btn:
                    return
                # 예 선택 시 동영상 없이 데이터만 복원

            elif state['video_path']:
                # 동영상 로드 (프로젝트 로드에서 호출)
                self._load_video(state['video_path'], from_project_load=True)
                # 프레임 위치 복원
                if state['frame_position'] > 0:
                    self.player_widget.seek_to_frame(state['frame_position'])

            # 캡처 데이터 복원
            if state['capture_model']:
                self.status_widget.spreadsheet_widget.load_from_model(
                    state['capture_model']
                )

            # UI 상태 복원
            self._restore_ui_state(state['ui_state'])

            self._add_recent_project(file_path)
            self._update_window_title()
            self._status_bar.showMessage(f"프로젝트 로드됨: {file_path}")
            self._logger.info(f"프로젝트 로드 완료: 캡처 {info.capture_count}개, 이미지 {info.image_count}개")

        except ProjectLoadError as e:
            self._logger.error(f"프로젝트 로드 실패: {file_path}, 오류: {e}")
            QMessageBox.critical(self, "프로젝트 로드 오류", str(e))

    def _save_project(self) -> bool:
        """프로젝트 저장"""
        if self._project_manager.current_path is None:
            return self._save_project_as()

        return self._do_save_project(self._project_manager.current_path)

    def _save_project_as(self) -> bool:
        """다른 이름으로 저장"""
        default_name = ""
        if self._video_name:
            default_name = f"{self._video_name}.skpx"

        default_dir = self._config.get("directories.project_save", "")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "프로젝트 저장",
            os.path.join(default_dir, default_name),
            "Skeleton Analyzer 프로젝트 (*.skpx)"
        )

        if file_path:
            if not file_path.endswith('.skpx'):
                file_path += '.skpx'
            return self._do_save_project(Path(file_path))

        return False

    def _do_save_project(self, path: Path) -> bool:
        """실제 프로젝트 저장 수행"""
        self._logger.info(f"프로젝트 저장 시작: {path}")
        try:
            # 현재 상태 수집
            capture_dir = Path(self._config.get(
                "directories.capture_save",
                "captures"
            ))

            self._project_manager.set_state(
                video_path=self.player_widget.get_video_path(),
                frame_position=self.player_widget.get_current_frame_number(),
                fps=self.player_widget.get_fps(),
                capture_model=self.status_widget.spreadsheet_widget.get_model(),
                ui_state=self._collect_ui_state(),
                capture_dir=capture_dir,
            )

            if self._project_manager.save(path):
                self._add_recent_project(str(path))
                self._update_window_title()
                self._status_bar.showMessage(f"프로젝트 저장됨: {path}")
                self._logger.info(f"프로젝트 저장 완료: {path}")
                return True

        except Exception as e:
            self._logger.error(f"프로젝트 저장 실패: {path}, 오류: {e}")
            QMessageBox.critical(self, "저장 오류", f"프로젝트 저장 실패:\n{e}")

        return False

    def _collect_ui_state(self) -> dict:
        """현재 UI 상태 수집"""
        return {
            'panels': {
                'angle': self.status_widget.is_angle_visible(),
                'ergonomic': self.status_widget.is_ergonomic_visible(),
                'spreadsheet': self.status_widget.is_spreadsheet_visible(),
                'rula': self.status_widget.is_rula_visible(),
                'reba': self.status_widget.is_reba_visible(),
                'owas': self.status_widget.is_owas_visible(),
            },
            'splitter_sizes': {
                'main': self._splitter.sizes(),
            },
        }

    def _restore_ui_state(self, ui_state: dict):
        """UI 상태 복원"""
        if not ui_state:
            return

        panels = ui_state.get('panels', {})
        if 'angle' in panels:
            self.status_widget.set_angle_visible(panels['angle'])
            self._angle_action.setChecked(panels['angle'])
        if 'ergonomic' in panels:
            self.status_widget.set_ergonomic_visible(panels['ergonomic'])
            self._ergonomic_action.setChecked(panels['ergonomic'])
        if 'spreadsheet' in panels:
            self.status_widget.set_spreadsheet_visible(panels['spreadsheet'])
            self._spreadsheet_action.setChecked(panels['spreadsheet'])
        if 'rula' in panels:
            self.status_widget.set_rula_visible(panels['rula'])
        if 'reba' in panels:
            self.status_widget.set_reba_visible(panels['reba'])
        if 'owas' in panels:
            self.status_widget.set_owas_visible(panels['owas'])

        splitter_sizes = ui_state.get('splitter_sizes', {})
        if 'main' in splitter_sizes:
            self._splitter.setSizes(splitter_sizes['main'])

    def _mark_project_dirty(self):
        """프로젝트를 dirty로 표시"""
        self._project_manager.mark_dirty()
        self._update_window_title()

    @property
    def _video_name(self) -> Optional[str]:
        """현재 비디오 이름"""
        return self.status_widget._video_name
