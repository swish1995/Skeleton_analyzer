"""RULA/REBA Calculator 세부 점수 테스트 (Phase 2)"""

import pytest
import sys
from pathlib import Path

# 테스트 모듈 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.ergonomic.rula_calculator import RULACalculator, RULAResult
from core.ergonomic.reba_calculator import REBACalculator, REBAResult


class TestRULAResultDetailFields:
    """RULAResult 세부 점수 필드 테스트"""

    def test_rula_result_has_upper_arm_detail_fields(self):
        """RULAResult에 상박 세부 필드 존재"""
        result = RULAResult(
            final_score=3,
            risk_level='investigate',
            action_required='',
            details={},
        )
        assert hasattr(result, 'upper_arm_base')
        assert hasattr(result, 'upper_arm_shoulder_raised')
        assert hasattr(result, 'upper_arm_abducted')
        assert hasattr(result, 'upper_arm_supported')

    def test_rula_result_has_lower_arm_detail_fields(self):
        """RULAResult에 하박 세부 필드 존재"""
        result = RULAResult(
            final_score=3,
            risk_level='investigate',
            action_required='',
            details={},
        )
        assert hasattr(result, 'lower_arm_base')
        assert hasattr(result, 'lower_arm_working_across')

    def test_rula_result_has_wrist_detail_fields(self):
        """RULAResult에 손목 세부 필드 존재"""
        result = RULAResult(
            final_score=3,
            risk_level='investigate',
            action_required='',
            details={},
        )
        assert hasattr(result, 'wrist_base')
        assert hasattr(result, 'wrist_bent_midline')

    def test_rula_result_has_neck_detail_fields(self):
        """RULAResult에 목 세부 필드 존재"""
        result = RULAResult(
            final_score=3,
            risk_level='investigate',
            action_required='',
            details={},
        )
        assert hasattr(result, 'neck_base')
        assert hasattr(result, 'neck_twisted')
        assert hasattr(result, 'neck_side_bending')

    def test_rula_result_has_trunk_detail_fields(self):
        """RULAResult에 몸통 세부 필드 존재"""
        result = RULAResult(
            final_score=3,
            risk_level='investigate',
            action_required='',
            details={},
        )
        assert hasattr(result, 'trunk_base')
        assert hasattr(result, 'trunk_twisted')
        assert hasattr(result, 'trunk_side_bending')


