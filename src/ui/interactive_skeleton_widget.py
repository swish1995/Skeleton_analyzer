"""인터랙티브 스켈레톤 에디터 위젯 모듈"""
import copy
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QEvent
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QTransform, QCursor,
)
from typing import List, Dict, Optional, Set, Tuple

from .skeleton_widget import SkeletonWidget, SKELETON_CONNECTIONS
from ..license import LicenseManager

# 편집 가능 관절 인덱스: 코(0), 어깨(11,12), 팔꿈치(13,14), 손목(15,16),
# 고관절(23,24), 무릎(25,26), 발목(27,28)
EDITABLE_JOINTS = {0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28}

# 히트 반경 (화면 픽셀)
HIT_RADIUS = 12

# --- Kinematic Chain: 관절을 움직이면 자식 관절이 함께 따라감 ---
# {관절 인덱스: [자식 인덱스들]} - 직접 자식만 정의, 재귀로 전체 하위 탐색
JOINT_CHILDREN: Dict[int, List[int]] = {
    # 머리: 코를 움직이면 얼굴 전체
    0: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    # 왼팔 체인
    11: [13],       # 왼어깨 → 왼팔꿈치
    13: [15],       # 왼팔꿈치 → 왼손목
    15: [17, 19, 21],  # 왼손목 → 왼손가락들
    # 오른팔 체인
    12: [14],       # 오른어깨 → 오른팔꿈치
    14: [16],       # 오른팔꿈치 → 오른손목
    16: [18, 20, 22],  # 오른손목 → 오른손가락들
    # 왼다리 체인
    23: [25],       # 왼골반 → 왼무릎
    25: [27],       # 왼무릎 → 왼발목
    27: [29, 31],   # 왼발목 → 왼발
    # 오른다리 체인
    24: [26],       # 오른골반 → 오른무릎
    26: [28],       # 오른무릎 → 오른발목
    28: [30, 32],   # 오른발목 → 오른발
}

