"""스켈레톤 시각화 위젯 모듈"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPalette, QPixmap
from typing import List, Dict, Optional


# 스켈레톤 연결 정의 (시작점 인덱스, 끝점 인덱스)
SKELETON_CONNECTIONS = [
    # 얼굴
    (0, 1), (1, 2), (2, 3), (3, 7),  # 왼쪽 눈
    (0, 4), (4, 5), (5, 6), (6, 8),  # 오른쪽 눈
    (9, 10),  # 입

    # 몸통
    (11, 12),  # 어깨
    (11, 23), (12, 24),  # 어깨-골반
    (23, 24),  # 골반

    # 왼팔
    (11, 13), (13, 15),  # 어깨-팔꿈치-손목
    (15, 17), (15, 19), (15, 21),  # 손목-손가락

    # 오른팔
    (12, 14), (14, 16),  # 어깨-팔꿈치-손목
    (16, 18), (16, 20), (16, 22),  # 손목-손가락

    # 왼다리
    (23, 25), (25, 27),  # 골반-무릎-발목
    (27, 29), (27, 31),  # 발목-발

    # 오른다리
    (24, 26), (26, 28),  # 골반-무릎-발목
    (28, 30), (28, 32),  # 발목-발
]

# 부위별 색상
BODY_PART_COLORS = {
    'face': QColor(200, 200, 200),
    'torso': QColor(255, 200, 100),
    'left_arm': QColor(100, 200, 255),
    'right_arm': QColor(255, 100, 100),
    'left_leg': QColor(100, 255, 200),
    'right_leg': QColor(255, 150, 200),
}


class SkeletonWidget(QWidget):
    """스켈레톤 시각화 위젯"""

    def __init__(self):
        super().__init__()
        self._landmarks: Optional[List[Dict]] = None
        self.setMinimumSize(200, 300)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.setPalette(palette)

    def set_landmarks(self, landmarks: List[Dict]):
        """랜드마크 설정"""
        self._landmarks = landmarks
        self.update()

    def clear(self):
        """클리어"""
        self._landmarks = None
        self.update()

    def paintEvent(self, event):
        """페인트 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._landmarks:
            # 랜드마크 없음 - 안내 메시지
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "인체가 감지되지 않음"
            )
            return

        # 위젯 크기
        w = self.width()
        h = self.height()
        margin = 20

        # 연결선 그리기
        self._draw_connections(painter, w, h, margin)

        # 관절점 그리기
        self._draw_joints(painter, w, h, margin)

    def _draw_connections(self, painter: QPainter, w: int, h: int, margin: int):
        """연결선 그리기"""
        pen = QPen()
        pen.setWidth(3)

        for start_idx, end_idx in SKELETON_CONNECTIONS:
            if start_idx >= len(self._landmarks) or end_idx >= len(self._landmarks):
                continue

            start = self._landmarks[start_idx]
            end = self._landmarks[end_idx]

            # visibility 체크
            if start.get('visibility', 1) < 0.5 or end.get('visibility', 1) < 0.5:
                continue

            # 좌표 변환 (정규화 좌표 → 픽셀)
            x1 = int(start['x'] * (w - 2 * margin) + margin)
            y1 = int(start['y'] * (h - 2 * margin) + margin)
            x2 = int(end['x'] * (w - 2 * margin) + margin)
            y2 = int(end['y'] * (h - 2 * margin) + margin)

            # 색상 결정
            color = self._get_connection_color(start_idx, end_idx)
            pen.setColor(color)
            painter.setPen(pen)

            painter.drawLine(x1, y1, x2, y2)

    def _draw_joints(self, painter: QPainter, w: int, h: int, margin: int):
        """관절점 그리기"""
        for i, lm in enumerate(self._landmarks):
            if lm.get('visibility', 1) < 0.5:
                continue

            x = int(lm['x'] * (w - 2 * margin) + margin)
            y = int(lm['y'] * (h - 2 * margin) + margin)

            # 색상
            color = self._get_joint_color(i)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.white, 1))

            # 원 그리기
            radius = 5
            painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

    def _get_connection_color(self, start_idx: int, end_idx: int) -> QColor:
        """연결선 색상 결정"""
        # 왼팔
        if start_idx in [11, 13, 15, 17, 19, 21] and end_idx in [11, 13, 15, 17, 19, 21]:
            return BODY_PART_COLORS['left_arm']
        # 오른팔
        if start_idx in [12, 14, 16, 18, 20, 22] and end_idx in [12, 14, 16, 18, 20, 22]:
            return BODY_PART_COLORS['right_arm']
        # 왼다리
        if start_idx in [23, 25, 27, 29, 31] and end_idx in [23, 25, 27, 29, 31]:
            return BODY_PART_COLORS['left_leg']
        # 오른다리
        if start_idx in [24, 26, 28, 30, 32] and end_idx in [24, 26, 28, 30, 32]:
            return BODY_PART_COLORS['right_leg']
        # 몸통
        if start_idx in [11, 12, 23, 24] and end_idx in [11, 12, 23, 24]:
            return BODY_PART_COLORS['torso']
        # 얼굴
        return BODY_PART_COLORS['face']

    def _get_joint_color(self, idx: int) -> QColor:
        """관절점 색상 결정"""
        if idx in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            return BODY_PART_COLORS['face']
        if idx in [11, 13, 15, 17, 19, 21]:
            return BODY_PART_COLORS['left_arm']
        if idx in [12, 14, 16, 18, 20, 22]:
            return BODY_PART_COLORS['right_arm']
        if idx in [23, 25, 27, 29, 31]:
            return BODY_PART_COLORS['left_leg']
        if idx in [24, 26, 28, 30, 32]:
            return BODY_PART_COLORS['right_leg']
        return BODY_PART_COLORS['torso']

    def grab_as_pixmap(self) -> QPixmap:
        """위젯을 QPixmap으로 캡처"""
        return self.grab()
