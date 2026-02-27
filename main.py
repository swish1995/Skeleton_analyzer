#!/usr/bin/env python3
"""
IMAS - Intelligent Musculoskeletal Analysis System
Main entry point
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtGui import QIcon, QPalette, QColor

from src.core.logger import setup_logging, get_logger
from src.ui.main_window import MainWindow

# 앱 이름 (환경변수로 변경 가능)
APP_NAME = os.environ.get('IMAS_APP_NAME', 'IMAS')


def set_process_name(name: str):
    """프로세스 이름 설정 (macOS dock 툴팁용)"""
    if sys.platform == 'darwin':
        try:
            # setproctitle 패키지 사용
            import setproctitle
            setproctitle.setproctitle(name)
        except ImportError:
            pass

        try:
            # ctypes를 통한 프로세스 이름 설정
            import ctypes
            libc = ctypes.CDLL('libc.dylib')
            # pthread_setname_np로 스레드 이름 설정
            libc.pthread_setname_np(name.encode('utf-8'))
        except Exception:
            pass

        try:
            # AppKit을 통한 macOS 앱 이름 설정
            from AppKit import NSApplication, NSRunningApplication
            from Foundation import NSBundle, NSMutableDictionary

            # 번들 정보 수정
            bundle = NSBundle.mainBundle()
            info = bundle.infoDictionary()
            if info is not None:
                info['CFBundleName'] = name
                info['CFBundleDisplayName'] = name
        except ImportError:
            pass


def get_icon_path():
    """아이콘 파일 경로 반환 (macOS/Windows 지원)"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 경우
        base_path = sys._MEIPASS
    else:
        # 개발 환경
        base_path = os.path.dirname(os.path.abspath(__file__))

    # macOS는 .icns, Windows는 .ico
    if sys.platform == 'darwin':
        icon_file = 'icon.icns'
    else:
        icon_file = 'icon.ico'

    return os.path.join(base_path, 'resources', icon_file)


class GlobalEventFilter(QObject):
    """글로벌 이벤트 필터 - 스페이스바 일시정지"""

    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Space:
                self._main_window.player_widget.toggle_play()
                return True  # 이벤트 소비
        return False


def main():
    # 로깅 시스템 초기화 (가장 먼저)
    setup_logging()
    logger = get_logger('main')
    logger.info("=" * 50)
    logger.info("앱 시작")

    # macOS dock 툴팁 이름 설정 (QApplication 생성 전에 호출)
    set_process_name(APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)  # 디스플레이 이름 설정
    app.setOrganizationName("IMAS")

    # 다크 테마 강제 적용 (시스템 테마 무시)
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(74, 158, 255))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(74, 158, 255))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(128, 128, 128))
    app.setPalette(dark_palette)

    # 앱 아이콘 설정
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.setWindowIcon(QIcon(icon_path))

    # 글로벌 이벤트 필터 설치
    event_filter = GlobalEventFilter(window)
    app.installEventFilter(event_filter)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
