"""스테이터스 위젯 모듈 (스켈레톤 + 각도 + 인체공학적 평가 + 캡처 스프레드시트)"""
import platform
from PyQt6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
import numpy as np
from datetime import datetime
from typing import Optional

from .skeleton_widget import SkeletonWidget
from .angle_widget import AngleWidget
from .ergonomic import ErgonomicWidget
from .movement_analysis_widget import MovementAnalysisWidget
from .capture_spreadsheet_widget import CaptureSpreadsheetWidget
from .settings_dialog import SettingsDialog
from ..core.pose_detector import PoseDetector
from ..core.angle_calculator import AngleCalculator
from ..core.capture_model import CaptureRecord
from ..utils.image_saver import ImageSaver
from ..utils.config import Config


class StatusWidget(QWidget):
    """스테이터스 위젯 (스켈레톤 + 각도 + 인체공학적 평가 + 캡처 스프레드시트)"""

    # 시그널
    capture_added = pyqtSignal(int)  # 캡처 추가 시 행 인덱스 전달
    visibility_changed = pyqtSignal(str, bool)  # 패널 가시성 변경 (패널명, 상태)
    exit_requested = pyqtSignal()  # 종료 요청

    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self._config = config
        self._pose_detector = PoseDetector()
        self._angle_calculator = AngleCalculator()
        self._image_saver = ImageSaver(config=config)
        self._current_timestamp = 0.0
        self._current_frame_number = 0
        self._current_frame: Optional[np.ndarray] = None  # 현재 프레임 저장
        self._video_name: Optional[str] = None  # 동영상 이름

        # 단축키 표시 접두사 (macOS: ⌘, 기타: Ctrl+)
        self._shortcut_prefix = "⌘" if platform.system() == "Darwin" else "Ctrl+"

        self._init_ui()
        self._connect_signals()

    # 버튼 색상 정의 (각 버튼별 다른 색상)
    BUTTON_COLORS = {
        '상태': ('#3a9a8a', '#2a8a7a', '#4aaa9a'),      # 틸색
        '데이터': ('#5a7ab8', '#4a6aa8', '#6a8ac8'),    # 파란색
        '안전지표': ('#8a5ab8', '#7a4aa8', '#9a6ac8'),  # 보라색
        'RULA': ('#b8825a', '#a8724a', '#c8926a'),      # 주황색
        'REBA': ('#5ab87a', '#4aa86a', '#6ac88a'),      # 초록색
        'OWAS': ('#b85a6a', '#a84a5a', '#c86a7a'),      # 빨간색
        'NLE': ('#5a8ab8', '#4a7aa8', '#6a9ac8'),       # 하늘색
        'SI': ('#b8a85a', '#a8984a', '#c8b86a'),        # 황금색
        '설정': ('#7a7a7a', '#6a6a6a', '#8a8a8a'),      # 회색
        '종료': ('#c55a5a', '#b54a4a', '#d56a6a'),      # 진한 빨간색
    }

    @classmethod
    def _get_button_style(cls, color_key: str, is_on: bool, is_sub: bool = False) -> str:
        """버튼 스타일 생성"""
        colors = cls.BUTTON_COLORS.get(color_key, cls.BUTTON_COLORS['상태'])
        base, dark, light = colors
        padding = "5px 8px" if is_sub else "5px 12px"
        font_size = "10px" if is_sub else "11px"

        if is_on:
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {base}, stop:1 {dark});
                    color: white;
                    border: none;
                    padding: {padding};
                    border-radius: 4px;
                    font-size: {font_size};
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {light}, stop:1 {base});
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {dark}, stop:1 {base});
                }}
                QPushButton:disabled {{
                    background: #444444;
                    color: #666666;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {base}, stop:1 {dark});
                    color: #666666;
                    border: none;
                    padding: {padding};
                    border-radius: 4px;
                    font-size: {font_size};
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {light}, stop:1 {base});
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {dark}, stop:1 {base});
                }}
                QPushButton:disabled {{
                    background: #444444;
                    color: #555555;
                }}
            """

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 패널 가시성 상태 (버튼 없이 직접 관리)
        self._angle_visible = True
        self._spreadsheet_visible = True
        self._ergonomic_visible = True
        self._analysis_visible = True
        self._rula_visible = True
        self._reba_visible = True
        self._owas_visible = True
        self._nle_visible = False  # 기본 숨김
        self._si_visible = False   # 기본 숨김

        # 스플리터 스타일 정의
        horizontal_splitter_style = """
            QSplitter::handle:horizontal {
                width: 2px;
                margin-left: 1px;
                margin-right: 5px;
                background: qlineargradient(
                    x1: 0, y1: 0.25,
                    x2: 0, y2: 0.75,
                    stop: 0 transparent,
                    stop: 0.001 #888888,
                    stop: 0.999 #888888,
                    stop: 1 transparent
                );
            }
        """
        vertical_splitter_style = """
            QSplitter::handle:vertical {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 0,
                    stop: 0 transparent,
                    stop: 0.24 transparent,
                    stop: 0.25 #888888,
                    stop: 0.75 #888888,
                    stop: 0.76 transparent,
                    stop: 1 transparent
                );
            }
        """

        # 메인 스플리터 (상/하 분할)
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)
        self._main_splitter.setHandleWidth(2)
        self._main_splitter.setStyleSheet(vertical_splitter_style)

        # 상단: 스켈레톤 + 각도 (좌/우 분할)
        self._top_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._top_splitter.setHandleWidth(8)
        self._top_splitter.setStyleSheet(horizontal_splitter_style)

        # 왼쪽: 스켈레톤 시각화
        self._skeleton_widget = SkeletonWidget()
        self._skeleton_widget.setMinimumWidth(200)  # 스켈레톤 최소 너비
        self._top_splitter.addWidget(self._skeleton_widget)

        # 오른쪽: 각도 표시
        self._angle_widget = AngleWidget()
        self._angle_widget.setMinimumWidth(150)  # 각도 패널 최소 너비
        self._top_splitter.addWidget(self._angle_widget)

        # 스플리터로 패널이 완전히 축소되지 않도록 설정
        self._top_splitter.setCollapsible(0, False)  # 스켈레톤
        self._top_splitter.setCollapsible(1, False)  # 각도

        # 50:50 비율
        self._top_splitter.setSizes([400, 400])

        # 상단 패널 최소 높이 설정
        self._top_splitter.setMinimumHeight(150)
        self._main_splitter.addWidget(self._top_splitter)

        # 중단: 분석 결과(좌) + 안전 지표(우) (좌/우 분할)
        self._middle_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._middle_splitter.setHandleWidth(8)
        self._middle_splitter.setStyleSheet(horizontal_splitter_style)
        self._middle_splitter.setMinimumHeight(100)

        # 좌: 분석 결과
        self._movement_analysis_widget = MovementAnalysisWidget()
        self._movement_analysis_widget.setMinimumWidth(200)
        self._middle_splitter.addWidget(self._movement_analysis_widget)

        # 우: 안전 지표
        self._ergonomic_widget = ErgonomicWidget()
        self._ergonomic_widget.setMinimumWidth(200)
        self._middle_splitter.addWidget(self._ergonomic_widget)

        # 스플리터로 패널이 완전히 축소되지 않도록 설정
        self._middle_splitter.setCollapsible(0, False)  # 분석 결과
        self._middle_splitter.setCollapsible(1, False)  # 안전 지표

        # 50:50 비율
        self._middle_splitter.setSizes([400, 400])

        self._main_splitter.addWidget(self._middle_splitter)

        # 하단: 캡처 스프레드시트
        self._spreadsheet_widget = CaptureSpreadsheetWidget(config=self._config)
        self._spreadsheet_widget.setMinimumHeight(100)  # 스프레드시트 최소 높이
        self._main_splitter.addWidget(self._spreadsheet_widget)

        # 스플리터로 패널이 완전히 축소되지 않도록 설정
        self._main_splitter.setCollapsible(0, False)  # 상단 (스켈레톤+각도)
        self._main_splitter.setCollapsible(1, False)  # 중단 (분석 결과+안전지표)
        self._main_splitter.setCollapsible(2, False)  # 하단 (스프레드시트)

        # 상단:중단:하단 = 35:35:30 비율
        self._main_splitter.setSizes([350, 350, 300])

        layout.addWidget(self._main_splitter)

    def _connect_signals(self):
        """시그널 연결"""
        # 버튼이 메인 툴바로 이동하여 시그널 연결 불필요
        pass

    # === 외부에서 패널 가시성 제어 ===

    def set_angle_visible(self, visible: bool):
        """각도 패널 가시성 설정"""
        self._angle_visible = visible
        self._angle_widget.setVisible(visible)
        self.visibility_changed.emit('angle', visible)

    def set_ergonomic_visible(self, visible: bool):
        """안전지표 패널 가시성 설정"""
        self._ergonomic_visible = visible
        self._ergonomic_widget.setVisible(visible)
        self._update_middle_visibility()
        self.visibility_changed.emit('ergonomic', visible)

    def set_analysis_visible(self, visible: bool):
        """분석 결과 패널 가시성 설정"""
        self._analysis_visible = visible
        self._movement_analysis_widget.setVisible(visible)
        self._update_middle_visibility()
        self.visibility_changed.emit('analysis', visible)

    def _update_middle_visibility(self):
        """분석 결과와 안전 지표 둘 다 숨김일 때만 중단 패널 숨김"""
        self._middle_splitter.setVisible(
            self._analysis_visible or self._ergonomic_visible
        )

    def set_spreadsheet_visible(self, visible: bool):
        """스프레드시트 패널 가시성 설정"""
        self._spreadsheet_visible = visible
        self._spreadsheet_widget.setVisible(visible)
        self.visibility_changed.emit('spreadsheet', visible)

    def set_rula_visible(self, visible: bool):
        """RULA 패널 가시성 설정"""
        self._rula_visible = visible
        self._ergonomic_widget.set_rula_visible(visible)

    def set_reba_visible(self, visible: bool):
        """REBA 패널 가시성 설정"""
        self._reba_visible = visible
        self._ergonomic_widget.set_reba_visible(visible)

    def set_owas_visible(self, visible: bool):
        """OWAS 패널 가시성 설정"""
        self._owas_visible = visible
        self._ergonomic_widget.set_owas_visible(visible)

    def is_angle_visible(self) -> bool:
        """각도 패널 가시성 반환"""
        return self._angle_visible

    def is_ergonomic_visible(self) -> bool:
        """안전지표 패널 가시성 반환"""
        return self._ergonomic_visible

    def is_analysis_visible(self) -> bool:
        """분석 결과 패널 가시성 반환"""
        return self._analysis_visible

    def is_spreadsheet_visible(self) -> bool:
        """스프레드시트 패널 가시성 반환"""
        return self._spreadsheet_visible

    def is_rula_visible(self) -> bool:
        """RULA 패널 가시성 반환"""
        return self._rula_visible

    def is_reba_visible(self) -> bool:
        """REBA 패널 가시성 반환"""
        return self._reba_visible

    def is_owas_visible(self) -> bool:
        """OWAS 패널 가시성 반환"""
        return self._owas_visible

    def set_nle_visible(self, visible: bool):
        """NLE 패널 가시성 설정"""
        self._nle_visible = visible
        self._ergonomic_widget.set_nle_visible(visible)

    def set_si_visible(self, visible: bool):
        """SI 패널 가시성 설정"""
        self._si_visible = visible
        self._ergonomic_widget.set_si_visible(visible)

    def is_nle_visible(self) -> bool:
        """NLE 패널 가시성 반환"""
        return self._nle_visible

    def is_si_visible(self) -> bool:
        """SI 패널 가시성 반환"""
        return self._si_visible

    def process_frame(self, frame: np.ndarray):
        """프레임 처리"""
        # 현재 프레임 저장 (캡처용)
        self._current_frame = frame.copy()

        # 포즈 감지
        result = self._pose_detector.detect(frame)

        if result.pose_detected and result.landmarks:
            # 스켈레톤 표시
            self._skeleton_widget.set_landmarks(result.landmarks)

            # 각도 계산 및 표시
            angles = self._angle_calculator.calculate_all_angles(result.landmarks)
            self._angle_widget.set_angles(angles)

            # 인체공학적 평가 업데이트
            self._ergonomic_widget.update_assessment(angles, result.landmarks)
        else:
            # 감지 안 됨
            self._skeleton_widget.clear()
            self._angle_widget.clear()
            self._ergonomic_widget.clear()

    def set_current_position(self, timestamp: float, frame_number: int):
        """현재 재생 위치 설정"""
        self._current_timestamp = timestamp
        self._current_frame_number = frame_number

    def capture_current_state(self) -> Optional[int]:
        """
        현재 상태를 캡처하여 스프레드시트에 추가

        Returns:
            추가된 행 인덱스 또는 None (결과 없을 시)
        """
        if not self._ergonomic_widget.has_results():
            return None

        results = self._ergonomic_widget.get_current_results()
        rula = results.get('rula')
        reba = results.get('reba')
        owas = results.get('owas')
        nle = results.get('nle')
        si = results.get('si')

        # NLE/SI 입력값 가져오기
        nle_inputs = self._ergonomic_widget.get_nle_inputs()
        si_inputs = self._ergonomic_widget.get_si_inputs()

        # 이미지 저장
        video_frame_path = None
        skeleton_image_path = None

        if self._video_name:
            video_frame_path, skeleton_image_path = self._image_saver.save_capture(
                video_name=self._video_name,
                timestamp=self._current_timestamp,
                frame=self._current_frame,
                skeleton_pixmap=self._skeleton_widget.grab_as_pixmap(),
            )

        # CaptureRecord 생성
        record = CaptureRecord(
            timestamp=self._current_timestamp,
            frame_number=self._current_frame_number,
            capture_time=datetime.now(),
            # RULA
            rula_upper_arm=rula.upper_arm_score if rula else 0,
            rula_lower_arm=rula.lower_arm_score if rula else 0,
            rula_wrist=rula.wrist_score if rula else 0,
            rula_wrist_twist=rula.wrist_twist_score if rula else 0,
            rula_neck=rula.neck_score if rula else 0,
            rula_trunk=rula.trunk_score if rula else 0,
            rula_leg=rula.leg_score if rula else 0,
            rula_score_a=rula.arm_wrist_score if rula else 0,
            rula_score_b=rula.neck_trunk_score if rula else 0,
            rula_score=rula.final_score if rula else 0,
            rula_risk=rula.risk_level if rula else '',
            # RULA 세부 점수
            rula_upper_arm_base=rula.upper_arm_base if rula else 0,
            rula_upper_arm_shoulder_raised=rula.upper_arm_shoulder_raised if rula else 0,
            rula_upper_arm_abducted=rula.upper_arm_abducted if rula else 0,
            rula_upper_arm_supported=rula.upper_arm_supported if rula else 0,
            rula_lower_arm_base=rula.lower_arm_base if rula else 0,
            rula_lower_arm_working_across=rula.lower_arm_working_across if rula else 0,
            rula_wrist_base=rula.wrist_base if rula else 0,
            rula_wrist_bent_midline=rula.wrist_bent_midline if rula else 0,
            rula_neck_base=rula.neck_base if rula else 0,
            rula_neck_twisted=rula.neck_twisted if rula else 0,
            rula_neck_side_bending=rula.neck_side_bending if rula else 0,
            rula_trunk_base=rula.trunk_base if rula else 0,
            rula_trunk_twisted=rula.trunk_twisted if rula else 0,
            rula_trunk_side_bending=rula.trunk_side_bending if rula else 0,
            # REBA
            reba_neck=reba.neck_score if reba else 0,
            reba_trunk=reba.trunk_score if reba else 0,
            reba_leg=reba.leg_score if reba else 0,
            reba_upper_arm=reba.upper_arm_score if reba else 0,
            reba_lower_arm=reba.lower_arm_score if reba else 0,
            reba_wrist=reba.wrist_score if reba else 0,
            reba_score_a=reba.group_a_score if reba else 0,
            reba_score_b=reba.group_b_score if reba else 0,
            reba_score=reba.final_score if reba else 0,
            reba_risk=reba.risk_level if reba else '',
            # REBA 세부 점수
            reba_neck_base=reba.neck_base if reba else 0,
            reba_neck_twist_side=reba.neck_twist_side if reba else 0,
            reba_trunk_base=reba.trunk_base if reba else 0,
            reba_trunk_twist_side=reba.trunk_twist_side if reba else 0,
            reba_leg_base=reba.leg_base if reba else 0,
            reba_leg_knee_30_60=reba.leg_knee_30_60 if reba else 0,
            reba_leg_knee_over_60=reba.leg_knee_over_60 if reba else 0,
            reba_upper_arm_base=reba.upper_arm_base if reba else 0,
            reba_upper_arm_shoulder_raised=reba.upper_arm_shoulder_raised if reba else 0,
            reba_upper_arm_abducted=reba.upper_arm_abducted if reba else 0,
            reba_upper_arm_supported=reba.upper_arm_supported if reba else 0,
            reba_wrist_base=reba.wrist_base if reba else 0,
            reba_wrist_twisted=reba.wrist_twisted if reba else 0,
            # OWAS
            owas_back=owas.back_code if owas else 1,
            owas_arms=owas.arms_code if owas else 1,
            owas_legs=owas.legs_code if owas else 1,
            owas_load=owas.load_code if owas else 1,
            owas_code=owas.posture_code if owas else '1111',
            owas_ac=owas.action_category if owas else 1,
            owas_risk=owas.risk_level if owas else '',
            # 이미지 경로
            video_frame_path=video_frame_path,
            skeleton_image_path=skeleton_image_path,
            # NLE
            nle_h=nle_inputs.get('h', 25),
            nle_v=nle_inputs.get('v', 75),
            nle_d=nle_inputs.get('d', 25),
            nle_a=nle_inputs.get('a', 0),
            nle_f=nle_inputs.get('f', 1),
            nle_c=nle_inputs.get('c', 1),
            nle_load=nle_inputs.get('load', 0),
            nle_rwl=nle.rwl if nle else 0,
            nle_li=nle.li if nle else 0,
            nle_risk=nle.risk_level if nle else '',
            # SI
            si_ie=si_inputs.get('ie', 1),
            si_de=si_inputs.get('de', 1),
            si_em=si_inputs.get('em', 1),
            si_hwp=si_inputs.get('hwp', 1),
            si_sw=si_inputs.get('sw', 1),
            si_dd=si_inputs.get('dd', 1),
            si_score=si.score if si else 0,
            si_risk=si.risk_level if si else '',
        )

        # 스프레드시트에 추가
        row_idx = self._spreadsheet_widget.add_record(record)
        self.capture_added.emit(row_idx)
        return row_idx

    def set_video_name(self, video_name: str):
        """동영상 이름 설정"""
        self._video_name = video_name
        self._spreadsheet_widget.set_video_name(video_name)

    @property
    def spreadsheet_widget(self) -> CaptureSpreadsheetWidget:
        """스프레드시트 위젯 반환"""
        return self._spreadsheet_widget

    @property
    def ergonomic_widget(self) -> ErgonomicWidget:
        """인체공학적 평가 위젯 반환"""
        return self._ergonomic_widget

    @property
    def movement_analysis_widget(self) -> MovementAnalysisWidget:
        """분석 결과 위젯 반환"""
        return self._movement_analysis_widget

    def switch_to_analysis_tab(self):
        """분석 결과 패널 표시"""
        if not self._analysis_visible:
            self.set_analysis_visible(True)

    def _open_settings(self):
        """설정 다이얼로그 열기"""
        dialog = SettingsDialog(self._config, self)
        dialog.exec()

    def release(self):
        """리소스 해제"""
        self._pose_detector.release()
