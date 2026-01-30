"""NLE Calculator 테스트"""

import pytest
import sys
from pathlib import Path

# 테스트 모듈 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.ergonomic.nle_calculator import NLECalculator, NLEResult


class TestNLEResult:
    """NLEResult 데이터 클래스 테스트"""

    def test_nle_result_creation(self):
        """NLEResult 인스턴스 생성"""
        result = NLEResult(
            hm=1.0, vm=1.0, dm=1.0, am=1.0, fm=0.94, cm=1.0,
            rwl=21.62, li=0.46, risk_level='safe'
        )
        assert result.hm == 1.0
        assert result.rwl == 21.62
        assert result.li == 0.46
        assert result.risk_level == 'safe'

    def test_nle_result_multipliers(self):
        """NLEResult multipliers 속성"""
        result = NLEResult(
            hm=0.83, vm=0.93, dm=0.91, am=0.86, fm=0.88, cm=0.95,
            rwl=12.5, li=1.2, risk_level='increased'
        )
        assert result.hm == 0.83
        assert result.vm == 0.93
        assert result.dm == 0.91
        assert result.am == 0.86
        assert result.fm == 0.88
        assert result.cm == 0.95


class TestNLECalculatorMultipliers:
    """NLE Multiplier 계산 테스트"""

    def test_horizontal_multiplier(self):
        """HM (Horizontal Multiplier) 계산"""
        calc = NLECalculator()

        # HM = 25 / H (최대 1.0)
        assert calc.calculate_hm(25) == 1.0   # H=25cm -> HM=1.0
        assert calc.calculate_hm(50) == 0.5   # H=50cm -> HM=0.5
        assert calc.calculate_hm(63) == pytest.approx(0.397, rel=0.01)

    def test_vertical_multiplier(self):
        """VM (Vertical Multiplier) 계산"""
        calc = NLECalculator()

        # VM = 1 - 0.003 * |V - 75|
        assert calc.calculate_vm(75) == 1.0   # V=75cm -> VM=1.0
        assert calc.calculate_vm(0) == pytest.approx(0.775, rel=0.01)
        assert calc.calculate_vm(150) == pytest.approx(0.775, rel=0.01)

    def test_distance_multiplier(self):
        """DM (Distance Multiplier) 계산"""
        calc = NLECalculator()

        # DM = 0.82 + 4.5 / D (최대 1.0)
        assert calc.calculate_dm(25) == 1.0   # D=25cm -> DM=1.0
        assert calc.calculate_dm(50) == pytest.approx(0.91, rel=0.01)

    def test_asymmetry_multiplier(self):
        """AM (Asymmetry Multiplier) 계산"""
        calc = NLECalculator()

        # AM = 1 - 0.0032 * A
        assert calc.calculate_am(0) == 1.0    # A=0° -> AM=1.0
        assert calc.calculate_am(45) == pytest.approx(0.856, rel=0.01)
        assert calc.calculate_am(90) == pytest.approx(0.712, rel=0.01)

    def test_frequency_multiplier(self):
        """FM (Frequency Multiplier) 테이블 조회"""
        calc = NLECalculator()

        # F=1회/분, Duration=≤1hr, V<75cm
        assert calc.calculate_fm(frequency=1, duration_hours=0.5, v=50) == 0.94

        # F=1회/분, Duration=≤1hr, V≥75cm
        assert calc.calculate_fm(frequency=1, duration_hours=0.5, v=80) == 0.94

    def test_coupling_multiplier(self):
        """CM (Coupling Multiplier) 테이블 조회"""
        calc = NLECalculator()

        # Good coupling, V<75cm
        assert calc.calculate_cm(coupling=1, v=50) == 1.0
        # Fair coupling, V<75cm
        assert calc.calculate_cm(coupling=2, v=50) == 0.95
        # Poor coupling
        assert calc.calculate_cm(coupling=3, v=50) == 0.90


class TestNLECalculatorRWL:
    """NLE RWL 계산 테스트"""

    def test_rwl_ideal_conditions(self):
        """이상적 조건에서 RWL 계산"""
        calc = NLECalculator()

        # 이상적 조건: H=25, V=75, D=25, A=0, F=1, C=Good
        result = calc.calculate(
            h=25, v=75, d=25, a=0,
            frequency=1, duration_hours=1, coupling=1, load=10
        )

        # RWL = 23 × 1.0 × 1.0 × 1.0 × 1.0 × FM × 1.0
        assert result.rwl > 20
        assert result.rwl <= 23

    def test_rwl_poor_conditions(self):
        """열악한 조건에서 RWL 계산"""
        calc = NLECalculator()

        result = calc.calculate(
            h=50, v=30, d=50, a=45,
            frequency=5, duration_hours=2, coupling=3, load=15
        )

        # 열악한 조건에서는 RWL이 낮음
        assert result.rwl < 10


class TestNLECalculatorLI:
    """NLE Lifting Index 계산 테스트"""

    def test_lifting_index_calculation(self):
        """LI 계산"""
        calc = NLECalculator()

        result = calc.calculate(
            h=25, v=75, d=25, a=0,
            frequency=1, duration_hours=1, coupling=1, load=10
        )

        # LI = Load / RWL
        expected_li = 10 / result.rwl
        assert result.li == pytest.approx(expected_li, rel=0.01)

    def test_lifting_index_zero_load(self):
        """Load=0일 때 LI 계산"""
        calc = NLECalculator()

        result = calc.calculate(
            h=25, v=75, d=25, a=0,
            frequency=1, duration_hours=1, coupling=1, load=0
        )

        assert result.li == 0


class TestNLECalculatorRiskLevel:
    """NLE 위험 수준 판정 테스트"""

    def test_risk_level_safe(self):
        """안전 수준 (LI ≤ 1.0)"""
        calc = NLECalculator()
        assert calc.get_risk_level(0.5) == 'safe'
        assert calc.get_risk_level(1.0) == 'safe'

    def test_risk_level_increased(self):
        """주의 수준 (1.0 < LI ≤ 3.0)"""
        calc = NLECalculator()
        assert calc.get_risk_level(1.5) == 'increased'
        assert calc.get_risk_level(3.0) == 'increased'

    def test_risk_level_high(self):
        """위험 수준 (LI > 3.0)"""
        calc = NLECalculator()
        assert calc.get_risk_level(3.5) == 'high'
        assert calc.get_risk_level(10.0) == 'high'

    def test_calculate_returns_correct_risk(self):
        """calculate()에서 올바른 위험 수준 반환"""
        calc = NLECalculator()

        # 안전한 조건
        result = calc.calculate(
            h=25, v=75, d=25, a=0,
            frequency=1, duration_hours=1, coupling=1, load=5
        )
        assert result.risk_level == 'safe'
