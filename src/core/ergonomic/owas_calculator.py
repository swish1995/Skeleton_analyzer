"""OWAS (Ovako Working Posture Analysis System) 계산기"""

from dataclasses import dataclass
from typing import Dict, List, Any
import math

from .base_assessment import BaseAssessment, AssessmentResult


@dataclass
class OWASResult(AssessmentResult):
    """OWAS 평가 결과"""
    back_code: int = 1      # 등 코드 (1-4)
    arms_code: int = 1      # 팔 코드 (1-3)
    legs_code: int = 1      # 다리 코드 (1-7)
    load_code: int = 1      # 하중 코드 (1-3)
    action_category: int = 1  # 조치 카테고리 (1-4)
    posture_code: str = "1111"  # 4자리 자세 코드


class OWASCalculator(BaseAssessment):
    """OWAS 점수 계산기"""

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

    # OWAS 조치 카테고리 테이블
    # [back][arms][legs] → AC
    ACTION_CATEGORY_TABLE = {
        # Back 1 (직립)
        (1, 1, 1): 1, (1, 1, 2): 1, (1, 1, 3): 1, (1, 1, 4): 1, (1, 1, 5): 1, (1, 1, 6): 1, (1, 1, 7): 1,
        (1, 2, 1): 1, (1, 2, 2): 1, (1, 2, 3): 1, (1, 2, 4): 1, (1, 2, 5): 1, (1, 2, 6): 1, (1, 2, 7): 1,
        (1, 3, 1): 1, (1, 3, 2): 1, (1, 3, 3): 1, (1, 3, 4): 1, (1, 3, 5): 1, (1, 3, 6): 1, (1, 3, 7): 1,
        # Back 2 (굴곡)
        (2, 1, 1): 2, (2, 1, 2): 2, (2, 1, 3): 2, (2, 1, 4): 2, (2, 1, 5): 2, (2, 1, 6): 2, (2, 1, 7): 2,
        (2, 2, 1): 2, (2, 2, 2): 2, (2, 2, 3): 2, (2, 2, 4): 2, (2, 2, 5): 2, (2, 2, 6): 2, (2, 2, 7): 2,
        (2, 3, 1): 2, (2, 3, 2): 2, (2, 3, 3): 2, (2, 3, 4): 2, (2, 3, 5): 2, (2, 3, 6): 3, (2, 3, 7): 3,
        # Back 3 (회전)
        (3, 1, 1): 1, (3, 1, 2): 1, (3, 1, 3): 1, (3, 1, 4): 1, (3, 1, 5): 1, (3, 1, 6): 2, (3, 1, 7): 2,
        (3, 2, 1): 2, (3, 2, 2): 2, (3, 2, 3): 2, (3, 2, 4): 2, (3, 2, 5): 2, (3, 2, 6): 2, (3, 2, 7): 2,
        (3, 3, 1): 2, (3, 3, 2): 2, (3, 3, 3): 3, (3, 3, 4): 3, (3, 3, 5): 3, (3, 3, 6): 3, (3, 3, 7): 3,
        # Back 4 (굴곡+회전)
        (4, 1, 1): 2, (4, 1, 2): 2, (4, 1, 3): 3, (4, 1, 4): 3, (4, 1, 5): 3, (4, 1, 6): 3, (4, 1, 7): 3,
        (4, 2, 1): 3, (4, 2, 2): 3, (4, 2, 3): 3, (4, 2, 4): 3, (4, 2, 5): 3, (4, 2, 6): 3, (4, 2, 7): 3,
        (4, 3, 1): 3, (4, 3, 2): 3, (4, 3, 3): 4, (4, 3, 4): 4, (4, 3, 5): 4, (4, 3, 6): 4, (4, 3, 7): 4,
    }

    RISK_LEVELS = {
        'normal': '정상',
        'slight': '약간 유해',
        'harmful': '명백히 유해',
        'very_harmful': '매우 유해',
    }

    ACTION_MESSAGES = {
        'normal': '조치 불필요 - 정상적인 작업 자세',
        'slight': '가까운 시일 내 개선 필요',
        'harmful': '가능한 빨리 개선 필요',
        'very_harmful': '즉시 개선 필요',
    }

    AC_DESCRIPTIONS = {
        1: 'AC1: 정상 자세 - 조치 불필요',
        2: 'AC2: 약간 유해 - 가까운 시일 내 개선',
        3: 'AC3: 명백히 유해 - 가능한 빨리 개선',
        4: 'AC4: 매우 유해 - 즉시 개선',
    }

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> OWASResult:
        """OWAS 점수 계산"""
        # 각 부위 코드 계산
        back_code = self._calculate_back_code(angles, landmarks)
        arms_code = self._calculate_arms_code(angles, landmarks)
        legs_code = self._calculate_legs_code(angles, landmarks)
        load_code = 1  # 기본값 (하중 정보 없음)

        # 자세 코드 생성
        posture_code = f"{back_code}{arms_code}{legs_code}{load_code}"

        # 조치 카테고리 결정
        action_category = self._get_action_category(back_code, arms_code, legs_code)

        # 위험 수준
        risk_level = self.get_risk_level(action_category)
        action_required = self.get_action_required(risk_level)

        return OWASResult(
            final_score=action_category,
            risk_level=risk_level,
            action_required=action_required,
            details={
                'back': back_code,
                'arms': arms_code,
                'legs': legs_code,
                'load': load_code,
                'posture_code': posture_code,
                'ac_description': self.AC_DESCRIPTIONS.get(action_category, ''),
            },
            back_code=back_code,
            arms_code=arms_code,
            legs_code=legs_code,
            load_code=load_code,
            action_category=action_category,
            posture_code=posture_code,
        )

    def _calculate_back_code(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """
        등 코드 계산 (1-4)
        1: 직립
        2: 굴곡
        3: 회전/측굴
        4: 굴곡 + 회전/측굴
        """
        if not landmarks:
            return 1

        # 몸통 굴곡 계산
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
        is_bent = flexion > 20

        # 회전/측굴 확인
        shoulder_diff = abs(left_shoulder[1] - right_shoulder[1])
        hip_diff = abs(left_hip[1] - right_hip[1])
        is_twisted = shoulder_diff > 0.04 or hip_diff > 0.04

        if is_bent and is_twisted:
            return 4
        elif is_twisted:
            return 3
        elif is_bent:
            return 2
        else:
            return 1

    def _calculate_arms_code(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """
        팔 코드 계산 (1-3)
        1: 양팔 어깨 아래
        2: 한 팔 어깨 위
        3: 양팔 어깨 위
        """
        if not landmarks:
            return 1

        left_shoulder = self._get_landmark_point(landmarks, self.LEFT_SHOULDER)
        right_shoulder = self._get_landmark_point(landmarks, self.RIGHT_SHOULDER)
        left_elbow = self._get_landmark_point(landmarks, self.LEFT_ELBOW)
        right_elbow = self._get_landmark_point(landmarks, self.RIGHT_ELBOW)
        left_wrist = self._get_landmark_point(landmarks, self.LEFT_WRIST)
        right_wrist = self._get_landmark_point(landmarks, self.RIGHT_WRIST)

        # 손목이 어깨보다 위에 있는지 확인 (y좌표가 작을수록 위)
        left_raised = left_wrist[1] < left_shoulder[1] or left_elbow[1] < left_shoulder[1]
        right_raised = right_wrist[1] < right_shoulder[1] or right_elbow[1] < right_shoulder[1]

        if left_raised and right_raised:
            return 3
        elif left_raised or right_raised:
            return 2
        else:
            return 1

    def _calculate_legs_code(self, angles: Dict[str, float], landmarks: List[Dict]) -> int:
        """
        다리 코드 계산 (1-7)
        1: 앉기
        2: 서기 (양다리 곧음)
        3: 서기 (한다리 곧음)
        4: 서기/쪼그려 앉기 (양무릎 굴곡)
        5: 서기/쪼그려 앉기 (한무릎 굴곡)
        6: 무릎꿇기
        7: 걷기/이동
        """
        left_knee_angle = angles.get('left_knee', 180)
        right_knee_angle = angles.get('right_knee', 180)
        left_hip_angle = angles.get('left_hip', 180)
        right_hip_angle = angles.get('right_hip', 180)

        # 무릎 굴곡 판단 (180도 = 곧음, 작을수록 굴곡)
        left_knee_bent = left_knee_angle < 150
        right_knee_bent = right_knee_angle < 150

        # 고관절 굴곡으로 앉기 판단
        is_sitting = left_hip_angle < 120 and right_hip_angle < 120

        if is_sitting:
            return 1
        elif left_knee_bent and right_knee_bent:
            # 양무릎 굴곡 정도에 따라
            if left_knee_angle < 90 and right_knee_angle < 90:
                return 6  # 무릎꿇기
            else:
                return 4  # 쪼그려 앉기
        elif left_knee_bent or right_knee_bent:
            return 5  # 한무릎 굴곡
        else:
            return 2  # 양다리 곧음

    def _get_action_category(self, back: int, arms: int, legs: int) -> int:
        """조치 카테고리 조회"""
        key = (back, arms, legs)
        return self.ACTION_CATEGORY_TABLE.get(key, 1)

    def get_risk_level(self, ac: int) -> str:
        """조치 카테고리에 따른 위험 수준 반환"""
        if ac == 1:
            return 'normal'
        elif ac == 2:
            return 'slight'
        elif ac == 3:
            return 'harmful'
        else:
            return 'very_harmful'

    def get_action_required(self, risk_level: str) -> str:
        """위험 수준에 따른 조치 사항 반환"""
        return self.ACTION_MESSAGES.get(risk_level, '')
