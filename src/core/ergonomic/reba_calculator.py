"""REBA (Rapid Entire Body Assessment) 계산기"""

from dataclasses import dataclass
from typing import Dict, List, Any
import math

from .base_assessment import BaseAssessment, AssessmentResult


@dataclass
class REBAResult(AssessmentResult):
    """REBA 평가 결과"""
    group_a_score: int = 0  # A그룹 점수 (목/몸통/다리)
    group_b_score: int = 0  # B그룹 점수 (상완/전완/손목)

    # 상세 점수
    neck_score: int = 0
    trunk_score: int = 0
    leg_score: int = 0
    upper_arm_score: int = 0
    lower_arm_score: int = 0
    wrist_score: int = 0


class REBACalculator(BaseAssessment):
    """REBA 점수 계산기"""

    # MediaPipe landmark 인덱스
    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    # REBA Table A: 목/몸통/다리 조합
    # [neck][trunk][legs]
    TABLE_A = [
        # Neck 1
        [[1, 2, 3, 4], [2, 3, 4, 5], [2, 4, 5, 6], [3, 5, 6, 7], [4, 6, 7, 8]],
        # Neck 2
        [[1, 2, 3, 4], [3, 4, 5, 6], [4, 5, 6, 7], [5, 6, 7, 8], [6, 7, 8, 9]],
        # Neck 3
        [[3, 3, 5, 6], [4, 5, 6, 7], [5, 6, 7, 8], [6, 7, 8, 9], [7, 8, 9, 9]],
    ]

    # REBA Table B: 상완/전완/손목 조합
    # [upper_arm][lower_arm][wrist]
    TABLE_B = [
        # Upper Arm 1
        [[1, 2], [1, 2], [3, 4]],
        # Upper Arm 2
        [[1, 2], [2, 3], [4, 5]],
        # Upper Arm 3
        [[3, 4], [4, 5], [5, 6]],
        # Upper Arm 4
        [[4, 5], [5, 6], [7, 8]],
        # Upper Arm 5
        [[6, 7], [7, 8], [8, 9]],
        # Upper Arm 6
        [[7, 8], [8, 9], [9, 9]],
    ]

    # REBA Table C: A그룹/B그룹 → 최종 점수
    TABLE_C = [
        [1, 1, 1, 2, 3, 3, 4, 5, 6, 7, 7, 7],   # A=1
        [1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],   # A=2
        [2, 3, 3, 3, 4, 5, 6, 7, 7, 8, 8, 8],   # A=3
        [3, 4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9],   # A=4
        [4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9, 9],   # A=5
        [6, 6, 6, 7, 8, 8, 9, 9, 10, 10, 10, 10],  # A=6
        [7, 7, 7, 8, 9, 9, 9, 10, 10, 11, 11, 11],  # A=7
        [8, 8, 8, 9, 10, 10, 10, 10, 10, 11, 11, 11],  # A=8
        [9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12, 12],  # A=9
        [10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12],  # A=10
        [11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12],  # A=11
        [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12],  # A=12
    ]

    RISK_LEVELS = {
        'negligible': '무시 가능',
        'low': '낮음',
        'medium': '중간',
        'high': '높음',
        'very_high': '매우 높음',
    }

    ACTION_MESSAGES = {
        'negligible': '조치 불필요',
        'low': '개선 고려',
        'medium': '개선 필요',
        'high': '빠른 개선 필요',
        'very_high': '즉시 개선 필요',
    }

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> REBAResult:
        """REBA 점수 계산"""
        # A그룹 점수 계산 (목/몸통/다리)
        neck = self._calculate_neck_score(angles, landmarks)
        trunk = self._calculate_trunk_score(angles, landmarks)
        leg = self._calculate_leg_score(angles, landmarks)

        # B그룹 점수 계산 (상완/전완/손목)
        upper_arm = self._calculate_upper_arm_score(angles, landmarks)
        lower_arm = self._calculate_lower_arm_score(angles)
        wrist = self._calculate_wrist_score(angles)

        # Table A 점수
        group_a_score = self._get_table_a_score(neck, trunk, leg)

        # Table B 점수
        group_b_score = self._get_table_b_score(upper_arm, lower_arm, wrist)

        # Table C 점수 (최종)
        final_score = self._get_table_c_score(group_a_score, group_b_score)

        # 위험 수준
        risk_level = self.get_risk_level(final_score)
        action_required = self.get_action_required(risk_level)

        return REBAResult(
            final_score=final_score,
            risk_level=risk_level,
            action_required=action_required,
            details={
                'neck': neck,
                'trunk': trunk,
                'leg': leg,
                'upper_arm': upper_arm,
                'lower_arm': lower_arm,
                'wrist': wrist,
            },
            group_a_score=group_a_score,
            group_b_score=group_b_score,
            neck_score=neck,
            trunk_score=trunk,
            leg_score=leg,
            upper_arm_score=upper_arm,
            lower_arm_score=lower_arm,
            wrist_score=wrist,
        )

    def _calculate_neck_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """목 점수 계산 (1-3)"""
        neck_angle = angles.get('neck', 180)
        flexion = 180 - neck_angle

        if 0 <= flexion <= 20:
            score = 1
        else:
            score = 2

        # 측굴/회전 시 +1
        if landmarks:
            nose = self._get_landmark_point(landmarks, self.NOSE)
            left_shoulder = self._get_landmark_point(landmarks, self.LEFT_SHOULDER)
            right_shoulder = self._get_landmark_point(landmarks, self.RIGHT_SHOULDER)

            shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            if abs(nose[0] - shoulder_center_x) > 0.05:
                score += 1

        return min(score, 3)

    def _calculate_trunk_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """몸통 점수 계산 (1-5)"""
        if not landmarks:
            return 1

        left_shoulder = self._get_landmark_point(landmarks, self.LEFT_SHOULDER)
        right_shoulder = self._get_landmark_point(landmarks, self.RIGHT_SHOULDER)
        left_hip = self._get_landmark_point(landmarks, self.LEFT_HIP)
        right_hip = self._get_landmark_point(landmarks, self.RIGHT_HIP)

        shoulder_center = (
            (left_shoulder[0] + right_shoulder[0]) / 2,
            (left_shoulder[1] + right_shoulder[1]) / 2,
        )
        hip_center = (
            (left_hip[0] + right_hip[0]) / 2,
            (left_hip[1] + right_hip[1]) / 2,
        )

        flexion = self._calculate_angle_from_vertical(shoulder_center, hip_center)

        if flexion <= 5:
            score = 1
        elif flexion <= 20:
            score = 2
        elif flexion <= 60:
            score = 3
        else:
            score = 4

        # 측굴/회전 시 +1
        if abs(left_shoulder[1] - right_shoulder[1]) > 0.03:
            score += 1

        return min(score, 5)

    def _calculate_leg_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """다리 점수 계산 (1-4)"""
        left_knee_angle = angles.get('left_knee', 180)
        right_knee_angle = angles.get('right_knee', 180)

        # 기본 점수: 양다리 지지 = 1, 한다리 지지 = 2
        score = 1

        # 무릎 굴곡 확인
        min_knee = min(left_knee_angle, right_knee_angle)
        knee_flexion = 180 - min_knee

        if knee_flexion > 30 and knee_flexion <= 60:
            score += 1
        elif knee_flexion > 60:
            score += 2

        return min(score, 4)

    def _calculate_upper_arm_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """상완 점수 계산 (1-6)"""
        shoulder_angle = angles.get('left_shoulder', 90)
        flexion = 180 - shoulder_angle

        if flexion >= -20 and flexion <= 20:
            score = 1
        elif flexion > 20 and flexion <= 45:
            score = 2
        elif flexion > 45 and flexion <= 90:
            score = 3
        elif flexion > 90:
            score = 4
        else:
            score = 2

        # 외전/어깨 올림 시 +1
        if landmarks:
            left_shoulder = self._get_landmark_point(landmarks, self.LEFT_SHOULDER)
            left_elbow = self._get_landmark_point(landmarks, self.LEFT_ELBOW)

            if left_elbow[0] < left_shoulder[0] - 0.08:
                score += 1

        return min(score, 6)

    def _calculate_lower_arm_score(self, angles: Dict[str, float]) -> int:
        """전완 점수 계산 (1-2)"""
        elbow_angle = angles.get('left_elbow', 90)

        if 60 <= elbow_angle <= 100:
            return 1
        else:
            return 2

    def _calculate_wrist_score(self, angles: Dict[str, float]) -> int:
        """손목 점수 계산 (1-3)"""
        wrist_angle = angles.get('left_wrist', 180)
        deviation = abs(180 - wrist_angle)

        if deviation <= 15:
            score = 1
        else:
            score = 2

        return min(score, 3)

    def _get_table_a_score(self, neck: int, trunk: int, leg: int) -> int:
        """Table A에서 A그룹 점수 조회"""
        n = min(max(neck - 1, 0), 2)
        t = min(max(trunk - 1, 0), 4)
        l = min(max(leg - 1, 0), 3)

        try:
            return self.TABLE_A[n][t][l]
        except IndexError:
            return 1

    def _get_table_b_score(self, upper_arm: int, lower_arm: int, wrist: int) -> int:
        """Table B에서 B그룹 점수 조회"""
        ua = min(max(upper_arm - 1, 0), 5)
        la = min(max(lower_arm - 1, 0), 2)
        w = min(max(wrist - 1, 0), 1)

        try:
            return self.TABLE_B[ua][la][w]
        except IndexError:
            return 1

    def _get_table_c_score(self, a_score: int, b_score: int) -> int:
        """Table C에서 최종 점수 조회"""
        a = min(max(a_score - 1, 0), 11)
        b = min(max(b_score - 1, 0), 11)

        try:
            return self.TABLE_C[a][b]
        except IndexError:
            return 1

    def get_risk_level(self, score: int) -> str:
        """점수에 따른 위험 수준 반환"""
        if score == 1:
            return 'negligible'
        elif score <= 3:
            return 'low'
        elif score <= 7:
            return 'medium'
        elif score <= 10:
            return 'high'
        else:
            return 'very_high'

    def get_action_required(self, risk_level: str) -> str:
        """위험 수준에 따른 조치 사항 반환"""
        return self.ACTION_MESSAGES.get(risk_level, '')
