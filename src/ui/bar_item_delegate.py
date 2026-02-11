"""QTableWidget 셀 안 인라인 바 렌더링 델리게이트"""
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PyQt6.QtCore import Qt, QModelIndex, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont


# 고위험 비율 색상 코드
RISK_COLOR_RED = QColor(220, 80, 80)       # 60% 이상
RISK_COLOR_ORANGE = QColor(220, 150, 60)   # 40% 이상
RISK_COLOR_YELLOW = QColor(200, 200, 60)   # 20% 이상
RISK_COLOR_GREEN = QColor(80, 180, 100)    # 20% 미만

# 움직임 바 색상
MOVEMENT_BAR_COLOR = QColor(74, 158, 255)  # #4a9eff


def get_risk_color(ratio: float) -> QColor:
    """고위험 비율에 따른 색상 반환"""
    if ratio >= 0.6:
        return RISK_COLOR_RED
    elif ratio >= 0.4:
        return RISK_COLOR_ORANGE
    elif ratio >= 0.2:
        return RISK_COLOR_YELLOW
    else:
        return RISK_COLOR_GREEN


class BarItemDelegate(QStyledItemDelegate):
    """셀 안에 인라인 바를 렌더링하는 델리게이트

    UserRole 데이터 형식:
        {
            'type': 'movement' | 'risk',
            'value': float,       # 실제 값 (횟수 또는 비율 0.0~1.0)
            'max_value': float,   # movement: 최대 횟수, risk: 1.0
            'display': str,       # 표시 텍스트 (예: "127", "68.3%")
        }
    """

    BAR_HEIGHT = 14
    BAR_MARGIN_X = 6
    BAR_MARGIN_Y = 4
    TEXT_MARGIN = 6
    BAR_RADIUS = 3

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data or not isinstance(data, dict):
            super().paint(painter, option, index)
            return

        try:
            self._paint_bar(painter, option, index, data)
        except Exception:
            super().paint(painter, option, index)

    def _paint_bar(self, painter: QPainter, option: QStyleOptionViewItem,
                   index: QModelIndex, data: dict):
        """바 렌더링 구현"""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경
        if option.state & QStyleOptionViewItem.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(50, 50, 70))
        else:
            painter.fillRect(option.rect, QColor(30, 30, 30))

        bar_type = data.get('type', 'movement')
        value = float(data.get('value', 0.0) or 0.0)
        max_value = float(data.get('max_value', 1.0) or 1.0)
        display_text = str(data.get('display', ''))

        rect = option.rect

        # 바 영역 계산
        bar_x = rect.x() + self.BAR_MARGIN_X
        bar_y = rect.y() + (rect.height() - self.BAR_HEIGHT) // 2
        bar_max_width = rect.width() - self.BAR_MARGIN_X * 2

        # 텍스트 폰트 설정
        font = QFont()
        font.setPixelSize(11)
        painter.setFont(font)
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(display_text) + self.TEXT_MARGIN * 2

        # 바 최대 너비 (텍스트 영역 제외)
        available_bar_width = bar_max_width - text_width
        if available_bar_width < 20:
            available_bar_width = 20

        # 비율 계산
        if max_value > 0:
            ratio = min(value / max_value, 1.0)
        else:
            ratio = 0.0

        filled_width = int(available_bar_width * ratio)

        # 바 배경 (트랙)
        track_rect = QRectF(bar_x, bar_y, available_bar_width, self.BAR_HEIGHT)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(50, 50, 50))
        painter.drawRoundedRect(track_rect, self.BAR_RADIUS, self.BAR_RADIUS)

        # 바 채움
        if filled_width > 0:
            if bar_type == 'risk':
                color = get_risk_color(value)  # value는 이미 0~1 비율
            else:
                color = MOVEMENT_BAR_COLOR

            fill_rect = QRectF(bar_x, bar_y, filled_width, self.BAR_HEIGHT)
            painter.setBrush(color)
            painter.drawRoundedRect(fill_rect, self.BAR_RADIUS, self.BAR_RADIUS)

        # 텍스트
        text_x = bar_x + available_bar_width + self.TEXT_MARGIN
        text_rect = QRectF(
            text_x,
            rect.y(),
            text_width,
            rect.height(),
        )
        painter.setPen(QColor(220, 220, 220))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, display_text)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), self.BAR_HEIGHT + self.BAR_MARGIN_Y * 2))
        return size
