"""메인 윈도우 모듈"""
import os
import platform
from pathlib import Path
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
from ..core.project_manager import ProjectManager, ProjectLoadError, LoadResult

# 앱 이름 (환경변수로 변경 가능)
APP_NAME = os.environ.get('SKELETON_ANALYZER_APP_NAME', 'Skeleton Analyzer')


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""

    MAX_RECENT_FILES = 10

    def __init__(self):
        super().__init__()
        self._recent_files: List[str] = []
        self._recent_projects: List[str] = []
        self._settings = QSettings("SkeletonAnalyzer", "SkeletonAnalyzer")
        self._config = Config()
        self._project_manager = ProjectManager()

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

    def _load_video(self, file_path: str, from_project_load: bool = False):
        """
        비디오 로드

        Args:
            file_path: 비디오 파일 경로
            from_project_load: 프로젝트 로드에서 호출된 경우 True (경고 건너뜀)
        """
        # 프로젝트 로드에서 호출된 경우가 아니고, 저장되지 않은 변경사항이 있는 경우
        if not from_project_load and self._project_manager.is_dirty:
            from PyQt6.QtWidgets import QStyle
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("저장되지 않은 변경사항")
            msg_box.setText(
                "새 동영상을 로드하면 현재 캡처 데이터가 삭제됩니다.\n\n"
                "저장되지 않은 캡처 이미지도 함께 삭제됩니다.\n"
                "계속하시겠습니까?"
            )
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
            msg_box.setIconPixmap(icon.pixmap(64, 64))
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.Save)
            reply = msg_box.exec()

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Save:
                if not self._save_project():
                    return

            # 기존 캡처 이미지 정리
            self._cleanup_capture_images()

        if self.player_widget.load_video(file_path):
            self._add_recent_file(file_path)
            self._status_bar.showMessage(f"로드됨: {file_path}")

            # 새 동영상이므로 프로젝트 상태 초기화
            if not from_project_load:
                self._project_manager.new_project()
                self.status_widget.spreadsheet_widget.clear_all()
                self._update_window_title()
        else:
            QMessageBox.warning(self, "오류", f"파일을 열 수 없습니다:\n{file_path}")

    def _cleanup_capture_images(self, silent: bool = False):
        """
        캡처 이미지 디렉토리 정리 (삭제)

        Args:
            silent: True이면 에러 무시, False이면 상태바에 에러 표시
        """
        if self._video_name:
            capture_dir = Path(self._config.get(
                "directories.capture_save",
                "captures"
            )) / self._video_name

            if capture_dir.exists():
                import shutil
                try:
                    shutil.rmtree(capture_dir)
                except Exception as e:
                    if not silent:
                        self._status_bar.showMessage(f"이미지 삭제 실패: {e}")

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
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.Save)
            reply = msg_box.exec()

            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.StandardButton.Save:
                if not self._save_project():
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Discard:
                # 캡처 이미지 정리
                self._cleanup_capture_images(silent=True)

        # 종료 확인 다이얼로그
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("종료 확인")
        msg_box.setText("앱을 종료하시겠습니까?")
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

        self._save_settings()
        self.player_widget.release()
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
            reply = QMessageBox.question(
                self,
                "저장되지 않은 변경사항",
                "저장되지 않은 변경사항이 있습니다.\n저장하시겠습니까?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Save:
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
            reply = QMessageBox.question(
                self,
                "저장되지 않은 변경사항",
                "저장되지 않은 변경사항이 있습니다.\n저장하시겠습니까?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Save:
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
        try:
            # 캡처 디렉토리 설정
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
                msg_box.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
                )
                msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
                reply = msg_box.exec()

                if reply != QMessageBox.StandardButton.Yes:
                    return
                # Yes 선택 시 동영상 없이 데이터만 복원

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

        except ProjectLoadError as e:
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
                return True

        except Exception as e:
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
