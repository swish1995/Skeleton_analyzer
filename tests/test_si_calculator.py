"""SI Calculator 테스트"""

import pytest
import sys
from pathlib import Path

# 테스트 모듈 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.ergonomic.si_calculator import SICalculator, SIResult


class TestSIResult:
    """SIResult 데이터 클래스 테스트"""

    def test_si_result_creation(self):
        """SIResult 인스턴스 생성"""
        result = SIResult(
            ie_m=1.0, de_m=0.5, em_m=0.5, hwp_m=1.0, sw_m=1.0, dd_m=0.25,
            score=0.0625, risk_level='safe'
        )
        assert result.ie_m == 1.0
        assert result.score == 0.0625
        assert result.risk_level == 'safe'

    def test_si_result_multipliers(self):
        """SIResult multipliers 속성"""
        result = SIResult(
            ie_m=6.0, de_m=1.5, em_m=1.5, hwp_m=1.5, sw_m=1.0, dd_m=0.75,
            score=15.1875, risk_level='hazardous'
        )
        assert result.ie_m == 6.0
        assert result.de_m == 1.5
        assert result.em_m == 1.5
        assert result.hwp_m == 1.5
        assert result.sw_m == 1.0
        assert result.dd_m == 0.75


class TestSICalculatorMultipliers:
    """SI Multiplier 테이블 조회 테스트"""

    def test_intensity_of_exertion_multiplier(self):
        """IE (Intensity of Exertion) Multiplier"""
        calc = SICalculator()

        assert calc.get_multiplier('ie', 1) == 1.0
        assert calc.get_multiplier('ie', 2) == 3.0
        assert calc.get_multiplier('ie', 3) == 6.0
        assert calc.get_multiplier('ie', 4) == 9.0
        assert calc.get_multiplier('ie', 5) == 13.0

    def test_duration_of_exertion_multiplier(self):
        """DE (Duration of Exertion) Multiplier"""
        calc = SICalculator()

        assert calc.get_multiplier('de', 1) == 0.5
        assert calc.get_multiplier('de', 3) == 1.5
        assert calc.get_multiplier('de', 5) == 3.0

    def test_efforts_per_minute_multiplier(self):
        """EM (Efforts per Minute) Multiplier"""
        calc = SICalculator()

        assert calc.get_multiplier('em', 1) == 0.5
        assert calc.get_multiplier('em', 3) == 1.5
        assert calc.get_multiplier('em', 5) == 3.0

    def test_hand_wrist_posture_multiplier(self):
        """HWP (Hand/Wrist Posture) Multiplier"""
        calc = SICalculator()

        assert calc.get_multiplier('hwp', 1) == 1.0
        assert calc.get_multiplier('hwp', 2) == 1.0
        assert calc.get_multiplier('hwp', 3) == 1.5
        assert calc.get_multiplier('hwp', 5) == 3.0

    def test_speed_of_work_multiplier(self):
        """SW (Speed of Work) Multiplier"""
        calc = SICalculator()

        assert calc.get_multiplier('sw', 1) == 1.0
        assert calc.get_multiplier('sw', 3) == 1.0
        assert calc.get_multiplier('sw', 4) == 1.5
        assert calc.get_multiplier('sw', 5) == 2.0

    def test_duration_per_day_multiplier(self):
        """DD (Duration per Day) Multiplier"""
        calc = SICalculator()

        assert calc.get_multiplier('dd', 1) == 0.25
        assert calc.get_multiplier('dd', 2) == 0.50
        assert calc.get_multiplier('dd', 3) == 0.75
        assert calc.get_multiplier('dd', 4) == 1.00
        assert calc.get_multiplier('dd', 5) == 1.50


