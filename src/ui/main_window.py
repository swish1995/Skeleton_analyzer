"""메인 윈도우 모듈"""
import os
import platform
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox,
    QToolBar, QToolButton, QSlider, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QPixmap, QPainter
from typing import Optional, List

from .player_widget import PlayerWidget
from .status_widget import StatusWidget
from .settings_dialog import SettingsDialog
from .help_dialog import HelpDialog
from .analysis_progress_dialog import AnalysisProgressDialog
from ..utils.config import Config
from ..core.project_manager import ProjectManager, ProjectLoadError, LoadResult
from ..core.image_slide_player import ImageSlidePlayer
from ..core.logger import get_logger
from ..license import LicenseManager, LicenseMode
from ..license.license_dialog import LicenseDialog

# 앱 이름 (환경변수로 변경 가능)
APP_NAME = os.environ.get('SKELETON_ANALYZER_APP_NAME', 'Skeleton Analyzer')


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""

    MAX_RECENT_FILES = 10

    def __init__(self):
        super().__init__()
        self._logger = get_logger('main_window')
        self._logger.info("MainWindow 초기화")

        self._recent_files: List[str] = []
        self._recent_projects: List[str] = []
        self._settings = QSettings("SkeletonAnalyzer", "SkeletonAnalyzer")
        self._config = Config()
        self._project_manager = ProjectManager()

        # 라이센스 매니저
        self._license_manager = LicenseManager.instance()
        self._license_manager.license_changed.connect(self._on_license_changed)

        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_shortcuts()
        self._load_settings()

        # 라이센스 상태에 따른 메뉴 업데이트
        self._update_menu_state()
        self._update_window_title()

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
        self.player_widget.setMinimumWidth(400)  # 플레이어 최소 너비
        self._splitter.addWidget(self.player_widget)

        # 오른쪽: 스테이터스 위젯
        self.status_widget = StatusWidget(config=self._config)
        self.status_widget.setMinimumWidth(500)  # 스테이터스 최소 너비
        self._splitter.addWidget(self.status_widget)

        # 스플리터로 패널이 완전히 축소되지 않도록 설정
        self._splitter.setCollapsible(0, False)  # 플레이어
        self._splitter.setCollapsible(1, False)  # 스테이터스

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
        self.player_widget.folder_open_requested.connect(self._load_images)
        self.player_widget.archive_open_requested.connect(self._load_archive)
        self.player_widget.source_loaded.connect(self._on_source_loaded)
        self.status_widget.exit_requested.connect(self.close)
        # 캡처 추가/변경 시 dirty 표시
        self.status_widget.capture_added.connect(self._mark_project_dirty)
        # 분석 요청 시그널
        self.status_widget.movement_analysis_widget.analysis_requested.connect(
            self._on_analysis_requested
        )
        # 분석 위젯 라이센스 등록 요청
        self.status_widget.movement_analysis_widget.register_requested.connect(
            self._show_license_dialog
        )
        # 스켈레톤 편집 모드 변경 시 영상 일시정지 연동
        self.status_widget._skeleton_widget.edit_mode_changed.connect(
            self._on_edit_mode_changed
        )

    def _init_menu(self):
        """메뉴 초기화"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")

        # 작업 불러오기
        self._open_project_action = QAction("작업 불러오기(&P)...", self)
        self._open_project_action.setShortcut("Ctrl+Shift+O")
        self._open_project_action.triggered.connect(self._open_project)
        file_menu.addAction(self._open_project_action)

        # 작업 저장
        self._save_project_action = QAction("작업 저장(&S)", self)
        self._save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        self._save_project_action.triggered.connect(self._save_project)
        file_menu.addAction(self._save_project_action)

        # 다른 이름으로 저장
        self._save_as_action = QAction("다른 이름으로 저장(&A)...", self)
        self._save_as_action.setShortcut("Ctrl+Shift+S")
        self._save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(self._save_as_action)

        file_menu.addSeparator()

        # 동영상 열기
        open_action = QAction("동영상 파일 열기(&O)...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        # 이미지 폴더 열기
        open_folder_action = QAction("폴더 열기(&I)...", self)
        open_folder_action.triggered.connect(self._open_image_folder)
        file_menu.addAction(open_folder_action)

        # 압축 파일 열기
        open_archive_action = QAction("파일 열기(&Z)...", self)
        open_archive_action.triggered.connect(self._open_archive_file)
        file_menu.addAction(open_archive_action)

        file_menu.addSeparator()

        # 최근 작업 서브메뉴
        self._recent_projects_menu = file_menu.addMenu("최근 작업")
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

        # 분석 결과 패널
        self._analysis_result_action = QAction("분석 결과(&R)", self)
        self._analysis_result_action.setCheckable(True)
        self._analysis_result_action.setChecked(True)
        self._analysis_result_action.setShortcut("Ctrl+3")
        self._analysis_result_action.triggered.connect(
            lambda checked: self.status_widget.set_analysis_visible(checked)
        )
        view_menu.addAction(self._analysis_result_action)

        # 안전지표 패널
        self._ergonomic_action = QAction("안전지표(&E)", self)
        self._ergonomic_action.setCheckable(True)
        self._ergonomic_action.setChecked(True)
        self._ergonomic_action.setShortcut("Ctrl+4")
        self._ergonomic_action.triggered.connect(
            lambda checked: self.status_widget.set_ergonomic_visible(checked)
        )
        view_menu.addAction(self._ergonomic_action)

        # StatusWidget 가시성 변경 시 메뉴 동기화
        self.status_widget.visibility_changed.connect(self._on_visibility_changed)

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")

        # 사용 방법
        usage_action = QAction("사용 방법(&U)...", self)
        usage_action.setShortcut("F1")
        usage_action.triggered.connect(self._show_help_usage)
        help_menu.addAction(usage_action)

        help_menu.addSeparator()

        # 라이센스 등록
        self._license_action = QAction("라이센스 등록(&L)...", self)
        self._license_action.triggered.connect(self._show_license_dialog)
        help_menu.addAction(self._license_action)

        help_menu.addSeparator()

        # 프로그램 정보
        about_action = QAction("프로그램 정보(&A)...", self)
        about_action.setShortcut("Ctrl+F1")
        about_action.triggered.connect(self._show_help_about)
        help_menu.addAction(about_action)

    # 툴바 버튼 색상 정의
    TOOLBAR_BUTTON_COLORS = {
        'open': ('#b8a25a', '#a8924a', '#c8b26a'),     # 골드/노란색
        'save': ('#5ab87a', '#4aa86a', '#6ac88a'),     # 초록색
        '상태': ('#3a9a8a', '#2a8a7a', '#4aaa9a'),      # 틸색
        '데이터': ('#5a7ab8', '#4a6aa8', '#6a8ac8'),    # 파란색
        '분석 결과': ('#5ab8b8', '#4aa8a8', '#6ac8c8'),  # 시안색
        '안전지표': ('#8a5ab8', '#7a4aa8', '#9a6ac8'),  # 보라색
        'RULA': ('#b8825a', '#a8724a', '#c8926a'),      # 주황색
        'REBA': ('#5ab87a', '#4aa86a', '#6ac88a'),      # 초록색
        'OWAS': ('#b85a6a', '#a84a5a', '#c86a7a'),      # 빨간색
        'NLE': ('#5a8ab8', '#4a7aa8', '#6a9ac8'),       # 하늘색
        'SI': ('#b8a85a', '#a8984a', '#c8b86a'),        # 황금색
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

        # 작업 불러오기 버튼
        self._open_btn = QPushButton(" 작업 불러오기")
        self._open_btn.setIcon(QIcon(self._get_icon_path("folder_open")))
        self._open_btn.setIconSize(QSize(14, 14))
        self._open_btn.setFixedHeight(28)
        self._open_btn.setToolTip("작업 불러오기 (Ctrl+Shift+O)")
        self._open_btn.setStyleSheet(self._get_toolbar_button_style('open'))
        self._open_btn.clicked.connect(self._open_project)
        self._toolbar.addWidget(self._open_btn)

        # 작업 저장 버튼
        self._save_btn = QPushButton(" 작업 저장")
        self._save_btn.setIcon(QIcon(self._get_icon_path("save")))
        self._save_btn.setIconSize(QSize(14, 14))
        self._save_btn.setFixedHeight(28)
        self._save_btn.setToolTip("작업 저장 (Ctrl+S)")
        self._save_btn.setStyleSheet(self._get_toolbar_button_style('save'))
        self._save_btn.clicked.connect(self._save_project)
        self._toolbar.addWidget(self._save_btn)

        # ── 민감도 슬라이더 ──
        sensitivity_container = QWidget()
        sensitivity_layout = QHBoxLayout(sensitivity_container)
        sensitivity_layout.setContentsMargins(8, 0, 0, 0)
        sensitivity_layout.setSpacing(4)

        sensitivity_label = QLabel("민감도:")
        sensitivity_label.setStyleSheet("color: #999999; font-size: 11px;")
        sensitivity_layout.addWidget(sensitivity_label)

        self._sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self._sensitivity_slider.setRange(0, 100)
        self._sensitivity_slider.setValue(0)
        self._sensitivity_slider.setFixedWidth(100)
        self._sensitivity_slider.setFixedHeight(20)
        self._sensitivity_slider.setToolTip("감지 민감도\n0.0 = 정확한 값, 1.0 = 대부분의 자세가 최소 점수")
        self._sensitivity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #555;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 12px;
                margin: -4px 0;
                background: #aaa;
                border-radius: 6px;
            }
        """)
        sensitivity_layout.addWidget(self._sensitivity_slider)

        self._sensitivity_value_label = QLabel("0.0")
        self._sensitivity_value_label.setFixedWidth(24)
        self._sensitivity_value_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        sensitivity_layout.addWidget(self._sensitivity_value_label)

        self._sensitivity_slider.valueChanged.connect(self._on_sensitivity_changed)
        self._toolbar.addWidget(sensitivity_container)

        # 민감도와 보기 사이 간격
        project_spacer = QWidget()
        project_spacer.setFixedWidth(8)
        self._toolbar.addWidget(project_spacer)

        # 보기 라벨
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

        # 분석 결과 버튼 (토글)
        self._analysis_result_btn = QPushButton(f" 분석 결과 ({shortcut_prefix}3)")
        self._analysis_result_btn.setIcon(QIcon(self._get_icon_path("analysis")))
        self._analysis_result_btn.setIconSize(QSize(14, 14))
        self._analysis_result_btn.setFixedHeight(28)
        self._analysis_result_btn.setCheckable(True)
        self._analysis_result_btn.setChecked(True)
        self._analysis_result_btn.setStyleSheet(self._get_toolbar_button_style('분석 결과', True))
        self._analysis_result_btn.toggled.connect(self._on_analysis_result_toggled)
        self._toolbar.addWidget(self._analysis_result_btn)

        # 안전지표 버튼 (토글)
        self._safety_btn = QPushButton(f" 안전지표 ({shortcut_prefix}4)")
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

        # NLE 버튼 (서브 토글) - 기본 비활성
        self._nle_btn = QPushButton("NLE")
        self._nle_btn.setFixedHeight(28)
        self._nle_btn.setCheckable(True)
        self._nle_btn.setChecked(False)
        self._nle_btn.setStyleSheet(self._get_toolbar_button_style('NLE', False, True))
        self._nle_btn.toggled.connect(self._on_nle_toggled)
        self._toolbar.addWidget(self._nle_btn)

        # SI 버튼 (서브 토글) - 기본 비활성
        self._si_btn = QPushButton("SI")
        self._si_btn.setFixedHeight(28)
        self._si_btn.setCheckable(True)
        self._si_btn.setChecked(False)
        self._si_btn.setStyleSheet(self._get_toolbar_button_style('SI', False, True))
        self._si_btn.toggled.connect(self._on_si_toggled)
        self._toolbar.addWidget(self._si_btn)

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

    def _on_analysis_result_toggled(self, checked: bool):
        """분석 결과 패널 토글"""
        self.status_widget.set_analysis_visible(checked)
        self._analysis_result_btn.setStyleSheet(self._get_toolbar_button_style('분석 결과', checked))
        self._analysis_result_action.setChecked(checked)

    def _on_safety_toggled(self, checked: bool):
        """안전지표 패널 토글"""
        self.status_widget.set_ergonomic_visible(checked)
        self._safety_btn.setStyleSheet(self._get_toolbar_button_style('안전지표', checked))
        self._safety_btn.setIcon(self._get_icon_with_opacity("safety", 1.0 if checked else 0.6))
        self._ergonomic_action.setChecked(checked)
        # RULA/REBA/OWAS/NLE/SI 버튼 활성/비활성
        self._rula_btn.setEnabled(checked)
        self._reba_btn.setEnabled(checked)
        self._owas_btn.setEnabled(checked)
        self._nle_btn.setEnabled(checked)
        self._si_btn.setEnabled(checked)

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

    def _on_nle_toggled(self, checked: bool):
        """NLE 패널 토글"""
        self.status_widget.set_nle_visible(checked)
        self._nle_btn.setStyleSheet(self._get_toolbar_button_style('NLE', checked, True))

    def _on_si_toggled(self, checked: bool):
        """SI 패널 토글"""
        self.status_widget.set_si_visible(checked)
        self._si_btn.setStyleSheet(self._get_toolbar_button_style('SI', checked, True))

    def _init_shortcuts(self):
        """단축키 초기화"""
        # 스페이스바: 재생/일시정지
        # PlayerWidget에서 처리

    def _load_settings(self):
        """설정 로드"""
        # 최근 파일 목록
        self._recent_files = self._settings.value("recent_files", [], type=list)
        self._recent_projects = self._settings.value("recent_projects", [], type=list)

        # 민감도 슬라이더
        sensitivity = self._settings.value("detection_sensitivity", 0, type=int)
        self._sensitivity_slider.setValue(sensitivity)
        self._on_sensitivity_changed(sensitivity)

        # 윈도우 크기/위치
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # 스플리터 상태
        splitter_state = self._settings.value("splitter_state")
        if splitter_state:
            self._splitter.restoreState(splitter_state)

        # 내부 스플리터 상태 복원
        internal_states = {}
        for key in ('main', 'top', 'middle'):
            state = self._settings.value(f"status_splitter_{key}")
            if state:
                internal_states[key] = state
        if internal_states:
            self.status_widget.restore_splitter_states(internal_states)

        # 패널 가시성 로드
        angle_visible = self._settings.value("panel_angle", True, type=bool)
        analysis_visible = self._settings.value("panel_analysis", True, type=bool)
        ergonomic_visible = self._settings.value("panel_ergonomic", True, type=bool)
        spreadsheet_visible = self._settings.value("panel_spreadsheet", True, type=bool)
        rula_visible = self._settings.value("panel_rula", True, type=bool)
        reba_visible = self._settings.value("panel_reba", True, type=bool)
        owas_visible = self._settings.value("panel_owas", True, type=bool)
        nle_visible = self._settings.value("panel_nle", False, type=bool)
        si_visible = self._settings.value("panel_si", False, type=bool)

        self.status_widget.set_angle_visible(angle_visible)
        self.status_widget.set_analysis_visible(analysis_visible)
        self.status_widget.set_ergonomic_visible(ergonomic_visible)
        self.status_widget.set_spreadsheet_visible(spreadsheet_visible)
        self.status_widget.set_rula_visible(rula_visible)
        self.status_widget.set_reba_visible(reba_visible)
        self.status_widget.set_owas_visible(owas_visible)
        self.status_widget.set_nle_visible(nle_visible)
        self.status_widget.set_si_visible(si_visible)

        # 메뉴 체크 상태 동기화
        self._angle_action.setChecked(angle_visible)
        self._analysis_result_action.setChecked(analysis_visible)
        self._ergonomic_action.setChecked(ergonomic_visible)
        self._spreadsheet_action.setChecked(spreadsheet_visible)

        # 툴바 버튼 상태 동기화
        self._status_btn.setChecked(angle_visible)
        self._status_btn.setStyleSheet(self._get_toolbar_button_style('상태', angle_visible))
        self._data_btn.setChecked(spreadsheet_visible)
        self._data_btn.setStyleSheet(self._get_toolbar_button_style('데이터', spreadsheet_visible))
        self._analysis_result_btn.setChecked(analysis_visible)
        self._analysis_result_btn.setStyleSheet(self._get_toolbar_button_style('분석 결과', analysis_visible))
        self._safety_btn.setChecked(ergonomic_visible)
        self._safety_btn.setStyleSheet(self._get_toolbar_button_style('안전지표', ergonomic_visible))
        self._rula_btn.setChecked(rula_visible)
        self._rula_btn.setStyleSheet(self._get_toolbar_button_style('RULA', rula_visible, True))
        self._reba_btn.setChecked(reba_visible)
        self._reba_btn.setStyleSheet(self._get_toolbar_button_style('REBA', reba_visible, True))
        self._owas_btn.setChecked(owas_visible)
        self._owas_btn.setStyleSheet(self._get_toolbar_button_style('OWAS', owas_visible, True))
        self._nle_btn.setChecked(nle_visible)
        self._nle_btn.setStyleSheet(self._get_toolbar_button_style('NLE', nle_visible, True))
        self._si_btn.setChecked(si_visible)
        self._si_btn.setStyleSheet(self._get_toolbar_button_style('SI', si_visible, True))
        # 안전지표 비활성 시 RULA/REBA/OWAS/NLE/SI 버튼도 비활성
        if not ergonomic_visible:
            self._rula_btn.setEnabled(False)
            self._reba_btn.setEnabled(False)
            self._owas_btn.setEnabled(False)
            self._nle_btn.setEnabled(False)
            self._si_btn.setEnabled(False)

    def _save_settings(self):
        """설정 저장"""
        self._settings.setValue("recent_files", self._recent_files)
        self._settings.setValue("recent_projects", self._recent_projects)
        self._settings.setValue("detection_sensitivity", self._sensitivity_slider.value())
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("splitter_state", self._splitter.saveState())

        # 내부 스플리터 상태 저장
        internal_states = self.status_widget.save_splitter_states()
        for key, state in internal_states.items():
            self._settings.setValue(f"status_splitter_{key}", state)

        # 패널 가시성 저장
        self._settings.setValue("panel_angle", self.status_widget.is_angle_visible())
        self._settings.setValue("panel_analysis", self.status_widget.is_analysis_visible())
        self._settings.setValue("panel_ergonomic", self.status_widget.is_ergonomic_visible())
        self._settings.setValue("panel_spreadsheet", self.status_widget.is_spreadsheet_visible())
        self._settings.setValue("panel_rula", self.status_widget.is_rula_visible())
        self._settings.setValue("panel_reba", self.status_widget.is_reba_visible())
        self._settings.setValue("panel_owas", self.status_widget.is_owas_visible())
        self._settings.setValue("panel_nle", self.status_widget.is_nle_visible())
        self._settings.setValue("panel_si", self.status_widget.is_si_visible())

    def _on_visibility_changed(self, panel: str, visible: bool):
        """패널 가시성 변경 시 메뉴 및 툴바 동기화"""
        if panel == 'angle':
            self._angle_action.setChecked(visible)
            self._status_btn.setChecked(visible)
            self._status_btn.setStyleSheet(self._get_toolbar_button_style('상태', visible))
        elif panel == 'analysis':
            self._analysis_result_action.setChecked(visible)
            self._analysis_result_btn.setChecked(visible)
            self._analysis_result_btn.setStyleSheet(self._get_toolbar_button_style('분석 결과', visible))
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
            self.status_widget.movement_analysis_widget.reset_to_ready()
            self.player_widget.stop()

        if self.player_widget.load_video(file_path):
            self._add_recent_file(file_path)
            self._status_bar.showMessage(f"로드됨: {file_path}")

            # 새 동영상이므로 프로젝트 상태 초기화
            if not from_project_load:
                self._project_manager.new_project()
                self._update_window_title()

            # 포커스를 플레이어로 설정 (엔터키 캡처가 동작하도록)
            self.player_widget.setFocus()
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

        # 2. 비디오 이름 기반 (captures/{video_name}/)
        if self._video_name:
            video_dir = capture_base / self._video_name
            # 프로젝트 디렉토리와 다른 경우에만 추가
            if not dirs_to_clean or dirs_to_clean[0][1] != video_dir:
                dirs_to_clean.append(('video', video_dir))

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
        captures 및 temp_images 디렉토리 전체 정리

        앱 시작 시 또는 정상 종료 시 호출하여 모든 임시 파일을 삭제합니다.
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

        # 압축 파일 해제 임시 디렉토리 정리
        ImageSlidePlayer.cleanup_all_temp()
        self._logger.info("temp_images 전체 삭제 완료")

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

        # 분석 위젯에 동영상 정보 전달
        video_path = self.player_widget.get_video_path()
        total_frames = self.player_widget._video_player.frame_count
        if video_path and total_frames > 0:
            self.status_widget.movement_analysis_widget.set_video_info(
                video_path, total_frames
            )

    def _on_source_loaded(self, source_name: str):
        """이미지 소스 로드 시 호출 (폴더/압축파일)"""
        self.status_widget.set_video_name(source_name)

    def _open_image_folder(self):
        """폴더 열기 다이얼로그"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "폴더 열기",
            "",
        )
        if folder_path:
            self._load_images(folder_path)

    def _open_archive_file(self):
        """파일 열기 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "파일 열기",
            "",
            "압축 파일 (*.zip);;모든 파일 (*.*)"
        )
        if file_path:
            self._load_archive(file_path)

    def _load_images(self, folder_path: str, from_project_load: bool = False):
        """이미지 폴더 로드"""
        self._logger.info(f"이미지 폴더 로드 요청: {folder_path}")

        if not from_project_load:
            record_count = self.status_widget.spreadsheet_widget.get_record_count()
            if record_count > 0:
                from PyQt6.QtWidgets import QStyle
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("기존 데이터 확인")
                msg_box.setText(
                    f"현재 {record_count}개의 캡처 데이터가 있습니다.\n\n"
                    "새 이미지를 로드하면 기존 데이터가 삭제됩니다.\n"
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

            self._cleanup_capture_images()
            self.status_widget.spreadsheet_widget.clear_all()
            self.status_widget.movement_analysis_widget.reset_to_ready()
            self.player_widget.stop()

        if self.player_widget.load_images(folder_path):
            self._status_bar.showMessage(f"이미지 폴더 로드됨: {folder_path}")

            if not from_project_load:
                self._project_manager.new_project()
                self._update_window_title()

            self.player_widget.setFocus()
        else:
            self._logger.error(f"이미지 폴더 로드 실패: {folder_path}")
            QMessageBox.warning(self, "오류", f"이미지 폴더를 열 수 없습니다:\n{folder_path}")

    def _load_archive(self, archive_path: str, from_project_load: bool = False):
        """압축 파일 로드"""
        self._logger.info(f"압축 파일 로드 요청: {archive_path}")

        if not from_project_load:
            record_count = self.status_widget.spreadsheet_widget.get_record_count()
            if record_count > 0:
                from PyQt6.QtWidgets import QStyle
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("기존 데이터 확인")
                msg_box.setText(
                    f"현재 {record_count}개의 캡처 데이터가 있습니다.\n\n"
                    "새 압축 파일을 로드하면 기존 데이터가 삭제됩니다.\n"
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

            self._cleanup_capture_images()
            self.status_widget.spreadsheet_widget.clear_all()
            self.status_widget.movement_analysis_widget.reset_to_ready()
            self.player_widget.stop()

        if self.player_widget.load_archive(archive_path):
            self._status_bar.showMessage(f"압축 파일 로드됨: {archive_path}")

            if not from_project_load:
                self._project_manager.new_project()
                self._update_window_title()

            self.player_widget.setFocus()
        else:
            self._logger.error(f"압축 파일 로드 실패: {archive_path}")
            QMessageBox.warning(self, "오류", f"압축 파일을 열 수 없습니다:\n{archive_path}")

    def _on_edit_mode_changed(self, enabled: bool):
        """스켈레톤 편집 모드 변경 시"""
        if enabled:
            self.player_widget.pause()

    def _on_frame_changed(self, frame, frame_number: int):
        """프레임 변경 시 호출"""
        if frame is not None:
            # 동영상 재생 중이면 편집 모드 강제 해제
            if self.status_widget._skeleton_widget.is_edit_mode:
                self.status_widget._skeleton_widget.exit_edit_mode()

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
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.player_widget._on_capture_clicked()
        elif self.player_widget.mode == PlayerWidget.MODE_VIDEO:
            # 동영상 모드 전용 단축키
            if event.key() == Qt.Key.Key_Space:
                self.player_widget.toggle_play()
            elif event.key() == Qt.Key.Key_Left:
                self.player_widget.seek_relative(-5)  # 5초 뒤로
            elif event.key() == Qt.Key.Key_Right:
                self.player_widget.seek_relative(5)  # 5초 앞으로
            else:
                super().keyPressEvent(event)
        elif self.player_widget.mode == PlayerWidget.MODE_IMAGE:
            # 이미지 모드 전용 단축키
            if event.key() == Qt.Key.Key_Left:
                self.player_widget.navigate_prev()
            elif event.key() == Qt.Key.Key_Right:
                self.player_widget.navigate_next()
            else:
                super().keyPressEvent(event)
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
            self._logger.info("사용자가 종료 취소")
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

        # 라이센스 모드 표시
        mode = self._license_manager.license_mode
        if mode == LicenseMode.DEV:
            title = f"{title} [DEV]"
        elif mode == LicenseMode.LICENSED:
            title = f"{title} [LICENSED]"
        elif not self._license_manager.is_licensed:
            title = f"{title} [FREE]"

        if self._project_manager.project_name:
            title = f"{self._project_manager.project_name} - {title}"
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
            "작업 불러오기",
            default_dir,
            "Skeleton Analyzer 프로젝트 (*.skpx);;모든 파일 (*.*)"
        )

        if file_path:
            self._load_project(file_path)

    def _load_project(self, file_path: str):
        """프로젝트 로드"""
        self._logger.info(f"작업 로드 시작: {file_path}")
        try:
            capture_dir = Path(self._config.get(
                "directories.capture_save",
                "captures"
            ))
            info = self._project_manager.load(
                Path(file_path),
                check_video=True,
                capture_dir=capture_dir,
            )

            state = self._project_manager.get_state()
            source_type = state.get('source_type', 'video')
            source_path = state.get('source_path')

            # 소스 타입에 따라 분기
            if source_type == 'folder':
                # 이미지 폴더 복원
                if source_path and Path(source_path).exists():
                    self._load_images(source_path, from_project_load=True)
                    if state['frame_position'] > 0:
                        self.player_widget.seek_to_frame(state['frame_position'])
                else:
                    self._show_source_missing_dialog(source_path, "이미지 폴더", info)

            elif source_type == 'archive':
                # 압축 파일 복원
                if source_path and Path(source_path).exists():
                    self._load_archive(source_path, from_project_load=True)
                    if state['frame_position'] > 0:
                        self.player_widget.seek_to_frame(state['frame_position'])
                else:
                    self._show_source_missing_dialog(source_path, "압축 파일", info)

            else:
                # 동영상 모드 (기존 호환)
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
                    icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
                    msg_box.setIconPixmap(icon.pixmap(64, 64))
                    yes_btn = msg_box.addButton("예", QMessageBox.ButtonRole.YesRole)
                    cancel_btn = msg_box.addButton("취소", QMessageBox.ButtonRole.RejectRole)
                    msg_box.setDefaultButton(yes_btn)
                    msg_box.exec()

                    if msg_box.clickedButton() != yes_btn:
                        return

                elif state['video_path']:
                    self._load_video(state['video_path'], from_project_load=True)
                    if state['frame_position'] > 0:
                        self.player_widget.seek_to_frame(state['frame_position'])

            # 캡처 데이터 복원
            if state['capture_model']:
                self.status_widget.spreadsheet_widget.load_from_model(
                    state['capture_model']
                )

            # UI 상태 복원
            self._restore_ui_state(state['ui_state'])

            # 분석 결과 복원
            movement_result = state.get('movement_analysis_result')
            if movement_result:
                self.status_widget.movement_analysis_widget.set_result(
                    movement_result, video_missing=info.video_missing
                )

            self._add_recent_project(file_path)
            self._update_window_title()
            self._status_bar.showMessage(f"작업 로드됨: {file_path}")
            self._logger.info(f"작업 로드 완료: 캡처 {info.capture_count}개, 이미지 {info.image_count}개")
            QMessageBox.information(self, "작업 불러오기", f"작업을 불러왔습니다.\n캡처 {info.capture_count}개, 이미지 {info.image_count}개")

            self.player_widget.setFocus()

        except ProjectLoadError as e:
            self._logger.error(f"작업 로드 실패: {file_path}, 오류: {e}")
            QMessageBox.critical(self, "작업 로드 오류", str(e))

    def _show_source_missing_dialog(self, source_path, source_type_label: str, info):
        """소스 경로 누락 시 안내 다이얼로그"""
        from PyQt6.QtWidgets import QStyle
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"{source_type_label} 없음")
        msg_box.setText(
            f"{source_type_label}을 찾을 수 없습니다:\n{source_path}\n\n"
            f"복원 가능한 항목:\n"
            f"• 캡처 데이터: {info.capture_count}개\n"
            f"• 이미지: {info.image_count}개\n\n"
            f"{source_type_label} 없이 데이터만 복원합니다."
        )
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        msg_box.setIconPixmap(icon.pixmap(64, 64))
        msg_box.addButton("확인", QMessageBox.ButtonRole.AcceptRole)
        msg_box.exec()

    def _on_sensitivity_changed(self, value: int):
        """민감도 슬라이더 변경"""
        # 표시값: 0→0.0, 100→1.0 (현재값/최대값)
        display_value = value / 100.0
        self._sensitivity_value_label.setText(f"{display_value:.1f}")
        # 슬라이더 0→100 을 sensitivity 1.0→10.0 으로 매핑
        sensitivity = 1.0 + (value / 100.0) * 9.0
        # 모든 계산기에 적용
        ergonomic = self.status_widget._ergonomic_widget
        ergonomic._rula_calculator.detection_sensitivity = sensitivity
        ergonomic._reba_calculator.detection_sensitivity = sensitivity
        ergonomic._owas_calculator.detection_sensitivity = sensitivity
        # 실시간 재계산
        ergonomic.recalculate()

    def _save_project(self) -> bool:
        """프로젝트 저장"""
        if self._project_manager.current_path is None:
            return self._save_project_as()

        return self._do_save_project(self._project_manager.current_path)

    def _save_project_as(self) -> bool:
        """다른 이름으로 저장"""
        default_name = ""
        source_name = self.player_widget.source_name or self._video_name
        if source_name:
            default_name = f"{source_name}.skpx"

        default_dir = self._config.get("directories.project_save", "")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "작업 저장",
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
        self._logger.info(f"작업 저장 시작: {path}")
        try:
            capture_dir = Path(self._config.get(
                "directories.capture_save",
                "captures"
            ))

            # 소스 타입 결정
            if self.player_widget.mode == 'image' and self.player_widget.image_player.is_loaded:
                source_type = self.player_widget.image_player.source_type or 'folder'
            else:
                source_type = 'video'
            source_path = self.player_widget.get_source_path()

            self._project_manager.set_state(
                video_path=self.player_widget.get_video_path(),
                frame_position=self.player_widget.get_current_frame_number(),
                fps=self.player_widget.get_fps(),
                capture_model=self.status_widget.spreadsheet_widget.get_model(),
                ui_state=self._collect_ui_state(),
                capture_dir=capture_dir,
                movement_analysis_result=self.status_widget.movement_analysis_widget.get_result(),
                source_type=source_type,
                source_path=source_path,
            )

            if self._project_manager.save(path):
                self._add_recent_project(str(path))
                self._update_window_title()
                self._status_bar.showMessage(f"작업 저장됨: {path}")
                self._logger.info(f"작업 저장 완료: {path}")
                QMessageBox.information(self, "작업 저장", f"작업이 저장되었습니다.\n{path}")
                return True

        except Exception as e:
            self._logger.error(f"작업 저장 실패: {path}, 오류: {e}")
            QMessageBox.critical(self, "저장 오류", f"작업 저장 실패:\n{e}")

        return False

    def _collect_ui_state(self) -> dict:
        """현재 UI 상태 수집"""
        return {
            'panels': {
                'angle': self.status_widget.is_angle_visible(),
                'analysis': self.status_widget.is_analysis_visible(),
                'ergonomic': self.status_widget.is_ergonomic_visible(),
                'spreadsheet': self.status_widget.is_spreadsheet_visible(),
                'rula': self.status_widget.is_rula_visible(),
                'reba': self.status_widget.is_reba_visible(),
                'owas': self.status_widget.is_owas_visible(),
                'nle': self.status_widget.is_nle_visible(),
                'si': self.status_widget.is_si_visible(),
            },
            'splitter_sizes': {
                'main': self._splitter.sizes(),
            },
            'status_splitter_states': self.status_widget.save_splitter_states(),
            'sensitivity': self._sensitivity_slider.value(),
        }

    def _restore_ui_state(self, ui_state: dict):
        """UI 상태 복원"""
        if not ui_state:
            return

        panels = ui_state.get('panels', {})
        if 'angle' in panels:
            self.status_widget.set_angle_visible(panels['angle'])
            self._angle_action.setChecked(panels['angle'])
        if 'analysis' in panels:
            self.status_widget.set_analysis_visible(panels['analysis'])
            self._analysis_result_action.setChecked(panels['analysis'])
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
        if 'nle' in panels:
            self.status_widget.set_nle_visible(panels['nle'])
        if 'si' in panels:
            self.status_widget.set_si_visible(panels['si'])

        splitter_sizes = ui_state.get('splitter_sizes', {})
        if 'main' in splitter_sizes:
            self._splitter.setSizes(splitter_sizes['main'])

        status_states = ui_state.get('status_splitter_states', {})
        if status_states:
            self.status_widget.restore_splitter_states(status_states)

        # 민감도 복원
        sensitivity = ui_state.get('sensitivity')
        if sensitivity is not None:
            self._sensitivity_slider.setValue(int(sensitivity))

    def _mark_project_dirty(self):
        """프로젝트를 dirty로 표시"""
        self._project_manager.mark_dirty()
        self._update_window_title()

    @property
    def _video_name(self) -> Optional[str]:
        """현재 비디오 이름"""
        return self.status_widget._video_name

    def _show_help_usage(self):
        """사용 방법 도움말 표시"""
        dialog = HelpDialog(self)
        dialog.show_usage()

    def _show_help_about(self):
        """프로그램 정보 도움말 표시"""
        dialog = HelpDialog(self)
        dialog.show_about()

    # === 분석 관련 메서드 ===

    def _on_analysis_requested(self, sample_interval: int):
        """분석 위젯에서 분석 요청 시"""
        video_path = self.player_widget.get_video_path()
        if not video_path:
            return

        # 재개 데이터 확인
        resume_data = self.status_widget.movement_analysis_widget.get_resume_data()
        if resume_data:
            self._run_analysis(
                video_path, sample_interval,
                resume_state=resume_data['analyzer_state'],
                resume_frame=resume_data['frame_index'],
                resume_skipped=resume_data['skipped_frames'],
                resume_elapsed=resume_data.get('elapsed_seconds', 0.0),
            )
        else:
            self._run_analysis(video_path, sample_interval)

    def _run_analysis(self, video_path: str, sample_interval: int,
                      resume_state: dict = None, resume_frame: int = 0,
                      resume_skipped: int = 0, resume_elapsed: float = 0.0):
        """분석 모달 실행"""
        dialog = AnalysisProgressDialog(
            video_path=video_path,
            sample_interval=sample_interval,
            resume_state=resume_state,
            resume_frame=resume_frame,
            resume_skipped=resume_skipped,
            resume_elapsed=resume_elapsed,
            parent=self,
        )
        dialog.start_analysis()
        accepted = dialog.exec()

        if accepted:
            result = dialog.get_result()
            if result:
                self.status_widget.movement_analysis_widget.set_result(result)
                self.status_widget.switch_to_analysis_tab()
                self._status_bar.showMessage(
                    f"분석 완료: {result.analyzed_frames:,}프레임 분석, "
                    f"{result.duration_seconds:.1f}초 소요"
                )
        else:
            # 취소 시 부분 상태 저장
            partial_state = dialog.get_partial_state()
            if partial_state:
                self.status_widget.movement_analysis_widget.save_resume_state(partial_state)
                self._status_bar.showMessage("분석 취소됨 - 진행 상태가 저장되었습니다.")

    # === 라이센스 관련 메서드 ===

    def _update_menu_state(self):
        """라이센스 상태에 따른 메뉴 활성화/비활성화"""
        is_licensed = self._license_manager.is_licensed

        # 프로젝트 관련 메뉴 - 라이센스 필요
        self._open_project_action.setEnabled(is_licensed)
        self._save_project_action.setEnabled(is_licensed)
        self._save_as_action.setEnabled(is_licensed)

        # 툴바 버튼도 동기화
        self._open_btn.setEnabled(is_licensed)
        self._save_btn.setEnabled(is_licensed)

    def _on_license_changed(self):
        """라이센스 상태 변경 시"""
        self._update_menu_state()
        self._update_window_title()

    def _show_license_dialog(self):
        """라이센스 다이얼로그 표시"""
        dialog = LicenseDialog(self)
        dialog.exec()
