#!/usr/bin/env python3
"""
Skeleton Analyzer - Human Pose Analysis Application
Main entry point
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtGui import QIcon

from src.ui.main_window import MainWindow


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
    app = QApplication(sys.argv)
    app.setApplicationName("Skeleton Analyzer")
    app.setOrganizationName("SkeletonAnalyzer")

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
