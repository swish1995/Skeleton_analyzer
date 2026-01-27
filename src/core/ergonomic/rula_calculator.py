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

    # 상세 점수
    upper_arm_score: int = 0
    lower_arm_score: int = 0
    wrist_score: int = 0
    wrist_twist_score: int = 0
    neck_score: int = 0
    trunk_score: int = 0
    leg_score: int = 0


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
        'acceptable': '허용 가능',
        'investigate': '추가 조사 필요',
        'change_soon': '빠른 개선 필요',
        'change_now': '즉시 개선 필요',
    }

    ACTION_MESSAGES = {
        'acceptable': '현재 자세는 허용 가능한 수준입니다.',
        'investigate': '작업 자세에 대한 추가 조사가 필요합니다.',
        'change_soon': '가까운 시일 내에 작업 자세 개선이 필요합니다.',
        'change_now': '즉시 작업 자세를 변경해야 합니다.',
    }

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> RULAResult:
        """RULA 점수 계산"""
        # 상세 점수 계산
        upper_arm = self._calculate_upper_arm_score(angles, landmarks)
        lower_arm = self._calculate_lower_arm_score(angles)
        wrist = self._calculate_wrist_score(angles)
        wrist_twist = self._calculate_wrist_twist_score(angles)
        neck = self._calculate_neck_score(angles, landmarks)
        trunk = self._calculate_trunk_score(angles, landmarks)
        leg = self._calculate_leg_score(angles, landmarks)

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
        )

    def _calculate_upper_arm_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """상완 점수 계산 (1-6)"""
        # 어깨 각도 사용 (굴곡/신전)
        shoulder_angle = angles.get('left_shoulder', 90)
        # 180도에서 빼서 굴곡 각도로 변환
        flexion = 180 - shoulder_angle

        if flexion <= 20 and flexion >= -20:
            score = 1
        elif flexion > 20 and flexion <= 45:
            score = 2
        elif flexion > 45 and flexion <= 90:
            score = 3
        elif flexion > 90:
            score = 4
        elif flexion < -20:  # 신전
            score = 2
        else:
            score = 1

        # 외전 확인 (어깨가 옆으로 벌어졌는지)
        if landmarks:
            left_shoulder = self._get_landmark_point(landmarks, self.LEFT_SHOULDER)
            left_elbow = self._get_landmark_point(landmarks, self.LEFT_ELBOW)
            left_hip = self._get_landmark_point(landmarks, self.LEFT_HIP)

            # 팔꿈치가 어깨보다 바깥쪽이면 외전
            if left_elbow[0] < left_shoulder[0] - 0.05:  # x좌표 비교 (왼쪽)
                score += 1

        return min(score, 6)

    def _calculate_lower_arm_score(self, angles: Dict[str, float]) -> int:
        """전완 점수 계산 (1-3)"""
        elbow_angle = angles.get('left_elbow', 90)

        if 60 <= elbow_angle <= 100:
            score = 1
        else:
            score = 2

        return min(score, 3)

    def _calculate_wrist_score(self, angles: Dict[str, float]) -> int:
        """손목 점수 계산 (1-4)"""
        wrist_angle = angles.get('left_wrist', 180)
        # 중립(180도)에서 벗어난 정도
        deviation = abs(180 - wrist_angle)

        if deviation <= 5:
            score = 1
        elif deviation <= 15:
            score = 2
        else:
            score = 3

        return min(score, 4)

    def _calculate_wrist_twist_score(self, angles: Dict[str, float]) -> int:
        """손목 비틀림 점수 계산 (1-2)"""
        # 손목 회전은 직접 측정하기 어려움, 기본값 사용
        return 1

    def _calculate_neck_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """목 점수 계산 (1-6)"""
        neck_angle = angles.get('neck', 180)

        # neck_angle은 어깨-코-어깨 각도이므로 굴곡으로 변환
        # 180도가 직립, 작을수록 굴곡
        flexion = 180 - neck_angle

        if 0 <= flexion <= 10:
            score = 1
        elif 10 < flexion <= 20:
            score = 2
        elif flexion > 20:
            score = 3
        elif flexion < 0:  # 신전
            score = 4
        else:
            score = 1

        # 측굴/회전 확인
        if landmarks:
            nose = self._get_landmark_point(landmarks, self.NOSE)
            left_shoulder = self._get_landmark_point(landmarks, self.LEFT_SHOULDER)
            right_shoulder = self._get_landmark_point(landmarks, self.RIGHT_SHOULDER)

            # 어깨 중심과 코의 x좌표 차이로 측굴/회전 판단
            shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            if abs(nose[0] - shoulder_center_x) > 0.05:
                score += 1

        return min(score, 6)

    def _calculate_trunk_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """몸통 점수 계산 (1-6)"""
        if not landmarks:
            return 1

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

        if flexion <= 5:
            score = 1
        elif flexion <= 20:
            score = 2
        elif flexion <= 60:
            score = 3
        else:
            score = 4

        # 측굴 확인
        if abs(left_shoulder[1] - right_shoulder[1]) > 0.03:
            score += 1

        return min(score, 6)

    def _calculate_leg_score(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """다리 점수 계산 (1-2)"""
        if not landmarks:
            return 1

        left_knee_angle = angles.get('left_knee', 180)
        right_knee_angle = angles.get('right_knee', 180)

        # 양다리가 균형 잡혀 있고 서 있으면 1
        # 한 다리에 체중이 실리거나 앉아있으면 2
        if left_knee_angle > 160 and right_knee_angle > 160:
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