class TestSICalculatorScore:
    """SI Score 계산 테스트"""

    def test_minimum_score(self):
        """최소 점수 (모두 레벨 1)"""
        calc = SICalculator()

        result = calc.calculate(ie=1, de=1, em=1, hwp=1, sw=1, dd=1)
        # SI = 1.0 × 0.5 × 0.5 × 1.0 × 1.0 × 0.25 = 0.0625
        assert result.score == pytest.approx(0.0625, rel=0.01)

    def test_medium_score(self):
        """중간 점수 (모두 레벨 3)"""
        calc = SICalculator()

        result = calc.calculate(ie=3, de=3, em=3, hwp=3, sw=3, dd=3)
        # SI = 6.0 × 1.5 × 1.5 × 1.5 × 1.0 × 0.75 = 15.1875
        assert result.score == pytest.approx(15.1875, rel=0.01)

    def test_maximum_score(self):
        """최대 점수 (모두 레벨 5)"""
        calc = SICalculator()

        result = calc.calculate(ie=5, de=5, em=5, hwp=5, sw=5, dd=5)
        # SI = 13.0 × 3.0 × 3.0 × 3.0 × 2.0 × 1.50 = 1053.0
        # (13 × 3 = 39, × 3 = 117, × 3 = 351, × 2 = 702, × 1.5 = 1053)
        assert result.score == pytest.approx(1053.0, rel=0.01)

    def test_mixed_levels(self):
        """혼합 레벨"""
        calc = SICalculator()

        result = calc.calculate(ie=2, de=3, em=2, hwp=1, sw=1, dd=2)
        # SI = 3.0 × 1.5 × 1.0 × 1.0 × 1.0 × 0.5 = 2.25
        assert result.score == pytest.approx(2.25, rel=0.01)


class TestSICalculatorRiskLevel:
    """SI 위험 수준 판정 테스트"""

    def test_risk_level_safe(self):
        """안전 수준 (SI < 3)"""
        calc = SICalculator()
        assert calc.get_risk_level(0.5) == 'safe'
        assert calc.get_risk_level(2.9) == 'safe'

    def test_risk_level_uncertain(self):
        """불확실 수준 (3 ≤ SI < 7)"""
        calc = SICalculator()
        assert calc.get_risk_level(3.0) == 'uncertain'
        assert calc.get_risk_level(6.9) == 'uncertain'

    def test_risk_level_hazardous(self):
        """위험 수준 (SI ≥ 7)"""
        calc = SICalculator()
        assert calc.get_risk_level(7.0) == 'hazardous'
        assert calc.get_risk_level(100) == 'hazardous'

    def test_calculate_returns_correct_risk(self):
        """calculate()에서 올바른 위험 수준 반환"""
        calc = SICalculator()

        # 안전한 조건 (모두 레벨 1)
        result = calc.calculate(ie=1, de=1, em=1, hwp=1, sw=1, dd=1)
        assert result.risk_level == 'safe'

        # 위험한 조건 (높은 레벨)
        result = calc.calculate(ie=4, de=3, em=3, hwp=3, sw=2, dd=4)
        assert result.risk_level == 'hazardous'


class TestSICalculatorBoundaryValues:
    """SI 경계값 테스트"""

    def test_level_boundary_clamp_low(self):
        """레벨 하한 (0 → 1)"""
        calc = SICalculator()

        # 0이하는 1로 처리
        assert calc.get_multiplier('ie', 0) == calc.get_multiplier('ie', 1)
        assert calc.get_multiplier('de', -1) == calc.get_multiplier('de', 1)

    def test_level_boundary_clamp_high(self):
        """레벨 상한 (6+ → 5)"""
        calc = SICalculator()

        # 6이상은 5로 처리
        assert calc.get_multiplier('ie', 6) == calc.get_multiplier('ie', 5)
        assert calc.get_multiplier('de', 10) == calc.get_multiplier('de', 5)

    def test_invalid_param_returns_default(self):
        """잘못된 파라미터명은 기본값 반환"""
        calc = SICalculator()

        assert calc.get_multiplier('invalid', 3) == 1.0
