"""인터랙티브 스켈레톤 에디터 위젯 모듈"""
import copy
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QEvent
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QTransform, QCursor,
)
from typing import List, Dict, Optional

from .skeleton_widget import SkeletonWidget, SKELETON_CONNECTIONS
from ..license import LicenseManager

# 편집 가능 관절 인덱스: 코(0), 어깨(11,12), 팔꿈치(13,14), 손목(15,16),
# 고관절(23,24), 무릎(25,26), 발목(27,28)
EDITABLE_JOINTS = {0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28}

# 히트 반경 (화면 픽셀)
HIT_RADIUS = 12


class InteractiveSkeletonWidget(QWidget):
    """인터랙티브 스켈레톤 에디터 위젯 (SkeletonWidget 래핑)"""

    landmarks_changed = pyqtSignal(list)
    edit_mode_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._edit_mode = False

        # 내부 SkeletonWidget (렌더링 용)
        self._skeleton = SkeletonWidget()

        # 편집용 랜드마크 (deep copy)
        self._edit_landmarks: Optional[List[Dict]] = None
        # 편집 진입 시점의 원본 랜드마크 (초기화용)
        self._original_landmarks: Optional[List[Dict]] = None

        # 트랜스폼 상태
        self._scale = 1.0
        self._pan_offset = QPointF(0, 0)

        # 드래그 상태
        self._dragging_joint: Optional[int] = None
        self._panning = False
        self._last_mouse_pos = QPointF()

        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 컨트롤 바
        self._control_bar = QWidget()
        self._control_bar.setVisible(False)
        self._control_bar.setFixedHeight(34)
        self._control_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 220);
                border-bottom: 1px solid #444;
            }
        """)
        ctrl_layout = QHBoxLayout(self._control_bar)
        ctrl_layout.setContentsMargins(6, 2, 6, 2)
        ctrl_layout.setSpacing(4)

        btn_style = """
            QPushButton {
                background: #444; color: #ddd; border: none;
                padding: 3px 8px; border-radius: 3px; font-size: 11px;
            }
            QPushButton:hover { background: #555; }
            QPushButton:pressed { background: #333; }
            QPushButton:disabled { color: #666; background: #3a3a3a; }
        """

        # 초기화 (관절 위치 + 뷰 트랜스폼 모두 리셋)
        self._reset_btn = QPushButton("초기화")
        self._reset_btn.setStyleSheet(btn_style)
        self._reset_btn.setEnabled(False)
        self._reset_btn.clicked.connect(self._reset_all)
        ctrl_layout.addWidget(self._reset_btn)

        ctrl_layout.addStretch()

        # 확대
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setStyleSheet(btn_style)
        zoom_in_btn.setFixedWidth(28)
        zoom_in_btn.clicked.connect(lambda: self._zoom(1.2))
        ctrl_layout.addWidget(zoom_in_btn)

        # 축소
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setStyleSheet(btn_style)
        zoom_out_btn.setFixedWidth(28)
        zoom_out_btn.clicked.connect(lambda: self._zoom(1 / 1.2))
        ctrl_layout.addWidget(zoom_out_btn)

        layout.addWidget(self._control_bar)
        layout.addWidget(self._skeleton, 1)

    # === 공개 API ===

    def set_landmarks(self, landmarks: List[Dict]):
        """랜드마크 설정 (외부에서 호출)"""
        if self._edit_mode:
            # 편집 모드에서는 외부 업데이트 무시
            return
        self._skeleton.set_landmarks(landmarks)
        # 편집용 데이터도 갱신 (편집 모드 진입 시 사용)
        self._edit_landmarks = copy.deepcopy(landmarks)

    def clear(self):
        """클리어"""
        if self._edit_mode:
            return
        self._skeleton.clear()
        self._edit_landmarks = None

    def set_edit_mode(self, enabled: bool):
        """편집 모드 설정"""
        if self._edit_mode == enabled:
            return
        self._edit_mode = enabled

        if enabled:
            # 편집 모드 진입: 현재 랜드마크를 원본으로 저장
            if self._edit_landmarks is None and self._skeleton._landmarks:
                self._edit_landmarks = copy.deepcopy(self._skeleton._landmarks)
            if self._edit_landmarks:
                self._original_landmarks = copy.deepcopy(self._edit_landmarks)
            self._reset_btn.setEnabled(True)
        else:
            # 편집 모드 해제
            self._dragging_joint = None
            self._original_landmarks = None
            self._reset_btn.setEnabled(False)
            # 트랜스폼 초기화
            self._reset_transform()

        self.edit_mode_changed.emit(enabled)
        self._skeleton.update()

    def exit_edit_mode(self):
        """편집 모드 강제 해제 (재생 시 호출)"""
        if self._edit_mode:
            self.set_edit_mode(False)

    def show_control_bar(self):
        """컨트롤 바 표시"""
        self._control_bar.setVisible(True)

    def hide_control_bar(self):
        """컨트롤 바 숨기기"""
        self._control_bar.setVisible(False)

    def grab_as_pixmap(self):
        """위젯을 QPixmap으로 캡처"""
        return self._skeleton.grab()

    @property
    def is_edit_mode(self) -> bool:
        return self._edit_mode

    def setMinimumWidth(self, w: int):
        super().setMinimumWidth(w)

    # === 내부 메서드 ===

    def _reset_all(self):
        """초기화: 관절 위치를 원본으로 복원 + 뷰 트랜스폼 초기화"""
        self._reset_transform()
        if self._original_landmarks:
            self._edit_landmarks = copy.deepcopy(self._original_landmarks)
            self._skeleton.set_landmarks(self._edit_landmarks)
            self.landmarks_changed.emit(self._edit_landmarks)

    def _reset_transform(self):
        """뷰 트랜스폼 초기화"""
        self._scale = 1.0
        self._pan_offset = QPointF(0, 0)
        self._skeleton.update()

    def _enter_edit_mode_if_needed(self) -> bool:
        """관절 클릭 시 편집 모드 자동 진입. 성공하면 True 반환."""
        if self._edit_mode:
            return True
        # 라이센스 체크
        if not LicenseManager.instance().check_feature('skeleton_editor'):
            QMessageBox.information(
                self, "등록 기능",
                "스켈레톤 편집 기능은 라이센스 등록이 필요합니다.\n\n"
                "도움말 → 라이센스 등록 메뉴에서 등록할 수 있습니다."
            )
            return False
        # 랜드마크가 없으면 불가
        if not self._edit_landmarks and not self._skeleton._landmarks:
            return False
        self.set_edit_mode(True)
        return True

    def _zoom(self, factor: float):
        """확대/축소"""
        new_scale = self._scale * factor
        if 0.3 <= new_scale <= 5.0:
            self._scale = new_scale
            self._skeleton.update()

    def _build_transform(self) -> QTransform:
        """QPainter 트랜스폼 생성"""
        w = self._skeleton.width()
        h = self._skeleton.height()
        cx, cy = w / 2.0, h / 2.0

        t = QTransform()
        t.translate(cx + self._pan_offset.x(), cy + self._pan_offset.y())
        t.scale(self._scale, self._scale)
        t.translate(-cx, -cy)
        return t

    def _screen_to_logical(self, screen_pos: QPointF) -> QPointF:
        """화면 좌표 → 논리 좌표"""
        transform = self._build_transform()
        inverted, ok = transform.inverted()
        if ok:
            return inverted.map(screen_pos)
        return screen_pos

    def _logical_to_normalized(self, logical_pos: QPointF) -> tuple:
        """논리 좌표 → 정규화 좌표 (0~1)"""
        w = self._skeleton.width()
        h = self._skeleton.height()
        margin = 20
        nx = (logical_pos.x() - margin) / max(w - 2 * margin, 1)
        ny = (logical_pos.y() - margin) / max(h - 2 * margin, 1)
        return (max(0.0, min(1.0, nx)), max(0.0, min(1.0, ny)))

    def _hit_test(self, screen_pos: QPointF) -> Optional[int]:
        """히트 테스팅: 화면 좌표 근처의 편집 가능 관절 인덱스 반환"""
        # 편집 모드가 아닐 때는 _edit_landmarks 또는 _skeleton._landmarks 사용
        landmarks = self._edit_landmarks
        if not landmarks:
            landmarks = self._skeleton._landmarks
        if not landmarks:
            return None

        logical = self._screen_to_logical(screen_pos)
        w = self._skeleton.width()
        h = self._skeleton.height()
        margin = 20

        hit_radius = HIT_RADIUS / max(self._scale, 0.1)
        best_idx = None
        best_dist = float('inf')

        for idx in EDITABLE_JOINTS:
            if idx >= len(landmarks):
                continue
            lm = landmarks[idx]
            if lm.get('visibility', 1) < 0.3:
                continue

            jx = lm['x'] * (w - 2 * margin) + margin
            jy = lm['y'] * (h - 2 * margin) + margin
            dx = logical.x() - jx
            dy = logical.y() - jy
            dist = (dx * dx + dy * dy) ** 0.5

            if dist < hit_radius and dist < best_dist:
                best_dist = dist
                best_idx = idx

        return best_idx

    # === 이벤트 처리 ===

    def showEvent(self, event):
        """위젯 표시 시"""
        super().showEvent(event)
        self._skeleton.installEventFilter(self)
        self._skeleton.paintEvent = self._custom_paint_event

    def eventFilter(self, obj, event):
        """SkeletonWidget 이벤트 가로채기"""
        if obj is not self._skeleton:
            return super().eventFilter(obj, event)

        if event.type() == QEvent.Type.MouseButtonPress:
            return self._on_mouse_press(event)
        elif event.type() == QEvent.Type.MouseMove:
            return self._on_mouse_move(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            return self._on_mouse_release(event)
        elif event.type() == QEvent.Type.Wheel:
            return self._on_wheel(event)

        return False

    def _on_mouse_press(self, event) -> bool:
        """마우스 눌림"""
        pos = QPointF(event.position())

        if event.button() == Qt.MouseButton.LeftButton:
            joint_idx = self._hit_test(pos)
            if joint_idx is not None:
                # 관절 클릭 → 편집 모드 자동 진입
                if not self._enter_edit_mode_if_needed():
                    return False
                self._dragging_joint = joint_idx
                self._skeleton.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
                return True
            elif self._edit_mode:
                # 편집 모드에서 빈 영역 → 팬 시작
                self._panning = True
                self._last_mouse_pos = pos
                self._skeleton.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
                return True
        elif event.button() == Qt.MouseButton.MiddleButton and self._edit_mode:
            self._panning = True
            self._last_mouse_pos = pos
            self._skeleton.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return True

        return False

    def _on_mouse_move(self, event) -> bool:
        """마우스 이동"""
        pos = QPointF(event.position())

        if self._dragging_joint is not None:
            # 관절 드래그
            logical = self._screen_to_logical(pos)
            nx, ny = self._logical_to_normalized(logical)

            lm = self._edit_landmarks[self._dragging_joint]
            lm['x'] = nx
            lm['y'] = ny

            self._skeleton.set_landmarks(self._edit_landmarks)
            self.landmarks_changed.emit(self._edit_landmarks)
            return True

        elif self._panning:
            # 팬
            delta = pos - self._last_mouse_pos
            self._pan_offset += delta
            self._last_mouse_pos = pos
            self._skeleton.update()
            return True
        else:
            # 호버: 커서 변경 (편집 모드 여부 무관하게 관절 위에서 커서 변경)
            joint_idx = self._hit_test(pos)
            if joint_idx is not None:
                self._skeleton.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self._skeleton.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        return False

    def _on_mouse_release(self, event) -> bool:
        """마우스 놓음"""
        if self._dragging_joint is not None:
            self._dragging_joint = None
            self._skeleton.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return True
        elif self._panning:
            self._panning = False
            self._skeleton.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return True
        return False

    def _on_wheel(self, event) -> bool:
        """마우스 휠 (편집 모드에서만)"""
        if not self._edit_mode:
            return False
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom(1.15)
        elif delta < 0:
            self._zoom(1 / 1.15)
        return True

    def _custom_paint_event(self, event):
        """커스텀 페인트 이벤트 (SkeletonWidget의 paintEvent를 대체)"""
        painter = QPainter(self._skeleton)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        landmarks = self._edit_landmarks if self._edit_mode else self._skeleton._landmarks

        if not landmarks:
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(
                self._skeleton.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "인체가 감지되지 않음"
            )
            return

        w = self._skeleton.width()
        h = self._skeleton.height()
        margin = 20

        # 편집 모드에서 트랜스폼 적용
        if self._edit_mode:
            painter.setTransform(self._build_transform())

        # 연결선 그리기
        self._skeleton._draw_connections(painter, w, h, margin, landmarks)

        # 관절점 그리기 (편집 모드에서는 편집 가능 관절 강조)
        if self._edit_mode:
            self._draw_joints_interactive(painter, w, h, margin, landmarks)
        else:
            self._skeleton._draw_joints(painter, w, h, margin, landmarks)

    def _draw_joints_interactive(self, painter: QPainter, w: int, h: int, margin: int, landmarks):
        """인터랙티브 모드 관절점 그리기 (편집 가능 관절 강조)"""
        for i, lm in enumerate(landmarks):
            if lm.get('visibility', 1) < 0.5:
                continue

            x = int(lm['x'] * (w - 2 * margin) + margin)
            y = int(lm['y'] * (h - 2 * margin) + margin)

            if i in EDITABLE_JOINTS:
                # 편집 가능 관절: 크게, 외곽선 강조
                color = self._skeleton._get_joint_color(i)

                # 외곽 글로우
                painter.setBrush(Qt.BrushStyle.NoBrush)
                glow_pen = QPen(QColor(255, 255, 255, 80), 2)
                painter.setPen(glow_pen)
                painter.drawEllipse(x - 10, y - 10, 20, 20)

                # 내부 원
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                radius = 7
                painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

                # 드래그 중인 관절 추가 강조
                if self._dragging_joint == i:
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.setPen(QPen(QColor(0, 255, 128, 180), 3))
                    painter.drawEllipse(x - 12, y - 12, 24, 24)
            else:
                # 편집 불가 관절: 기존 스타일 (작게)
                color = self._skeleton._get_joint_color(i)
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.GlobalColor.white, 1))
                radius = 4
                painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
