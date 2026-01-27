"""각도 계산 모듈"""
import numpy as np
from typing import Tuple, Dict, List, Union

# MediaPipe Pose 랜드마크 인덱스
LANDMARKS = {
    'nose': 0,
    'left_eye_inner': 1,
    'left_eye': 2,
    'left_eye_outer': 3,
    'right_eye_inner': 4,
    'right_eye': 5,
    'right_eye_outer': 6,
    'left_ear': 7,
    'right_ear': 8,
    'mouth_left': 9,
    'mouth_right': 10,
    'left_shoulder': 11,
    'right_shoulder': 12,
    'left_elbow': 13,
    'right_elbow': 14,
    'left_wrist': 15,
    'right_wrist': 16,
    'left_pinky': 17,
    'right_pinky': 18,
    'left_index': 19,
    'right_index': 20,
    'left_thumb': 21,
    'right_thumb': 22,
    'left_hip': 23,
    'right_hip': 24,
    'left_knee': 25,
    'right_knee': 26,
    'left_ankle': 27,
    'right_ankle': 28,
    'left_heel': 29,
    'right_heel': 30,
    'left_foot_index': 31,
    'right_foot_index': 32,
}

# 각도 계산 대상 정의: (시작점, 꼭지점, 끝점)
ANGLE_DEFINITIONS = {
    'neck': ('left_shoulder', 'nose', 'right_shoulder'),
    'left_shoulder': ('left_elbow', 'left_shoulder', 'left_hip'),
    'right_shoulder': ('right_elbow', 'right_shoulder', 'right_hip'),
    'left_elbow': ('left_shoulder', 'left_elbow', 'left_wrist'),
    'right_elbow': ('right_shoulder', 'right_elbow', 'right_wrist'),
    'left_wrist': ('left_elbow', 'left_wrist', 'left_index'),
    'right_wrist': ('right_elbow', 'right_wrist', 'right_index'),
    'left_hip': ('left_shoulder', 'left_hip', 'left_knee'),
    'right_hip': ('right_shoulder', 'right_hip', 'right_knee'),
    'left_knee': ('left_hip', 'left_knee', 'left_ankle'),
    'right_knee': ('right_hip', 'right_knee', 'right_ankle'),
    'left_ankle': ('left_knee', 'left_ankle', 'left_foot_index'),
    'right_ankle': ('right_knee', 'right_ankle', 'right_foot_index'),
}


class AngleCalculator:
    """인체 관절 각도 계산 클래스"""

    def calculate_angle(
        self,
        a: Union[Tuple, List],
        b: Union[Tuple, List],
        c: Union[Tuple, List]
    ) -> float:
        """
        세 점으로 각도를 계산 (b가 꼭지점)

        Args:
            a: 시작점 좌표 (x, y) 또는 (x, y, z)
            b: 꼭지점 좌표 (x, y) 또는 (x, y, z)
            c: 끝점 좌표 (x, y) 또는 (x, y, z)

        Returns:
            각도 (도 단위, 0-180)
        """
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        # 벡터 계산
        ba = a - b
        bc = c - b

        # 코사인 계산
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-10)
        cosine = np.clip(cosine, -1.0, 1.0)

        # 각도 계산 (라디안 → 도)
        angle = np.arccos(cosine)
        return np.degrees(angle)

    def _get_point(self, landmarks: List, name: str) -> Tuple[float, float, float]:
        """랜드마크 이름으로 좌표 추출"""
        idx = LANDMARKS[name]
        lm = landmarks[idx]
        if isinstance(lm, dict):
            return (lm['x'], lm['y'], lm.get('z', 0))
        else:
            # MediaPipe NormalizedLandmark 객체인 경우
            return (lm.x, lm.y, getattr(lm, 'z', 0))

    def calculate_all_angles(self, landmarks: List) -> Dict[str, float]:
        """
        모든 관절 각도 계산

        Args:
            landmarks: 33개의 랜드마크 리스트

        Returns:
            각도 딕셔너리 {'joint_name': angle_value}
        """
        angles = {}

        for angle_name, (p1_name, p2_name, p3_name) in ANGLE_DEFINITIONS.items():
            try:
                p1 = self._get_point(landmarks, p1_name)
                p2 = self._get_point(landmarks, p2_name)
                p3 = self._get_point(landmarks, p3_name)
                angles[angle_name] = self.calculate_angle(p1, p2, p3)
            except (IndexError, KeyError, TypeError):
                angles[angle_name] = 0.0

        return angles
