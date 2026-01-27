"""각도 표시 위젯 모듈"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from typing import Dict, Optional


# 각도 카테고리 정의
ANGLE_CATEGORIES = {
    '목/머리': ['neck'],
    '왼팔': ['left_shoulder', 'left_elbow', 'left_wrist'],
    '오른팔': ['right_shoulder', 'right_elbow', 'right_wrist'],
    '왼다리': ['left_hip', 'left_knee', 'left_ankle'],
    '오른다리': ['right_hip', 'right_knee', 'right_ankle'],
}

# 각도 한글 이름
ANGLE_NAMES = {
    'neck': '목 기울기',
    'left_shoulder': '왼쪽 어깨',
    'right_shoulder': '오른쪽 어깨',
    'left_elbow': '왼쪽 팔꿈치',
    'right_elbow': '오른쪽 팔꿈치',
    'left_wrist': '왼쪽 손목',
    'right_wrist': '오른쪽 손목',
    'left_hip': '왼쪽 고관절',
    'right_hip': '오른쪽 고관절',
    'left_knee': '왼쪽 무릎',
    'right_knee': '오른쪽 무릎',
    'left_ankle': '왼쪽 발목',
    'right_ankle': '오른쪽 발목',
}


class AngleWidget(QWidget):
    """각도 표시 위젯"""

    def __init__(self):
        super().__init__()
        self._angles: Optional[Dict[str, float]] = None
        self._category_items: Dict[str, QTreeWidgetItem] = {}
        self._angle_items: Dict[str, QTreeWidgetItem] = {}

        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 트리 위젯
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(['부위', '각도'])
        self._tree.setColumnWidth(0, 150)
        self._tree.setAlternatingRowColors(True)
        self._tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2d2d2d;
                color: white;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:alternate {
                background-color: #363636;
            }
        """)

        # 카테고리 및 항목 생성
        self._create_tree_structure()

        # 모든 항목 펼치기
        self._tree.expandAll()

        layout.addWidget(self._tree)

    def _create_tree_structure(self):
        """트리 구조 생성"""
        for category_name, angle_keys in ANGLE_CATEGORIES.items():
            # 카테고리 아이템
            category_item = QTreeWidgetItem([category_name, ''])
            category_item.setExpanded(True)
            self._tree.addTopLevelItem(category_item)
            self._category_items[category_name] = category_item

            # 각도 아이템
            for key in angle_keys:
                name = ANGLE_NAMES.get(key, key)
                angle_item = QTreeWidgetItem([name, '-'])
                category_item.addChild(angle_item)
                self._angle_items[key] = angle_item

    def set_angles(self, angles: Dict[str, float]):
        """각도 설정"""
        self._angles = angles

        for key, angle in angles.items():
            if key in self._angle_items:
                item = self._angle_items[key]
                item.setText(1, f"{angle:.1f}°")

                # 색상 설정 (각도에 따라)
                color = self._get_angle_color(angle)
                item.setForeground(1, QBrush(color))

    def clear(self):
        """클리어"""
        self._angles = None
        for item in self._angle_items.values():
            item.setText(1, '-')
            item.setForeground(1, QBrush(QColor(100, 100, 100)))

    def _get_angle_color(self, angle: float) -> QColor:
        """각도에 따른 색상 반환"""
        # 정상 범위: 녹색, 주의: 노란색, 위험: 빨간색
        if angle < 30 or angle > 150:
            return QColor(255, 100, 100)  # 빨강 (주의)
        elif angle < 45 or angle > 135:
            return QColor(255, 200, 100)  # 노랑 (경고)
        else:
            return QColor(100, 255, 100)  # 녹색 (정상)
