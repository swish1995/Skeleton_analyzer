"""인체공학적 평가 기본 클래스"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List


# 감지 임계값 기본값
# 실제 적용값 = 기본값 × detection_sensitivity
DEFAULT_DETECTION_THRESHOLDS = {
    # ── 위치 감지 (정규화 좌표, 0~1) ──
    'neck_twisted': 0.08,          # 목 회전 (코-어깨중심 x좌표 차이)
    'trunk_side_bending': 0.05,    # 몸통 측굴 (좌우 어깨 y좌표 차이)
    'upper_arm_abducted': 0.06,    # 상박 외전 (팔꿈치-어깨 x좌표 차이)
    # ── 각도 점수 임계값 (도, 2D 카메라 과대측정 보정 반영) ──
    'neck_flexion_mid': 15,        # 목 1→2점 경계 (RULA 표준: 10°)
    'neck_flexion_high': 35,       # 목 2→3점 경계 (RULA 표준: 20°)
    'elbow_flexion_low': 0,        # 하박 1점 하한 (RULA 표준: 60°, 2D 과소측정 보정)
    'elbow_flexion_high': 110,     # 하박 1점 상한 (RULA 표준: 100°)
}


@dataclass
class AssessmentResult:
    """평가 결과 기본 클래스"""
    final_score: int
    risk_level: str
    action_required: str
    details: Dict[str, Any]


class BaseAssessment(ABC):
    """인체공학적 평가 추상 기본 클래스"""

    # 위험 수준 정의 (서브클래스에서 오버라이드)
    RISK_LEVELS: Dict[str, str] = {}

    # 감지 민감도 (1.0=기본, >1.0=둔감해짐, <1.0=민감해짐)
    detection_sensitivity: float = 1.0

    @abstractmethod
    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> AssessmentResult:
        """
        평가 점수 계산

        Args:
            angles: 관절 각도 딕셔너리
            landmarks: MediaPipe landmark 리스트

        Returns:
            AssessmentResult: 평가 결과
        """
        pass

    @abstractmethod
    def get_risk_level(self, score: int) -> str:
        """
        점수에 따른 위험 수준 반환

        Args:
            score: 평가 점수

        Returns:
            str: 위험 수준
        """
        pass

    @abstractmethod
    def get_action_required(self, risk_level: str) -> str:
        """
        위험 수준에 따른 조치 사항 반환

        Args:
            risk_level: 위험 수준

        Returns:
            str: 조치 사항
        """
        pass

    def _get_threshold(self, key: str) -> float:
        """임계값 조회 (민감도 적용)"""
        base = DEFAULT_DETECTION_THRESHOLDS.get(key, 0.05)
        return base * self.detection_sensitivity

    def _get_landmark_point(self, landmarks: List[Dict], index: int) -> tuple:
        """
        landmark에서 좌표 추출

        Args:
            landmarks: landmark 리스트
            index: landmark 인덱스

        Returns:
            tuple: (x, y, z) 좌표
        """
        if not landmarks or index >= len(landmarks):
            return (0.0, 0.0, 0.0)

        lm = landmarks[index]
        if isinstance(lm, dict):
            return (lm.get('x', 0), lm.get('y', 0), lm.get('z', 0))
        else:
            return (getattr(lm, 'x', 0), getattr(lm, 'y', 0), getattr(lm, 'z', 0))

    def _calculate_angle_from_vertical(self, p1: tuple, p2: tuple) -> float:
        """
        두 점 사이의 수직선으로부터의 각도 계산

        Args:
            p1: 상단 점 (x, y)
            p2: 하단 점 (x, y)

        Returns:
            float: 각도 (도)
        """
        import math
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        if dy == 0:
            return 90.0

        angle = math.degrees(math.atan(abs(dx) / abs(dy)))
        return angle