class TestRULACalculatorDetailScores:
    """RULACalculator 세부 점수 계산 테스트"""

    @pytest.fixture
    def calculator(self):
        return RULACalculator()

    @pytest.fixture
    def sample_angles(self):
        return {
            'left_shoulder': 90,
            'left_elbow': 90,
            'left_wrist': 180,
            'neck': 170,
            'left_knee': 180,
            'right_knee': 180,
        }

    @pytest.fixture
    def sample_landmarks(self):
        # 간단한 landmark 데이터
        landmarks = [{'x': 0, 'y': 0, 'z': 0} for _ in range(33)]
        # 어깨
        landmarks[11] = {'x': 0.4, 'y': 0.3, 'z': 0}  # LEFT_SHOULDER
        landmarks[12] = {'x': 0.6, 'y': 0.3, 'z': 0}  # RIGHT_SHOULDER
        # 팔꿈치
        landmarks[13] = {'x': 0.35, 'y': 0.5, 'z': 0}  # LEFT_ELBOW
        landmarks[14] = {'x': 0.65, 'y': 0.5, 'z': 0}  # RIGHT_ELBOW
        # 손목
        landmarks[15] = {'x': 0.3, 'y': 0.7, 'z': 0}  # LEFT_WRIST
        landmarks[16] = {'x': 0.7, 'y': 0.7, 'z': 0}  # RIGHT_WRIST
        # 골반
        landmarks[23] = {'x': 0.4, 'y': 0.6, 'z': 0}  # LEFT_HIP
        landmarks[24] = {'x': 0.6, 'y': 0.6, 'z': 0}  # RIGHT_HIP
        # 코
        landmarks[0] = {'x': 0.5, 'y': 0.1, 'z': 0}   # NOSE
        return landmarks

    def test_calculate_returns_upper_arm_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 상박 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.upper_arm_base >= 1
        assert result.upper_arm_shoulder_raised in [0, 1]
        assert result.upper_arm_abducted in [0, 1]
        assert result.upper_arm_supported in [-1, 0]

    def test_calculate_returns_lower_arm_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 하박 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.lower_arm_base >= 1
        assert result.lower_arm_working_across in [0, 1]

    def test_calculate_returns_wrist_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 손목 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.wrist_base >= 1
        assert result.wrist_bent_midline in [0, 1]

    def test_calculate_returns_neck_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 목 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.neck_base >= 1
        assert result.neck_twisted in [0, 1]
        assert result.neck_side_bending in [0, 1]

    def test_calculate_returns_trunk_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 몸통 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.trunk_base >= 1
        assert result.trunk_twisted in [0, 1]
        assert result.trunk_side_bending in [0, 1]

    def test_upper_arm_total_equals_sum_of_details(self, calculator, sample_angles, sample_landmarks):
        """상박 total = base + shoulder_raised + abducted + supported"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        expected_total = (
            result.upper_arm_base +
            result.upper_arm_shoulder_raised +
            result.upper_arm_abducted +
            result.upper_arm_supported
        )
        assert result.upper_arm_score == expected_total

    def test_lower_arm_total_equals_sum_of_details(self, calculator, sample_angles, sample_landmarks):
        """하박 total = base + working_across"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        expected_total = result.lower_arm_base + result.lower_arm_working_across
        assert result.lower_arm_score == expected_total

    def test_neck_total_equals_sum_of_details(self, calculator, sample_angles, sample_landmarks):
        """목 total = base + twisted + side_bending"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        expected_total = (
            result.neck_base +
            result.neck_twisted +
            result.neck_side_bending
        )
        assert result.neck_score == expected_total

    def test_trunk_total_equals_sum_of_details(self, calculator, sample_angles, sample_landmarks):
        """몸통 total = base + twisted + side_bending"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        expected_total = (
            result.trunk_base +
            result.trunk_twisted +
            result.trunk_side_bending
        )
        assert result.trunk_score == expected_total


class TestREBAResultDetailFields:
    """REBAResult 세부 점수 필드 테스트"""

    def test_reba_result_has_neck_detail_fields(self):
        """REBAResult에 목 세부 필드 존재"""
        result = REBAResult(
            final_score=3,
            risk_level='low',
            action_required='',
            details={},
        )
        assert hasattr(result, 'neck_base')
        assert hasattr(result, 'neck_twist_side')

    def test_reba_result_has_trunk_detail_fields(self):
        """REBAResult에 몸통 세부 필드 존재"""
        result = REBAResult(
            final_score=3,
            risk_level='low',
            action_required='',
            details={},
        )
        assert hasattr(result, 'trunk_base')
        assert hasattr(result, 'trunk_twist_side')

    def test_reba_result_has_leg_detail_fields(self):
        """REBAResult에 다리 세부 필드 존재"""
        result = REBAResult(
            final_score=3,
            risk_level='low',
            action_required='',
            details={},
        )
        assert hasattr(result, 'leg_base')
        assert hasattr(result, 'leg_knee_30_60')
        assert hasattr(result, 'leg_knee_over_60')

    def test_reba_result_has_upper_arm_detail_fields(self):
        """REBAResult에 상완 세부 필드 존재"""
        result = REBAResult(
            final_score=3,
            risk_level='low',
            action_required='',
            details={},
        )
        assert hasattr(result, 'upper_arm_base')
        assert hasattr(result, 'upper_arm_shoulder_raised')
        assert hasattr(result, 'upper_arm_abducted')
        assert hasattr(result, 'upper_arm_supported')

    def test_reba_result_has_wrist_detail_fields(self):
        """REBAResult에 손목 세부 필드 존재"""
        result = REBAResult(
            final_score=3,
            risk_level='low',
            action_required='',
            details={},
        )
        assert hasattr(result, 'wrist_base')
        assert hasattr(result, 'wrist_twisted')


