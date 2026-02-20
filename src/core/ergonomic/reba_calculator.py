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

    # 상세 점수 (합계)
    neck_score: int = 0
    trunk_score: int = 0
    leg_score: int = 0
    upper_arm_score: int = 0
    lower_arm_score: int = 0
    wrist_score: int = 0

    # 목 세부 점수
    neck_base: int = 0                # 기본 점수 (1-2)
    neck_twist_side: int = 0          # 회전/측굴 (+1 or 0)

    # 몸통 세부 점수
    trunk_base: int = 0               # 기본 점수 (1-4)
    trunk_twist_side: int = 0         # 회전/측굴 (+1 or 0)

    # 다리 세부 점수
    leg_base: int = 0                 # 기본 점수 (1-2)
    leg_knee_30_60: int = 0           # 무릎 30-60° (+1 or 0)
    leg_knee_over_60: int = 0         # 무릎 60°+ (+2 or 0)

    # 상완 세부 점수
    upper_arm_base: int = 0           # 기본 점수 (1-4)
    upper_arm_shoulder_raised: int = 0  # 어깨 올림 (+1 or 0)
    upper_arm_abducted: int = 0       # 외전 (+1 or 0)
    upper_arm_supported: int = 0      # 팔 지지 (-1 or 0)

    # 손목 세부 점수
    wrist_base: int = 0               # 기본 점수 (1-2)
    wrist_twisted: int = 0            # 비틀림 (+1 or 0)


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
    # [upper_arm 1-6][lower_arm 1-2][wrist 1-3]
    TABLE_B = [
        # Upper Arm 1
        [[1, 2, 2], [1, 2, 3]],
        # Upper Arm 2
        [[1, 2, 3], [2, 3, 4]],
        # Upper Arm 3
        [[3, 4, 5], [4, 5, 5]],
        # Upper Arm 4
        [[4, 5, 5], [5, 6, 7]],
        # Upper Arm 5
        [[6, 7, 8], [7, 8, 8]],
        # Upper Arm 6
        [[7, 8, 8], [8, 9, 9]],
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
        'negligible': '개선 필요 없음',
        'low': '부분적 개선',
        'medium': '개선 필요',
        'high': '곧 개선 필요',
        'very_high': '즉시 개선',
    }

    ACTION_MESSAGES = {
        'negligible': '개선 필요 없음',
        'low': '부분적 개선',
        'medium': '개선 필요',
        'high': '곧 개선 필요',
        'very_high': '즉시 개선',
    }

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> REBAResult:
        """REBA 점수 계산"""
        # A그룹 점수 계산 (목/몸통/다리) - 세부 점수 포함
        neck_details = self._calculate_neck_score(angles, landmarks)
        trunk_details = self._calculate_trunk_score(angles, landmarks)
        leg_details = self._calculate_leg_score(angles, landmarks)

        # B그룹 점수 계산 (상완/전완/손목) - 세부 점수 포함
        upper_arm_details = self._calculate_upper_arm_score(angles, landmarks)
        lower_arm = self._calculate_lower_arm_score(angles)
        wrist_details = self._calculate_wrist_score(angles)

        # 합계 점수 추출
        neck = neck_details['total']
        trunk = trunk_details['total']
        leg = leg_details['total']
        upper_arm = upper_arm_details['total']
        wrist = wrist_details['total']

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
            # 목 세부 점수
            neck_base=neck_details['base'],
            neck_twist_side=neck_details['twist_side'],
            # 몸통 세부 점수
            trunk_base=trunk_details['base'],
            trunk_twist_side=trunk_details['twist_side'],
            # 다리 세부 점수
            leg_base=leg_details['base'],
            leg_knee_30_60=leg_details['knee_30_60'],
            leg_knee_over_60=leg_details['knee_over_60'],
            # 상완 세부 점수
            upper_arm_base=upper_arm_details['base'],
            upper_arm_shoulder_raised=upper_arm_details['shoulder_raised'],
            upper_arm_abducted=upper_arm_details['abducted'],
            upper_arm_supported=upper_arm_details['supported'],
            # 손목 세부 점수
            wrist_base=wrist_details['base'],
            wrist_twisted=wrist_details['twisted'],
        )

    def _calculate_neck_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> Dict[str, int]:
        """목 점수 계산 (세부 점수 포함)"""
        # 목 굴곡 (좌/우 몸통 기준 평균, 0°=직립)
        flexion = angles.get('neck_flexion', 0)

        # 기본 점수 (1-2)
        high = self._get_threshold('neck_flexion_high')
        if 0 <= flexion <= high:
            base = 1
        else:
            base = 2

        # 회전/측굴 (REBA에서는 합쳐서 처리)
        twist_side = 0
        if landmarks:
            left_ear = self._get_landmark_point(landmarks, 7)
            right_ear = self._get_landmark_point(landmarks, 8)
            left_shoulder = self._get_landmark_point(landmarks, self.LEFT_SHOULDER)
            right_shoulder = self._get_landmark_point(landmarks, self.RIGHT_SHOULDER)
            ear_center_x = (left_ear[0] + right_ear[0]) / 2
            shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            if abs(ear_center_x - shoulder_center_x) > self._get_threshold('neck_twisted'):
                twist_side = 1

        total = min(base + twist_side, 3)

        return {
            'base': base,
            'twist_side': twist_side,
            'total': total,
        }

    def _calculate_trunk_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> Dict[str, int]:
        """몸통 점수 계산 (세부 점수 포함)"""
        if not landmarks:
            return {
                'base': 1,
                'twist_side': 0,
                'total': 1,
            }

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

        # 기본 점수 (1-4)
        tt1 = self._get_threshold('trunk_flexion_1')
        tt2 = self._get_threshold('trunk_flexion_2')
        tt3 = self._get_threshold('trunk_flexion_3')
        if flexion <= tt1:
            base = 1
        elif flexion <= tt2:
            base = 2
        elif flexion <= tt3:
            base = 3
        else:
            base = 4

        # 회전/측굴 (REBA에서는 합쳐서 처리)
        twist_side = 0
        if abs(left_shoulder[1] - right_shoulder[1]) > self._get_threshold('trunk_side_bending'):
            twist_side = 1

        total = min(base + twist_side, 5)

        return {
            'base': base,
            'twist_side': twist_side,
            'total': total,
        }

    def _calculate_leg_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> Dict[str, int]:
        """다리 점수 계산 (세부 점수 포함)"""
        # 무릎 굴곡 (2D, 0°=펴짐)
        left_knee_flexion = angles.get('left_knee_flexion', 0)
        right_knee_flexion = angles.get('right_knee_flexion', 0)

        # 기본 점수: 양다리 지지 = 1, 한다리 지지 = 2
        base = 1

        # 무릎 굴곡 세부 점수
        knee_30_60 = 0
        knee_over_60 = 0

        knee_flexion = max(left_knee_flexion, right_knee_flexion)

        lk_mid = self._get_threshold('leg_knee_mid')
        lk_high = self._get_threshold('leg_knee_high')
        if knee_flexion > lk_mid and knee_flexion <= lk_high:
            knee_30_60 = 1
        elif knee_flexion > lk_high:
            knee_over_60 = 2

        total = min(base + knee_30_60 + knee_over_60, 4)

        return {
            'base': base,
            'knee_30_60': knee_30_60,
            'knee_over_60': knee_over_60,
            'total': total,
        }

    def _calculate_upper_arm_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> Dict[str, int]:
        """상완 점수 계산 (세부 점수 포함)"""
        # 어깨 각도(팔꿈치-어깨-엉덩이) 자체가 팔 거상각에 대응
        # 팔 내림 ≈ 0-20°, 수평 ≈ 90°, 머리 위 ≈ 170°+
        shoulder_angle = angles.get('left_shoulder', 90)
        flexion = shoulder_angle

        # 기본 점수 (1-4)
        t1 = self._get_threshold('upper_arm_flexion_1')
        t2 = self._get_threshold('upper_arm_flexion_2')
        t3 = self._get_threshold('upper_arm_flexion_3')
        if -t1 <= flexion <= t1:
            base = 1
        elif flexion > t1 and flexion <= t2:
            base = 2
        elif flexion > t2 and flexion <= t3:
            base = 3
        elif flexion > t3:
            base = 4
        else:
            base = 2

        # 세부 가점/감점
        shoulder_raised = 0  # 어깨 올림: 현재 미구현
        abducted = 0         # 외전
        supported = 0        # 팔 지지: 현재 미구현

        # 외전 확인
        if landmarks:
            left_shoulder = self._get_landmark_point(landmarks, self.LEFT_SHOULDER)
            left_elbow = self._get_landmark_point(landmarks, self.LEFT_ELBOW)

            if left_elbow[0] < left_shoulder[0] - self._get_threshold('upper_arm_abducted'):
                abducted = 1

        total = min(base + shoulder_raised + abducted + supported, 6)

        return {
            'base': base,
            'shoulder_raised': shoulder_raised,
            'abducted': abducted,
            'supported': supported,
            'total': total,
        }

    def _calculate_lower_arm_score(self, angles: Dict[str, float]) -> int:
        """전완 점수 계산 (1-2)"""
        # 팔꿈치 굴곡 (0°=펴짐, 90°=직각)
        flexion = angles.get('left_elbow_flexion', 90)

        # REBA 기준: 60~100° 굴곡 → 1점
        low = self._get_threshold('elbow_flexion_low')
        high = self._get_threshold('elbow_flexion_high')
        if low <= flexion <= high:
            return 1
        else:
            return 2

    def _calculate_wrist_score(self, angles: Dict[str, float]) -> Dict[str, int]:
        """손목 점수 계산 (세부 점수 포함)"""
        # 손목 굴곡 (0°=중립, 검지/소지 중 최소값)
        flexion = angles.get('left_wrist_flexion', 0)

        # 기본 점수 (1-2) — REBA 기준: 15° 이내 → 1점
        w2 = self._get_threshold('wrist_flexion_2')
        if flexion <= w2:
            base = 1
        else:
            base = 2

        # 비틀림: 현재 미구현 (수동 입력 필요)
        twisted = 0

        total = min(base + twisted, 3)

        return {
            'base': base,
            'twisted': twisted,
            'total': total,
        }

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
        la = min(max(lower_arm - 1, 0), 1)
        w = min(max(wrist - 1, 0), 2)

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
