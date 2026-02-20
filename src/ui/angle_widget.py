"""각도 표시 위젯 모듈"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont
from typing import Dict, Optional


# ── 굴곡 각도 (0°=자연 자세, 안전지표에 사용) ──
FLEXION_CATEGORIES = {
    '목/몸통': ['neck_flexion', 'trunk_flexion'],
    '왼팔': ['left_shoulder_flexion', 'left_elbow_flexion', 'left_wrist_flexion'],
    '오른팔': ['right_shoulder_flexion', 'right_elbow_flexion', 'right_wrist_flexion'],
    '왼다리': ['left_knee_flexion'],
    '오른다리': ['right_knee_flexion'],
}

FLEXION_NAMES = {
    'neck_flexion': '목',
    'trunk_flexion': '몸통',
    'left_shoulder_flexion': '왼쪽 상박',
    'right_shoulder_flexion': '오른쪽 상박',
    'left_elbow_flexion': '왼쪽 하박',
    'right_elbow_flexion': '오른쪽 하박',
    'left_wrist_flexion': '왼쪽 손목',
    'right_wrist_flexion': '오른쪽 손목',
    'left_knee_flexion': '왼쪽 무릎',
    'right_knee_flexion': '오른쪽 무릎',
}

# ── 랜드마크 각도 (3점 원본) ──
LANDMARK_CATEGORIES = {
    '목/머리': ['neck'],
    '왼팔': ['left_shoulder', 'left_elbow', 'left_wrist'],
    '오른팔': ['right_shoulder', 'right_elbow', 'right_wrist'],
    '왼다리': ['left_hip', 'left_knee', 'left_ankle'],
    '오른다리': ['right_hip', 'right_knee', 'right_ankle'],
}

LANDMARK_NAMES = {
    'neck': '목',
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

        # 섹션 생성
        self._create_tree_structure()

        # 모든 항목 펼치기
        self._tree.expandAll()

        layout.addWidget(self._tree)

    def _create_section_header(self, title: str) -> QTreeWidgetItem:
        """섹션 헤더 생성"""
        header = QTreeWidgetItem([title, ''])
        header.setExpanded(True)
        font = QFont()
        font.setBold(True)
        header.setFont(0, font)
        header.setForeground(0, QBrush(QColor('#2196F3')))
        self._tree.addTopLevelItem(header)
        return header

    def _create_tree_structure(self):
        """트리 구조 생성 (굴곡 각도 + 랜드마크 각도)"""
        # ── 굴곡 각도 (카테고리별 직접 표시) ──
        for category_name, angle_keys in FLEXION_CATEGORIES.items():
            category_item = QTreeWidgetItem([category_name, ''])
            category_item.setExpanded(True)
            font = QFont()
            font.setBold(True)
            category_item.setFont(0, font)
            category_item.setForeground(0, QBrush(QColor('#2196F3')))
            self._tree.addTopLevelItem(category_item)

            for key in angle_keys:
                name = FLEXION_NAMES.get(key, key)
                angle_item = QTreeWidgetItem([name, '-'])
                category_item.addChild(angle_item)
                self._angle_items[key] = angle_item

        # # ── 랜드마크 각도 섹션 (비활성) ──
        # landmark_header = self._create_section_header('▼ 랜드마크 각도')
        # for category_name, angle_keys in LANDMARK_CATEGORIES.items():
        #     category_item = QTreeWidgetItem([category_name, ''])
        #     category_item.setExpanded(True)
        #     landmark_header.addChild(category_item)
        #
        #     for key in angle_keys:
        #         name = LANDMARK_NAMES.get(key, key)
        #         angle_item = QTreeWidgetItem([name, '-'])
        #         category_item.addChild(angle_item)
        #         self._angle_items[key] = angle_item

    def set_angles(self, angles: Dict[str, float]):
        """각도 설정"""
        self._angles = angles

        for key, angle in angles.items():
            if key in self._angle_items:
                item = self._angle_items[key]
                item.setText(1, f"{angle:.1f}°")

                if key in FLEXION_NAMES:
                    color = self._get_flexion_color(angle)
                else:
                    color = self._get_landmark_color(angle)
                item.setForeground(1, QBrush(color))

    def clear(self):
        """클리어"""
        self._angles = None
        for item in self._angle_items.values():
            item.setText(1, '-')
            item.setForeground(1, QBrush(QColor(100, 100, 100)))

    def _get_flexion_color(self, angle: float) -> QColor:
        """굴곡 각도 색상 (0°=자연 자세)"""
        if angle <= 10:
            return QColor(100, 255, 100)
        elif angle <= 20:
            return QColor(200, 255, 100)
        elif angle <= 45:
            return QColor(255, 200, 100)
        else:
            return QColor(255, 100, 100)

    def _get_landmark_color(self, angle: float) -> QColor:
        """랜드마크 3점 각도 색상"""
        if angle < 30 or angle > 150:
            return QColor(255, 100, 100)
        elif angle < 45 or angle > 135:
            return QColor(255, 200, 100)
        else:
            return QColor(100, 255, 100)