class TestREBACalculatorDetailScores:
    """REBACalculator 세부 점수 계산 테스트"""

    @pytest.fixture
    def calculator(self):
        return REBACalculator()

    @pytest.fixture
    def sample_angles(self):
        return {
            'left_shoulder': 90,
            'left_elbow': 90,
            'left_wrist': 180,
            'neck': 170,
            'left_knee': 180,
            'right_knee': 180,
        }

    @pytest.fixture
    def sample_landmarks(self):
        landmarks = [{'x': 0, 'y': 0, 'z': 0} for _ in range(33)]
        landmarks[11] = {'x': 0.4, 'y': 0.3, 'z': 0}  # LEFT_SHOULDER
        landmarks[12] = {'x': 0.6, 'y': 0.3, 'z': 0}  # RIGHT_SHOULDER
        landmarks[13] = {'x': 0.35, 'y': 0.5, 'z': 0}  # LEFT_ELBOW
        landmarks[14] = {'x': 0.65, 'y': 0.5, 'z': 0}  # RIGHT_ELBOW
        landmarks[15] = {'x': 0.3, 'y': 0.7, 'z': 0}  # LEFT_WRIST
        landmarks[16] = {'x': 0.7, 'y': 0.7, 'z': 0}  # RIGHT_WRIST
        landmarks[23] = {'x': 0.4, 'y': 0.6, 'z': 0}  # LEFT_HIP
        landmarks[24] = {'x': 0.6, 'y': 0.6, 'z': 0}  # RIGHT_HIP
        landmarks[0] = {'x': 0.5, 'y': 0.1, 'z': 0}   # NOSE
        return landmarks

    def test_calculate_returns_neck_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 목 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.neck_base >= 1
        assert result.neck_twist_side in [0, 1]

    def test_calculate_returns_trunk_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 몸통 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.trunk_base >= 1
        assert result.trunk_twist_side in [0, 1]

    def test_calculate_returns_leg_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 다리 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.leg_base >= 1
        assert result.leg_knee_30_60 in [0, 1]
        assert result.leg_knee_over_60 in [0, 2]

    def test_calculate_returns_upper_arm_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 상완 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.upper_arm_base >= 1
        assert result.upper_arm_shoulder_raised in [0, 1]
        assert result.upper_arm_abducted in [0, 1]
        assert result.upper_arm_supported in [-1, 0]

    def test_calculate_returns_wrist_details(self, calculator, sample_angles, sample_landmarks):
        """calculate()가 손목 세부 점수를 반환"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        assert result.wrist_base >= 1
        assert result.wrist_twisted in [0, 1]

    def test_neck_total_equals_sum_of_details(self, calculator, sample_angles, sample_landmarks):
        """목 total = base + twist_side"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        expected_total = result.neck_base + result.neck_twist_side
        assert result.neck_score == expected_total

    def test_trunk_total_equals_sum_of_details(self, calculator, sample_angles, sample_landmarks):
        """몸통 total = base + twist_side"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        expected_total = result.trunk_base + result.trunk_twist_side
        assert result.trunk_score == expected_total

    def test_leg_total_equals_sum_of_details(self, calculator, sample_angles, sample_landmarks):
        """다리 total = base + knee_30_60 + knee_over_60"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        expected_total = (
            result.leg_base +
            result.leg_knee_30_60 +
            result.leg_knee_over_60
        )
        assert result.leg_score == expected_total

    def test_upper_arm_total_equals_sum_of_details(self, calculator, sample_angles, sample_landmarks):
        """상완 total = base + shoulder_raised + abducted + supported"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        expected_total = (
            result.upper_arm_base +
            result.upper_arm_shoulder_raised +
            result.upper_arm_abducted +
            result.upper_arm_supported
        )
        assert result.upper_arm_score == expected_total

    def test_wrist_total_equals_sum_of_details(self, calculator, sample_angles, sample_landmarks):
        """손목 total = base + twisted"""
        result = calculator.calculate(sample_angles, sample_landmarks)

        expected_total = result.wrist_base + result.wrist_twisted
        assert result.wrist_score == expected_total
