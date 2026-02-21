"""RULA (Rapid Upper Limb Assessment) 계산기"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
import math

from .base_assessment import BaseAssessment, AssessmentResult


@dataclass
class RULAResult(AssessmentResult):
    """RULA 평가 결과"""
    arm_wrist_score: int = 0  # A그룹 점수
    neck_trunk_score: int = 0  # B그룹 점수

    # 상세 점수 (합계)
    upper_arm_score: int = 0
    lower_arm_score: int = 0
    wrist_score: int = 0
    wrist_twist_score: int = 0
    neck_score: int = 0
    trunk_score: int = 0
    leg_score: int = 0

    # 상박 세부 점수
    upper_arm_base: int = 0           # 기본 점수 (1-4)
    upper_arm_shoulder_raised: int = 0  # 어깨 올림 (+1 or 0)
    upper_arm_abducted: int = 0       # 외전 (+1 or 0)
    upper_arm_supported: int = 0      # 팔 지지 (-1 or 0)

    # 하박 세부 점수
    lower_arm_base: int = 0           # 기본 점수 (1-2)
    lower_arm_working_across: int = 0  # 중앙선 교차 (+1 or 0)

    # 손목 세부 점수
    wrist_base: int = 0               # 기본 점수 (1-3)
    wrist_bent_midline: int = 0       # 중립에서 꺾임 (+1 or 0)

    # 목 세부 점수
    neck_base: int = 0                # 기본 점수 (1-4)
    neck_twisted: int = 0             # 회전 (+1 or 0)
    neck_side_bending: int = 0        # 측굴 (+1 or 0)

    # 몸통 세부 점수
    trunk_base: int = 0               # 기본 점수 (1-4)
    trunk_twisted: int = 0            # 회전 (+1 or 0)
    trunk_side_bending: int = 0       # 측굴 (+1 or 0)


class RULACalculator(BaseAssessment):
    """RULA 점수 계산기"""

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

    # RULA Table A: 상완/전완/손목 조합 → A그룹 점수
    # [upper_arm][lower_arm][wrist][wrist_twist]
    TABLE_A = [
        # Upper Arm 1
        [[[1, 2], [2, 2], [2, 3], [3, 3]],   # Lower Arm 1
         [[2, 2], [2, 2], [3, 3], [3, 3]],   # Lower Arm 2
         [[2, 3], [3, 3], [3, 3], [4, 4]]],  # Lower Arm 3
        # Upper Arm 2
        [[[2, 3], [3, 3], [3, 4], [4, 4]],
         [[3, 3], [3, 3], [3, 4], [4, 4]],
         [[3, 4], [4, 4], [4, 4], [5, 5]]],
        # Upper Arm 3
        [[[3, 3], [4, 4], [4, 4], [5, 5]],
         [[3, 4], [4, 4], [4, 4], [5, 5]],
         [[4, 4], [4, 4], [4, 5], [5, 5]]],
        # Upper Arm 4
        [[[4, 4], [4, 4], [4, 5], [5, 5]],
         [[4, 4], [4, 4], [4, 5], [5, 5]],
         [[4, 4], [4, 5], [5, 5], [6, 6]]],
        # Upper Arm 5
        [[[5, 5], [5, 5], [5, 6], [6, 7]],
         [[5, 6], [6, 6], [6, 7], [7, 7]],
         [[6, 6], [6, 7], [7, 7], [7, 8]]],
        # Upper Arm 6
        [[[7, 7], [7, 7], [7, 8], [8, 9]],
         [[8, 8], [8, 8], [8, 9], [9, 9]],
         [[9, 9], [9, 9], [9, 9], [9, 9]]],
    ]

    # RULA Table B: 목/몸통/다리 조합 → B그룹 점수
    # [neck][trunk][legs]
    TABLE_B = [
        # Neck 1
        [[1, 3], [2, 3], [3, 4], [5, 5], [6, 6], [7, 7]],
        # Neck 2
        [[2, 3], [2, 3], [4, 5], [5, 5], [6, 7], [7, 7]],
        # Neck 3
        [[3, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 7]],
        # Neck 4
        [[5, 5], [5, 6], [6, 7], [7, 7], [7, 7], [8, 8]],
        # Neck 5
        [[7, 7], [7, 7], [7, 8], [8, 8], [8, 8], [8, 8]],
        # Neck 6
        [[8, 8], [8, 8], [8, 8], [8, 9], [9, 9], [9, 9]],
    ]

    # RULA Table C: A그룹/B그룹 → 최종 점수
    TABLE_C = [
        [1, 2, 3, 3, 4, 5, 5],  # A=1
        [2, 2, 3, 4, 4, 5, 5],  # A=2
        [3, 3, 3, 4, 4, 5, 6],  # A=3
        [3, 3, 3, 4, 5, 6, 6],  # A=4
        [4, 4, 4, 5, 6, 7, 7],  # A=5
        [4, 4, 5, 6, 6, 7, 7],  # A=6
        [5, 5, 6, 6, 7, 7, 7],  # A=7
        [5, 5, 6, 7, 7, 7, 7],  # A=8
    ]

    RISK_LEVELS = {
        'acceptable': '개선 필요 없음',
        'investigate': '부분적 개선',
        'change_soon': '곧 개선 필요',
        'change_now': '즉시 개선',
    }

    ACTION_MESSAGES = {
        'acceptable': '개선 필요 없음',
        'investigate': '부분적 개선',
        'change_soon': '곧 개선 필요',
        'change_now': '즉시 개선',
    }

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> RULAResult:
        """RULA 점수 계산"""
        # 상세 점수 계산 (세부 점수 튜플 반환)
        upper_arm_details = self._calculate_upper_arm_score(angles, landmarks)
        lower_arm_details = self._calculate_lower_arm_score(angles)
        wrist_details = self._calculate_wrist_score(angles)
        wrist_twist = self._calculate_wrist_twist_score(angles)
        neck_details = self._calculate_neck_score(angles, landmarks)
        trunk_details = self._calculate_trunk_score(angles, landmarks)
        leg = self._calculate_leg_score(angles, landmarks)

        # 합계 점수 추출
        upper_arm = upper_arm_details['total']
        lower_arm = lower_arm_details['total']
        wrist = wrist_details['total']
        neck = neck_details['total']
        trunk = trunk_details['total']

        # Table A 점수 (A그룹)
        arm_wrist_score = self._get_table_a_score(upper_arm, lower_arm, wrist, wrist_twist)

        # Table B 점수 (B그룹)
        neck_trunk_score = self._get_table_b_score(neck, trunk, leg)

        # Table C 점수 (최종)
        final_score = self._get_table_c_score(arm_wrist_score, neck_trunk_score)

        # 위험 수준
        risk_level = self.get_risk_level(final_score)
        action_required = self.get_action_required(risk_level)

        return RULAResult(
            final_score=final_score,
            risk_level=risk_level,
            action_required=action_required,
            details={
                'upper_arm': upper_arm,
                'lower_arm': lower_arm,
                'wrist': wrist,
                'wrist_twist': wrist_twist,
                'neck': neck,
                'trunk': trunk,
                'leg': leg,
            },
            arm_wrist_score=arm_wrist_score,
            neck_trunk_score=neck_trunk_score,
            upper_arm_score=upper_arm,
            lower_arm_score=lower_arm,
            wrist_score=wrist,
            wrist_twist_score=wrist_twist,
            neck_score=neck,
            trunk_score=trunk,
            leg_score=leg,
            # 상박 세부 점수
            upper_arm_base=upper_arm_details['base'],
            upper_arm_shoulder_raised=upper_arm_details['shoulder_raised'],
            upper_arm_abducted=upper_arm_details['abducted'],
            upper_arm_supported=upper_arm_details['supported'],
            # 하박 세부 점수
            lower_arm_base=lower_arm_details['base'],
            lower_arm_working_across=lower_arm_details['working_across'],
            # 손목 세부 점수
            wrist_base=wrist_details['base'],
            wrist_bent_midline=wrist_details['bent_midline'],
            # 목 세부 점수
            neck_base=neck_details['base'],
            neck_twisted=neck_details['twisted'],
            neck_side_bending=neck_details['side_bending'],
            # 몸통 세부 점수
            trunk_base=trunk_details['base'],
            trunk_twisted=trunk_details['twisted'],
            trunk_side_bending=trunk_details['side_bending'],
        )

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
        elif flexion < -t1:  # 신전
            base = 2
        else:
            base = 1

        # 세부 가점/감점
        shoulder_raised = 0  # 어깨 올림: 현재 미구현 (추후 추가 가능)
        abducted = 0         # 외전
        supported = 0        # 팔 지지: 현재 미구현 (수동 입력 필요)

        # 외전 확인 (어깨가 옆으로 벌어졌는지)
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

    def _calculate_lower_arm_score(self, angles: Dict[str, float]) -> Dict[str, int]:
        """전완 점수 계산 (세부 점수 포함)"""
        # 팔꿈치 굴곡 (0°=펴짐, 90°=직각)
        flexion = angles.get('left_elbow_flexion', 90)

        # 기본 점수 (1-2) — RULA 기준: 60~100° 굴곡 → 1점
        low = self._get_threshold('elbow_flexion_low')
        high = self._get_threshold('elbow_flexion_high')
        if low <= flexion <= high:
            base = 1
        else:
            base = 2

        # 중앙선 교차 작업: 현재 미구현 (수동 입력 필요)
        working_across = 0

        total = min(base + working_across, 3)

        return {
            'base': base,
            'working_across': working_across,
            'total': total,
        }

    def _calculate_wrist_score(self, angles: Dict[str, float]) -> Dict[str, int]:
        """손목 점수 계산 (세부 점수 포함)"""
        # 손목 굴곡 (0°=중립, 검지/소지 중 최소값)
        flexion = angles.get('left_wrist_flexion', 0)

        # 기본 점수 (1-3)
        w1 = self._get_threshold('wrist_flexion_1')
        w2 = self._get_threshold('wrist_flexion_2')
        if flexion <= w1:
            base = 1
        elif flexion <= w2:
            base = 2
        else:
            base = 3

        # 중립에서 측면 꺾임: 현재 미구현 (수동 입력 필요)
        bent_midline = 0

        total = min(base + bent_midline, 4)

        return {
            'base': base,
            'bent_midline': bent_midline,
            'total': total,
        }

    def _calculate_wrist_twist_score(self, angles: Dict[str, float]) -> int:
        """손목 비틀림 점수 계산 (1-2)"""
        # 손목 회전은 직접 측정하기 어려움, 기본값 사용
        return 1

    def _calculate_neck_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> Dict[str, int]:
        """목 점수 계산 (세부 점수 포함)"""
        # 목 굴곡 (좌/우 몸통 기준 평균, 0°=직립)
        flexion = angles.get('neck_flexion', 0)

        # 기본 점수 (1-4)
        mid = self._get_threshold('neck_flexion_mid')
        high = self._get_threshold('neck_flexion_high')
        if flexion < 0:
            base = 4  # 신전 (뒤로 젖힘)
        elif flexion <= mid:
            base = 1
        elif flexion <= high:
            base = 2
        else:
            base = 3

        # 세부 가점
        twisted = 0       # 회전
        side_bending = 0  # 측굴

        # 회전 판단 (귀 중심점과 어깨중심의 x좌표 차이)
        if landmarks:
            left_ear = self._get_landmark_point(landmarks, 7)
            right_ear = self._get_landmark_point(landmarks, 8)
            left_shoulder = self._get_landmark_point(landmarks, self.LEFT_SHOULDER)
            right_shoulder = self._get_landmark_point(landmarks, self.RIGHT_SHOULDER)
            ear_center_x = (left_ear[0] + right_ear[0]) / 2
            shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            if abs(ear_center_x - shoulder_center_x) > self._get_threshold('neck_twisted'):
                twisted = 1

        total = min(base + twisted + side_bending, 6)

        return {
            'base': base,
            'twisted': twisted,
            'side_bending': side_bending,
            'total': total,
        }

    def _calculate_trunk_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> Dict[str, int]:
        """몸통 점수 계산 (세부 점수 포함)"""
        if not landmarks:
            return {
                'base': 1,
                'twisted': 0,
                'side_bending': 0,
                'total': 1,
            }

        # 어깨 중심과 골반 중심으로 몸통 각도 계산
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

        # 수직선으로부터의 각도
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

        # 세부 가점
        twisted = 0       # 회전
        side_bending = 0  # 측굴

        # 측굴 확인
        if abs(left_shoulder[1] - right_shoulder[1]) > self._get_threshold('trunk_side_bending'):
            side_bending = 1

        total = min(base + twisted + side_bending, 6)

        return {
            'base': base,
            'twisted': twisted,
            'side_bending': side_bending,
            'total': total,
        }

    def _calculate_leg_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """다리 점수 계산 (1-2)"""
        # 무릎 굴곡 (2D, 0°=펴짐)
        left_knee_flexion = angles.get('left_knee_flexion', 0)
        right_knee_flexion = angles.get('right_knee_flexion', 0)

        # 양다리가 균형 잡혀 있고 서 있으면 1
        leg_thresh = self._get_threshold('leg_flexion')
        if left_knee_flexion <= leg_thresh and right_knee_flexion <= leg_thresh:
            return 1
        else:
            return 2

    def _get_table_a_score(self, upper_arm: int, lower_arm: int, wrist: int, wrist_twist: int) -> int:
        """Table A에서 A그룹 점수 조회"""
        ua = min(max(upper_arm - 1, 0), 5)
        la = min(max(lower_arm - 1, 0), 2)
        w = min(max(wrist - 1, 0), 3)
        wt = min(max(wrist_twist - 1, 0), 1)

        try:
            return self.TABLE_A[ua][la][w][wt]
        except IndexError:
            return 1

    def _get_table_b_score(self, neck: int, trunk: int, leg: int) -> int:
        """Table B에서 B그룹 점수 조회"""
        n = min(max(neck - 1, 0), 5)
        t = min(max(trunk - 1, 0), 5)
        l = min(max(leg - 1, 0), 1)

        try:
            return self.TABLE_B[n][t][l]
        except IndexError:
            return 1

    def _get_table_c_score(self, a_score: int, b_score: int) -> int:
        """Table C에서 최종 점수 조회"""
        a = min(max(a_score - 1, 0), 7)
        b = min(max(b_score - 1, 0), 6)

        try:
            return self.TABLE_C[a][b]
        except IndexError:
            return 1

    def get_risk_level(self, score: int) -> str:
        """점수에 따른 위험 수준 반환"""
        if score <= 2:
            return 'acceptable'
        elif score <= 4:
            return 'investigate'
        elif score <= 6:
            return 'change_soon'
        else:
            return 'change_now'

    def get_action_required(self, risk_level: str) -> str:
        """위험 수준에 따른 조치 사항 반환"""
        return self.ACTION_MESSAGES.get(risk_level, '')
