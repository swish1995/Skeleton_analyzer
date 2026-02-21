"""각도 계산 모듈"""
import math
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

        # 수직선 기준 굴곡 각도 추가 (RULA/REBA에서 사용하는 실제 값)
        try:
            flexion_angles = self._calculate_flexion_angles(landmarks)
            angles.update(flexion_angles)
        except (IndexError, KeyError, TypeError):
            pass

        return angles

    def _calculate_flexion_angles(self, landmarks: List) -> Dict[str, float]:
        """
        굴곡 각도 계산 (RULA/REBA 평가에 사용되는 값, 0°=자연 자세)

        Args:
            landmarks: 33개의 랜드마크 리스트

        Returns:
            굴곡 각도 딕셔너리
        """
        flexion_angles = {}

        # 주요 랜드마크
        l_ear = self._get_point(landmarks, 'left_ear')
        r_ear = self._get_point(landmarks, 'right_ear')
        ls = self._get_point(landmarks, 'left_shoulder')
        rs = self._get_point(landmarks, 'right_shoulder')
        le = self._get_point(landmarks, 'left_elbow')
        re = self._get_point(landmarks, 'right_elbow')
        lw = self._get_point(landmarks, 'left_wrist')
        rw = self._get_point(landmarks, 'right_wrist')
        lh = self._get_point(landmarks, 'left_hip')
        rh = self._get_point(landmarks, 'right_hip')
        li = self._get_point(landmarks, 'left_index')
        ri = self._get_point(landmarks, 'right_index')
        lp = self._get_point(landmarks, 'left_pinky')
        rp = self._get_point(landmarks, 'right_pinky')
        lk = self._get_point(landmarks, 'left_knee')
        rk = self._get_point(landmarks, 'right_knee')
        la = self._get_point(landmarks, 'left_ankle')
        ra = self._get_point(landmarks, 'right_ankle')

        shoulder_center = (
            (ls[0] + rs[0]) / 2,
            (ls[1] + rs[1]) / 2,
            (ls[2] + rs[2]) / 2,
        )
        hip_center = (
            (lh[0] + rh[0]) / 2,
            (lh[1] + rh[1]) / 2,
            (lh[2] + rh[2]) / 2,
        )

        # --- 몸통 굴곡 (수직선 기준) ---
        flexion_angles['trunk_flexion'] = self._angle_from_vertical(
            shoulder_center, hip_center
        )

        # --- 목 굴곡 (귀 중심점 2D, 부호 포함) ---
        # nose 대신 귀 중심점 사용 (두개골 중심에 가까워 편향 감소)
        # 양수 = 굴곡 (앞으로 숙임), 음수 = 신전 (뒤로 젖힘)
        NECK_OFFSET = 5.0  # 정면 카메라 보정값 (°)
        nose = self._get_point(landmarks, 'nose')
        ear_center_2d = ((l_ear[0] + r_ear[0]) / 2, (l_ear[1] + r_ear[1]) / 2)
        sc_2d = (shoulder_center[0], shoulder_center[1])
        hc_2d = (hip_center[0], hip_center[1])
        neck_trunk_angle = self.calculate_angle(ear_center_2d, sc_2d, hc_2d)
        neck_value = 180 - neck_trunk_angle - NECK_OFFSET

        # 크로스곱으로 신전(뒤로 젖힘) 여부 판정
        # 얼굴 전방 방향(귀 중심→코)은 머리 위치에 상관없이 일정하므로,
        # 목의 편향 방향이 얼굴 전방과 반대이면 신전(뒤로 젖힘)
        trunk_up = (sc_2d[0] - hc_2d[0], sc_2d[1] - hc_2d[1])
        neck_dir = (ear_center_2d[0] - sc_2d[0], ear_center_2d[1] - sc_2d[1])
        nose_2d = (nose[0], nose[1])
        face_fwd = (nose_2d[0] - ear_center_2d[0], nose_2d[1] - ear_center_2d[1])

        cross_neck = trunk_up[0] * neck_dir[1] - trunk_up[1] * neck_dir[0]
        cross_face = trunk_up[0] * face_fwd[1] - trunk_up[1] * face_fwd[0]

        is_extension = (abs(cross_face) > 1e-10) and (cross_neck * cross_face < 0)

        if is_extension:
            flexion_angles['neck_flexion'] = -abs(neck_value)
        else:
            flexion_angles['neck_flexion'] = max(neck_value, 0)

        # --- 2D 좌표 추출 (z축 노이즈로 인한 과대측정 방지) ---
        ls2 = (ls[0], ls[1])
        rs2 = (rs[0], rs[1])
        le2 = (le[0], le[1])
        re2 = (re[0], re[1])
        lw2 = (lw[0], lw[1])
        rw2 = (rw[0], rw[1])
        lh2 = (lh[0], lh[1])
        rh2 = (rh[0], rh[1])
        li2 = (li[0], li[1])
        ri2 = (ri[0], ri[1])
        lp2 = (lp[0], lp[1])
        rp2 = (rp[0], rp[1])

        # --- 상박 굴곡 (팔꿈치-어깨-엉덩이, 0°=팔 내림) ---
        flexion_angles['left_shoulder_flexion'] = self.calculate_angle(le2, ls2, lh2)
        flexion_angles['right_shoulder_flexion'] = self.calculate_angle(re2, rs2, rh2)

        # --- 팔꿈치 굴곡 (0°=펴짐, 90°=직각) ---
        left_elbow_raw = self.calculate_angle(ls2, le2, lw2)
        right_elbow_raw = self.calculate_angle(rs2, re2, rw2)
        flexion_angles['left_elbow_flexion'] = max(180 - left_elbow_raw, 0)
        flexion_angles['right_elbow_flexion'] = max(180 - right_elbow_raw, 0)

        # --- 손목 굴곡 (검지/소지 중 최소 굴곡값) ---
        left_wrist_max = max(
            self.calculate_angle(le2, lw2, li2),
            self.calculate_angle(le2, lw2, lp2),
        )
        flexion_angles['left_wrist_flexion'] = max(180 - left_wrist_max, 0)

        right_wrist_max = max(
            self.calculate_angle(re2, rw2, ri2),
            self.calculate_angle(re2, rw2, rp2),
        )
        flexion_angles['right_wrist_flexion'] = max(180 - right_wrist_max, 0)

        # --- 무릎 굴곡 (0°=펴짐, 90°=직각) ---
        lk2 = (lk[0], lk[1])
        rk2 = (rk[0], rk[1])
        la2 = (la[0], la[1])
        ra2 = (ra[0], ra[1])
        left_knee_raw = self.calculate_angle(lh2, lk2, la2)
        right_knee_raw = self.calculate_angle(rh2, rk2, ra2)
        flexion_angles['left_knee_flexion'] = max(180 - left_knee_raw, 0)
        flexion_angles['right_knee_flexion'] = max(180 - right_knee_raw, 0)

        return flexion_angles

    @staticmethod
    def _angle_from_vertical(p_top: tuple, p_bottom: tuple) -> float:
        """
        상단점에서 하단점 방향이 수직선과 이루는 각도

        Args:
            p_top: 상단 점 (x, y)
            p_bottom: 하단 점 (x, y)

        Returns:
            각도 (도, 0=수직, 90=수평)
        """
        dx = p_bottom[0] - p_top[0]
        dy = p_bottom[1] - p_top[1]
        if dy == 0:
            return 90.0
        return math.degrees(math.atan(abs(dx) / abs(dy)))
