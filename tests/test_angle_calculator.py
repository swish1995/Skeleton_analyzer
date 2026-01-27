"""AngleCalculator 클래스 테스트"""
import pytest
import numpy as np


class TestAngleCalculator:
    """AngleCalculator 클래스 테스트"""

    @pytest.fixture
    def calculator(self):
        from src.core.angle_calculator import AngleCalculator
        return AngleCalculator()

    # --- 기본 각도 계산 ---

    def test_calculate_angle_90_degrees(self, calculator):
        """직각(90도) 계산 테스트"""
        a = (0, 1)  # 위
        b = (0, 0)  # 꼭지점
        c = (1, 0)  # 오른쪽
        angle = calculator.calculate_angle(a, b, c)
        assert abs(angle - 90.0) < 0.1

    def test_calculate_angle_180_degrees(self, calculator):
        """일직선(180도) 계산 테스트"""
        a = (-1, 0)
        b = (0, 0)
        c = (1, 0)
        angle = calculator.calculate_angle(a, b, c)
        assert abs(angle - 180.0) < 0.1

    def test_calculate_angle_45_degrees(self, calculator):
        """45도 계산 테스트"""
        a = (0, 1)
        b = (0, 0)
        c = (1, 1)
        angle = calculator.calculate_angle(a, b, c)
        assert abs(angle - 45.0) < 0.1

    def test_calculate_angle_with_3d_points(self, calculator):
        """3D 좌표 각도 계산 테스트"""
        a = (0, 1, 0)
        b = (0, 0, 0)
        c = (1, 0, 0)
        angle = calculator.calculate_angle(a, b, c)
        assert abs(angle - 90.0) < 0.1

    def test_calculate_angle_60_degrees(self, calculator):
        """60도 계산 테스트"""
        a = (0, 1)
        b = (0, 0)
        c = (np.sqrt(3)/2, 0.5)  # (0,1)과 이 점 사이 각도 = 60도
        angle = calculator.calculate_angle(a, b, c)
        assert abs(angle - 60.0) < 0.1

    # --- 관절 각도 계산 ---

    def test_calculate_all_angles_returns_dict(self, calculator):
        """전체 각도 계산이 딕셔너리 반환하는지 테스트"""
        landmarks = self._create_mock_landmarks()
        angles = calculator.calculate_all_angles(landmarks)
        assert isinstance(angles, dict)
        # 필수 키 확인
        required_keys = [
            'neck', 'left_elbow', 'right_elbow',
            'left_shoulder', 'right_shoulder',
            'left_hip', 'right_hip',
            'left_knee', 'right_knee',
            'left_ankle', 'right_ankle',
            'left_wrist', 'right_wrist'
        ]
        for key in required_keys:
            assert key in angles

    def test_calculate_elbow_angle(self, calculator):
        """팔꿈치 각도 계산 테스트"""
        landmarks = self._create_mock_landmarks()
        angles = calculator.calculate_all_angles(landmarks)
        assert 'left_elbow' in angles
        assert 'right_elbow' in angles
        assert 0 <= angles['left_elbow'] <= 180
        assert 0 <= angles['right_elbow'] <= 180

    def test_calculate_knee_angle(self, calculator):
        """무릎 각도 계산 테스트"""
        landmarks = self._create_mock_landmarks()
        angles = calculator.calculate_all_angles(landmarks)
        assert 'left_knee' in angles
        assert 'right_knee' in angles
        assert 0 <= angles['left_knee'] <= 180
        assert 0 <= angles['right_knee'] <= 180

    def test_angles_in_valid_range(self, calculator):
        """모든 각도가 유효 범위(0-180) 내에 있는지 테스트"""
        landmarks = self._create_mock_landmarks()
        angles = calculator.calculate_all_angles(landmarks)
        for name, angle in angles.items():
            assert 0 <= angle <= 180, f"{name} angle {angle} out of range"

    def _create_mock_landmarks(self):
        """테스트용 랜드마크 생성 - 직립 자세 시뮬레이션"""
        # 33개 랜드마크 생성 (MediaPipe Pose 기준)
        landmarks = []
        # 기본 좌표 설정 (정면 직립 자세)
        base_positions = [
            (0.5, 0.1),   # 0: nose
            (0.48, 0.08), # 1: left_eye_inner
            (0.47, 0.08), # 2: left_eye
            (0.46, 0.08), # 3: left_eye_outer
            (0.52, 0.08), # 4: right_eye_inner
            (0.53, 0.08), # 5: right_eye
            (0.54, 0.08), # 6: right_eye_outer
            (0.44, 0.1),  # 7: left_ear
            (0.56, 0.1),  # 8: right_ear
            (0.48, 0.12), # 9: mouth_left
            (0.52, 0.12), # 10: mouth_right
            (0.35, 0.25), # 11: left_shoulder
            (0.65, 0.25), # 12: right_shoulder
            (0.30, 0.40), # 13: left_elbow
            (0.70, 0.40), # 14: right_elbow
            (0.28, 0.55), # 15: left_wrist
            (0.72, 0.55), # 16: right_wrist
            (0.26, 0.58), # 17: left_pinky
            (0.74, 0.58), # 18: right_pinky
            (0.27, 0.57), # 19: left_index
            (0.73, 0.57), # 20: right_index
            (0.29, 0.56), # 21: left_thumb
            (0.71, 0.56), # 22: right_thumb
            (0.40, 0.55), # 23: left_hip
            (0.60, 0.55), # 24: right_hip
            (0.40, 0.75), # 25: left_knee
            (0.60, 0.75), # 26: right_knee
            (0.40, 0.95), # 27: left_ankle
            (0.60, 0.95), # 28: right_ankle
            (0.38, 0.97), # 29: left_heel
            (0.62, 0.97), # 30: right_heel
            (0.42, 0.98), # 31: left_foot_index
            (0.58, 0.98), # 32: right_foot_index
        ]
        for x, y in base_positions:
            landmarks.append({'x': x, 'y': y, 'z': 0, 'visibility': 1.0})
        return landmarks