# --- 가동 범위 (Range of Motion) ---
# (부모, 관절, 자식): (최소각도, 최대각도) - 단위: degree
# 각도는 부모-관절-자식 세 점이 이루는 각도
JOINT_ROM: Dict[Tuple[int, int, int], Tuple[float, float]] = {
    # 팔꿈치: 30°~180° (완전 펴짐=180°, 과도 굽힘 방지)
    (11, 13, 15): (30, 180),   # 왼팔꿈치
    (12, 14, 16): (30, 180),   # 오른팔꿈치
    # 어깨: 10°~180°
    (23, 11, 13): (10, 180),   # 왼어깨 (골반-어깨-팔꿈치)
    (24, 12, 14): (10, 180),   # 오른어깨
    # 무릎: 30°~180°
    (23, 25, 27): (30, 180),   # 왼무릎
    (24, 26, 28): (30, 180),   # 오른무릎
    # 골반: 30°~180°
    (11, 23, 25): (30, 180),   # 왼골반 (어깨-골반-무릎)
    (12, 24, 26): (30, 180),   # 오른골반
    # 손목: 90°~210°
    (13, 15, 19): (90, 210),   # 왼손목 (팔꿈치-손목-검지)
    (14, 16, 20): (90, 210),   # 오른손목
}


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

    def _get_all_descendants(self, joint_idx: int) -> Set[int]:
        """관절의 모든 하위 자손 인덱스 반환 (재귀)"""
        result: Set[int] = set()
        direct = JOINT_CHILDREN.get(joint_idx, [])
        for child in direct:
            result.add(child)
            result.update(self._get_all_descendants(child))
        return result

    @staticmethod
    def _calc_angle(ax: float, ay: float, bx: float, by: float,
                    cx: float, cy: float) -> float:
        """세 점 A-B-C에서 B 지점의 각도 (degree) 계산"""
        v1x, v1y = ax - bx, ay - by
        v2x, v2y = cx - bx, cy - by
        dot = v1x * v2x + v1y * v2y
        cross = v1x * v2y - v1y * v2x
        angle = math.atan2(abs(cross), dot)
        return math.degrees(angle)

    def _apply_rom_constraints(self, moved_idx: int):
        """이동된 관절에 관련된 가동 범위 제한 적용"""
        lms = self._edit_landmarks
        if not lms:
            return

        for (p, j, c), (min_a, max_a) in JOINT_ROM.items():
            # 이동된 관절이 이 ROM 트리플에 관련된 경우만 처리
            if moved_idx not in (p, j, c):
                continue
            if max(p, j, c) >= len(lms):
                continue

            px, py = lms[p]['x'], lms[p]['y']
            jx, jy = lms[j]['x'], lms[j]['y']
            cx, cy = lms[c]['x'], lms[c]['y']

            angle = self._calc_angle(px, py, jx, jy, cx, cy)

            if min_a <= angle <= max_a:
                continue

            # 범위 초과 → 클램핑 (움직인 관절을 제한 각도로 보정)
            target_angle = max(min_a, min(max_a, angle))

            # 어떤 점을 보정할지: 이동된 관절이 c이면 c를 보정, 아니면 c를 보정
            # (보통 자식 쪽이 움직이므로 c를 보정하는 게 자연스러움)
            if moved_idx == p:
                # 부모를 움직인 경우 → 관절(j) 기준으로 자식(c)은 이미 따라감, p를 보정
                self._clamp_point_to_angle(p, j, c, target_angle, adjust_target=p, lms=lms)
            elif moved_idx == c:
                self._clamp_point_to_angle(p, j, c, target_angle, adjust_target=c, lms=lms)
            else:
                # j를 움직인 경우 → c를 보정
                self._clamp_point_to_angle(p, j, c, target_angle, adjust_target=c, lms=lms)

    def _clamp_point_to_angle(self, p: int, j: int, c: int,
                              target_angle: float, adjust_target: int,
                              lms: list):
        """adjust_target 점을 이동하여 p-j-c 각도가 target_angle이 되도록 보정"""
        jx, jy = lms[j]['x'], lms[j]['y']

        # 보정할 점의 반대편 점
        if adjust_target == c:
            ref_x, ref_y = lms[p]['x'], lms[p]['y']
            cur_x, cur_y = lms[c]['x'], lms[c]['y']
        else:
            ref_x, ref_y = lms[c]['x'], lms[c]['y']
            cur_x, cur_y = lms[p]['x'], lms[p]['y']

        # j→ref 벡터의 각도
        ref_angle = math.atan2(ref_y - jy, ref_x - jx)
        # j→cur 벡터의 각도와 거리
        cur_dist = math.hypot(cur_x - jx, cur_y - jy)
        if cur_dist < 1e-6:
            return

        cur_angle = math.atan2(cur_y - jy, cur_x - jx)

        # ref→cur의 회전 방향 결정
        diff = cur_angle - ref_angle
        sign = 1.0 if diff >= 0 else -1.0
        # 부호를 유지하면서 target_angle 적용
        new_angle = ref_angle + sign * math.radians(target_angle)

        new_x = jx + cur_dist * math.cos(new_angle)
        new_y = jy + cur_dist * math.sin(new_angle)

        # 보정 적용
        old_x = lms[adjust_target]['x']
        old_y = lms[adjust_target]['y']
        lms[adjust_target]['x'] = max(0.0, min(1.0, new_x))
        lms[adjust_target]['y'] = max(0.0, min(1.0, new_y))

        # 보정된 점의 자손도 함께 이동
        dx = lms[adjust_target]['x'] - old_x
        dy = lms[adjust_target]['y'] - old_y
        if abs(dx) > 1e-6 or abs(dy) > 1e-6:
            for desc in self._get_all_descendants(adjust_target):
                if desc < len(lms) and desc != adjust_target:
                    lms[desc]['x'] = max(0.0, min(1.0, lms[desc]['x'] + dx))
                    lms[desc]['y'] = max(0.0, min(1.0, lms[desc]['y'] + dy))

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

            idx = self._dragging_joint
            lm = self._edit_landmarks[idx]
            old_x, old_y = lm['x'], lm['y']
            dx, dy = nx - old_x, ny - old_y

            # 1) 드래그 대상 관절 이동
            lm['x'] = nx
            lm['y'] = ny

            # 2) 자식 관절 연동 이동
            children = self._get_all_descendants(idx)
            for child_idx in children:
                if child_idx < len(self._edit_landmarks):
                    clm = self._edit_landmarks[child_idx]
                    clm['x'] = max(0.0, min(1.0, clm['x'] + dx))
                    clm['y'] = max(0.0, min(1.0, clm['y'] + dy))

            # 3) 가동 범위 제한
            self._apply_rom_constraints(idx)

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
