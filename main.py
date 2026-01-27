#!/usr/bin/env python3
"""
Skeleton Analyzer - Human Pose Analysis Application
Main entry point
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QEvent, Qt

from src.ui.main_window import MainWindow


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

    window = MainWindow()

    # 글로벌 이벤트 필터 설치
    event_filter = GlobalEventFilter(window)
    app.installEventFilter(event_filter)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
