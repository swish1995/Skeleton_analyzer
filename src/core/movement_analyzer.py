"""신체 부위별 움직임 빈도 분석 엔진"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.core.angle_calculator import ANGLE_DEFINITIONS

# 관절명 → 한글 표시명 매핑
JOINT_DISPLAY_NAMES = {
    'neck': '목',
    'left_shoulder': '좌측 어깨',
    'right_shoulder': '우측 어깨',
    'left_elbow': '좌측 팔꿈치',
    'right_elbow': '우측 팔꿈치',
    'left_wrist': '좌측 손목',
    'right_wrist': '우측 손목',
    'left_hip': '좌측 엉덩이',
    'right_hip': '우측 엉덩이',
    'left_knee': '좌측 무릎',
    'right_knee': '우측 무릎',
    'left_ankle': '좌측 발목',
    'right_ankle': '우측 발목',
}

# RULA 부위별 점수 → 관절 매핑 (고위험 기준: 점수 >= 4)
RULA_HIGH_RISK_THRESHOLD = 4
RULA_JOINT_MAPPING = {
    'upper_arm_score': ['left_shoulder', 'right_shoulder'],
    'lower_arm_score': ['left_elbow', 'right_elbow'],
    'wrist_score': ['left_wrist', 'right_wrist'],
    'neck_score': ['neck'],
    'trunk_score': ['left_hip', 'right_hip'],
}

# REBA 부위별 점수 → 관절 매핑 (고위험 기준: 점수 >= 4)
REBA_HIGH_RISK_THRESHOLD = 4
REBA_JOINT_MAPPING = {
    'upper_arm_score': ['left_shoulder', 'right_shoulder'],
    'lower_arm_score': ['left_elbow', 'right_elbow'],
    'wrist_score': ['left_wrist', 'right_wrist'],
    'neck_score': ['neck'],
    'trunk_score': ['left_hip', 'right_hip'],
    'leg_score': ['left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
}

DEFAULT_THRESHOLD = 15.0


@dataclass
class BodyPartStats:
    """신체 부위별 통계 데이터"""
    joint_name: str
    display_name: str
    total_frames: int = 0
    movement_count: int = 0
    high_risk_frames: int = 0
    high_risk_ratio: float = 0.0
    max_angle: float = 0.0
    min_angle: float = 0.0
    avg_angle: float = 0.0
    cumulative_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            'joint_name': self.joint_name,
            'display_name': self.display_name,
            'total_frames': self.total_frames,
            'movement_count': self.movement_count,
            'high_risk_frames': self.high_risk_frames,
            'high_risk_ratio': self.high_risk_ratio,
            'max_angle': self.max_angle,
            'min_angle': self.min_angle,
            'avg_angle': self.avg_angle,
            'cumulative_score': self.cumulative_score,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'BodyPartStats':
        return cls(**d)


@dataclass
class MovementAnalysisResult:
    """움직임 분석 결과"""
    body_parts: Dict[str, BodyPartStats] = field(default_factory=dict)
    total_frames: int = 0
    analyzed_frames: int = 0
    skipped_frames: int = 0
    sample_interval: int = 1
    duration_seconds: float = 0.0

    def get_sorted_by_movement(self) -> List[BodyPartStats]:
        return sorted(self.body_parts.values(), key=lambda s: s.movement_count, reverse=True)

    def get_sorted_by_risk(self) -> List[BodyPartStats]:
        return sorted(self.body_parts.values(), key=lambda s: s.high_risk_ratio, reverse=True)

    def to_dict(self) -> dict:
        return {
            'body_parts': {name: stats.to_dict() for name, stats in self.body_parts.items()},
            'total_frames': self.total_frames,
            'analyzed_frames': self.analyzed_frames,
            'skipped_frames': self.skipped_frames,
            'sample_interval': self.sample_interval,
            'duration_seconds': self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'MovementAnalysisResult':
        body_parts = {
            name: BodyPartStats.from_dict(stats_d)
            for name, stats_d in d['body_parts'].items()
        }
        return cls(
            body_parts=body_parts,
            total_frames=d['total_frames'],
            analyzed_frames=d['analyzed_frames'],
            skipped_frames=d['skipped_frames'],
            sample_interval=d['sample_interval'],
            duration_seconds=d.get('duration_seconds', 0.0),
        )


class MovementAnalyzer:
    """움직임 빈도 분석 엔진"""

    def __init__(self, threshold: float = DEFAULT_THRESHOLD, sample_interval: int = 1):
        self._threshold = threshold
        self._sample_interval = sample_interval
        self._prev_angles: Optional[Dict[str, float]] = None
        self._total_frames = 0
        self._analyzed_frames = 0
        self._skipped_frames = 0

        # 관절별 내부 누적 데이터
        self._movement_counts: Dict[str, int] = {}
        self._high_risk_frames: Dict[str, int] = {}
        self._angle_sums: Dict[str, float] = {}
        self._angle_counts: Dict[str, int] = {}
        self._max_angles: Dict[str, float] = {}
        self._min_angles: Dict[str, float] = {}
        self._risk_score_sums: Dict[str, float] = {}

        self._init_joints()

    def _init_joints(self):
        for name in ANGLE_DEFINITIONS:
            self._movement_counts[name] = 0
            self._high_risk_frames[name] = 0
            self._angle_sums[name] = 0.0
            self._angle_counts[name] = 0
            self._max_angles[name] = 0.0
            self._min_angles[name] = 0.0
            self._risk_score_sums[name] = 0.0

    def get_state(self) -> dict:
        """내부 상태 직렬화 (재개용)"""
        return {
            'prev_angles': dict(self._prev_angles) if self._prev_angles else None,
            'total_frames': self._total_frames,
            'analyzed_frames': self._analyzed_frames,
            'skipped_frames': self._skipped_frames,
            'movement_counts': dict(self._movement_counts),
            'high_risk_frames': dict(self._high_risk_frames),
            'angle_sums': dict(self._angle_sums),
            'angle_counts': dict(self._angle_counts),
            'max_angles': dict(self._max_angles),
            'min_angles': dict(self._min_angles),
            'risk_score_sums': dict(self._risk_score_sums),
        }

    def load_state(self, state: dict):
        """직렬화된 상태 복원 (재개용)"""
        self._prev_angles = state['prev_angles']
        self._total_frames = state['total_frames']
        self._analyzed_frames = state['analyzed_frames']
        self._skipped_frames = state['skipped_frames']
        self._movement_counts = dict(state['movement_counts'])
        self._high_risk_frames = dict(state['high_risk_frames'])
        self._angle_sums = dict(state['angle_sums'])
        self._angle_counts = dict(state['angle_counts'])
        self._max_angles = dict(state['max_angles'])
        self._min_angles = dict(state['min_angles'])
        self._risk_score_sums = dict(state['risk_score_sums'])

    def reset(self):
        self._prev_angles = None
        self._total_frames = 0
        self._analyzed_frames = 0
        self._skipped_frames = 0
        self._init_joints()

    def update(self, angles: Dict[str, float], rula_result, reba_result, frame_index: int = -1):
        """프레임 데이터를 누적 분석

        Args:
            angles: 13개 관절 각도 딕셔너리
            rula_result: RULAResult
            reba_result: REBAResult
            frame_index: 프레임 인덱스 (-1이면 샘플링 없이 모두 처리)
        """
        self._total_frames += 1

        # 샘플링: frame_index가 지정된 경우 sample_interval에 따라 스킵
        if frame_index >= 0 and frame_index % self._sample_interval != 0:
            return

        self._analyzed_frames += 1

        for name in ANGLE_DEFINITIONS:
            angle = angles.get(name, 0.0)

            # 각도 통계 업데이트
            self._angle_sums[name] += angle
            self._angle_counts[name] += 1

            if self._angle_counts[name] == 1:
                self._max_angles[name] = angle
                self._min_angles[name] = angle
            else:
                if angle > self._max_angles[name]:
                    self._max_angles[name] = angle
                if angle < self._min_angles[name]:
                    self._min_angles[name] = angle

            # 움직임 카운팅: 이전 분석 프레임 대비 각도 변화 > threshold
            if self._prev_angles is not None:
                delta = abs(angle - self._prev_angles.get(name, 0.0))
                if delta > self._threshold:
                    self._movement_counts[name] += 1

        # 고위험 자세 집계 (RULA)
        self._update_high_risk_from_rula(rula_result)

        # 고위험 자세 집계 (REBA)
        self._update_high_risk_from_reba(reba_result)

        # 누적 위험 점수 업데이트
        self._update_risk_scores(rula_result, reba_result)

        # 이전 각도 저장 (분석된 프레임만)
        self._prev_angles = dict(angles)

    def _update_high_risk_from_rula(self, rula_result):
        for score_attr, joint_names in RULA_JOINT_MAPPING.items():
            score = getattr(rula_result, score_attr, 0)
            if score >= RULA_HIGH_RISK_THRESHOLD:
                for joint in joint_names:
                    self._high_risk_frames[joint] += 1

    def _update_high_risk_from_reba(self, reba_result):
        """REBA에서 RULA에 없는 관절(leg_score 등)만 추가 카운트"""
        for score_attr, joint_names in REBA_JOINT_MAPPING.items():
            if score_attr in RULA_JOINT_MAPPING:
                continue
            score = getattr(reba_result, score_attr, 0)
            if score >= REBA_HIGH_RISK_THRESHOLD:
                for joint in joint_names:
                    self._high_risk_frames[joint] += 1

    def _update_risk_scores(self, rula_result, reba_result):
        """누적 위험 점수 업데이트"""
        for score_attr, joint_names in RULA_JOINT_MAPPING.items():
            score = getattr(rula_result, score_attr, 0)
            for joint in joint_names:
                self._risk_score_sums[joint] += score

    def get_result(self) -> MovementAnalysisResult:
        body_parts = {}
        for name in ANGLE_DEFINITIONS:
            count = self._angle_counts[name]
            total_frames = count
            avg_angle = self._angle_sums[name] / count if count > 0 else 0.0
            high_risk = self._high_risk_frames[name]
            high_risk_ratio = high_risk / count if count > 0 else 0.0
            movement_count = self._movement_counts[name]
            avg_risk = self._risk_score_sums[name] / count if count > 0 else 0.0
            cumulative_score = movement_count * avg_risk

            body_parts[name] = BodyPartStats(
                joint_name=name,
                display_name=JOINT_DISPLAY_NAMES.get(name, name),
                total_frames=total_frames,
                movement_count=movement_count,
                high_risk_frames=high_risk,
                high_risk_ratio=high_risk_ratio,
                max_angle=self._max_angles[name],
                min_angle=self._min_angles[name],
                avg_angle=avg_angle,
                cumulative_score=cumulative_score,
            )

        return MovementAnalysisResult(
            body_parts=body_parts,
            total_frames=self._total_frames,
            analyzed_frames=self._analyzed_frames,
            skipped_frames=self._skipped_frames,
            sample_interval=self._sample_interval,
        )
