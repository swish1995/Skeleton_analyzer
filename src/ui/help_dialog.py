"""도움말 다이얼로그 모듈"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QTextBrowser,
    QDialogButtonBox
)
from PyQt6.QtCore import QSettings, QUrl
from PyQt6.QtGui import QDesktopServices


def get_resource_path(relative_path: str) -> Path:
    """리소스 파일 경로 반환 (PyInstaller 빌드 지원)"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 빌드 환경: help/ 디렉토리가 루트에 배치됨
        base_path = Path(sys._MEIPASS)
        # 'help/about.html' 형식의 경로를 처리
        if relative_path.startswith('help/'):
            return base_path / relative_path
        return base_path / "help" / relative_path
    else:
        # 개발 환경: src/resources/ 아래에 위치
        base_path = Path(__file__).parent.parent / "resources"
        return base_path / relative_path


class HelpDialog(QDialog):
    """도움말 다이얼로그"""

    # 탭 인덱스 상수
    TAB_ABOUT = 0
    TAB_USAGE = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings("SkeletonAnalyzer", "SkeletonAnalyzer")
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("도움말")
        self.setMinimumSize(750, 550)
        self.resize(950, 750)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 탭 위젯
        self._tab_widget = QTabWidget()
        self._tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #1e1e1e;
            }
            QTabBar::tab {
                background: #2a2a2a;
                color: #aaaaaa;
                padding: 12px 28px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: #1e1e1e;
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background: #3a3a3a;
                color: #dddddd;
            }
        """)
        layout.addWidget(self._tab_widget)

        # 프로그램 정보 탭
        self._about_browser = self._create_text_browser()
        self._tab_widget.addTab(self._about_browser, "  프로그램 정보  ")

        # 사용 방법 탭
        self._usage_browser = self._create_text_browser()
        self._tab_widget.addTab(self._usage_browser, "  사용 방법  ")

        # 콘텐츠 로드
        self._load_content()

        # 하단 버튼 영역
        button_container = QDialogButtonBox()
        button_container.setStyleSheet("""
            QDialogButtonBox {
                background-color: #252525;
                padding: 12px 20px;
                border-top: 1px solid #3a3a3a;
            }
            QPushButton {
                background: linear-gradient(180deg, #4a9eff 0%, #3a8eef 100%);
                color: white;
                border: none;
                padding: 10px 28px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background: linear-gradient(180deg, #5aaeFF 0%, #4a9eff 100%);
            }
            QPushButton:pressed {
                background: linear-gradient(180deg, #3a8eef 0%, #2a7edf 100%);
            }
        """)
        close_btn = button_container.addButton("닫기", QDialogButtonBox.ButtonRole.RejectRole)
        button_container.rejected.connect(self.accept)
        layout.addWidget(button_container)

    def _create_text_browser(self) -> QTextBrowser:
        """텍스트 브라우저 위젯 생성"""
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.anchorClicked.connect(self._on_link_clicked)
        browser.setStyleSheet("""
            QTextBrowser {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 14px;
                border-radius: 7px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #444;
                border-radius: 5px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        return browser

    def _load_content(self):
        """도움말 콘텐츠 로드"""
        # 프로그램 정보 (HTML)
        about_path = get_resource_path("help/about.html")
        about_html = self._load_html(about_path)
        self._about_browser.setHtml(about_html)

        # 사용 방법 (HTML)
        usage_path = get_resource_path("help/usage.html")
        usage_html = self._load_html(usage_path)
        self._usage_browser.setHtml(usage_html)

    def _load_html(self, path: Path) -> str:
        """HTML 파일 로드"""
        try:
            if path.exists():
                return path.read_text(encoding='utf-8')
            else:
                return self._error_html(f"도움말 파일을 찾을 수 없습니다: {path.name}")
        except Exception as e:
            return self._error_html(f"도움말 파일 로드 중 오류: {e}")

    def _error_html(self, message: str) -> str:
        """에러 메시지 HTML 생성"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, sans-serif;
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    padding: 40px;
                    text-align: center;
                }}
                .error {{
                    background-color: #3a2a2a;
                    border: 1px solid #5a3a3a;
                    border-radius: 8px;
                    padding: 20px;
                    display: inline-block;
                }}
                .error-icon {{
                    font-size: 32px;
                    margin-bottom: 10px;
                }}
                .error-text {{
                    color: #ff6b6b;
                }}
            </style>
        </head>
        <body>
            <div class="error">
                <div class="error-icon">⚠️</div>
                <p class="error-text">{message}</p>
            </div>
        </body>
        </html>
        """

    def _on_link_clicked(self, url: QUrl):
        """링크 클릭 처리"""
        url_str = url.toString()
        # 내부 앵커 링크 처리
        if url_str.startswith('#'):
            current_browser = self._tab_widget.currentWidget()
            if isinstance(current_browser, QTextBrowser):
                current_browser.scrollToAnchor(url_str[1:])
        else:
            # 외부 링크는 기본 브라우저에서 열기
            QDesktopServices.openUrl(url)

    def _load_settings(self):
        """설정 로드"""
        geometry = self._settings.value("help_dialog/geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def _save_settings(self):
        """설정 저장"""
        self._settings.setValue("help_dialog/geometry", self.saveGeometry())

    def show_about(self):
        """프로그램 정보 탭으로 열기"""
        self._tab_widget.setCurrentIndex(self.TAB_ABOUT)
        self.exec()

    def show_usage(self):
        """사용 방법 탭으로 열기"""
        self._tab_widget.setCurrentIndex(self.TAB_USAGE)
        self.exec()

    def closeEvent(self, event):
        """창 닫기 이벤트"""
        self._save_settings()
        super().closeEvent(event)

    def accept(self):
        """다이얼로그 승인"""
        self._save_settings()
        super().accept()

    def reject(self):
        """다이얼로그 거부"""
        self._save_settings()
        super().reject()
