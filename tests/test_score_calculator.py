"""점수 계산기 모듈 테스트"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.score_calculator import (
    get_rula_table_a_score,
    get_rula_table_b_score,
    get_rula_table_c_score,
    get_rula_risk_level,
    get_reba_table_a_score,
    get_reba_table_b_score,
    get_reba_table_c_score,
    get_reba_risk_level,
    get_owas_action_category,
    get_owas_risk_level,
)


class TestRULAScoreCalculator:
    """RULA 점수 계산 테스트"""

    def test_rula_table_a_score_basic(self):
        """RULA Table A 기본 점수 조회"""
        # upper_arm=1, lower_arm=1, wrist=1, wrist_twist=1 → 1
        score = get_rula_table_a_score(1, 1, 1, 1)
        assert score == 1

    def test_rula_table_a_score_mid_range(self):
        """RULA Table A 중간 범위 테스트"""
        # upper_arm=2, lower_arm=2, wrist=2, wrist_twist=1 → 3
        score = get_rula_table_a_score(2, 2, 2, 1)
        assert score == 3

    def test_rula_table_a_score_high(self):
        """RULA Table A 높은 점수 테스트"""
        # upper_arm=6, lower_arm=3, wrist=4, wrist_twist=2 → 9
        score = get_rula_table_a_score(6, 3, 4, 2)
        assert score == 9

    def test_rula_table_b_score_basic(self):
        """RULA Table B 기본 점수 조회"""
        # neck=1, trunk=1, leg=1 → 1
        score = get_rula_table_b_score(1, 1, 1)
        assert score == 1

    def test_rula_table_b_score_mid_range(self):
        """RULA Table B 중간 범위 테스트"""
        # neck=2, trunk=3, leg=2 → 5
        score = get_rula_table_b_score(2, 3, 2)
        assert score == 5

    def test_rula_table_c_score_basic(self):
        """RULA Table C 기본 점수 조회"""
        # score_a=1, score_b=1 → 1
        score = get_rula_table_c_score(1, 1)
        assert score == 1

    def test_rula_table_c_score_mid_range(self):
        """RULA Table C 중간 범위 테스트"""
        # score_a=4, score_b=4 → 4
        score = get_rula_table_c_score(4, 4)
        assert score == 4

    def test_rula_table_c_score_high(self):
        """RULA Table C 높은 점수 테스트"""
        # score_a=8, score_b=7 → 7
        score = get_rula_table_c_score(8, 7)
        assert score == 7

    def test_rula_risk_level_acceptable(self):
        """RULA 위험 수준: acceptable (1-2)"""
        assert get_rula_risk_level(1) == 'acceptable'
        assert get_rula_risk_level(2) == 'acceptable'

    def test_rula_risk_level_investigate(self):
        """RULA 위험 수준: investigate (3-4)"""
        assert get_rula_risk_level(3) == 'investigate'
        assert get_rula_risk_level(4) == 'investigate'

    def test_rula_risk_level_change_soon(self):
        """RULA 위험 수준: change_soon (5-6)"""
        assert get_rula_risk_level(5) == 'change_soon'
        assert get_rula_risk_level(6) == 'change_soon'

    def test_rula_risk_level_change_now(self):
        """RULA 위험 수준: change_now (7+)"""
        assert get_rula_risk_level(7) == 'change_now'
        assert get_rula_risk_level(8) == 'change_now'


class TestREBAScoreCalculator:
    """REBA 점수 계산 테스트"""

    def test_reba_table_a_score_basic(self):
        """REBA Table A 기본 점수 조회"""
        # neck=1, trunk=1, leg=1 → 1
        score = get_reba_table_a_score(1, 1, 1)
        assert score == 1

    def test_reba_table_a_score_mid_range(self):
        """REBA Table A 중간 범위 테스트"""
        # neck=2, trunk=3, leg=3 → 6
        score = get_reba_table_a_score(2, 3, 3)
        assert score == 6

    def test_reba_table_b_score_basic(self):
        """REBA Table B 기본 점수 조회"""
        # upper_arm=1, lower_arm=1, wrist=1 → 1
        score = get_reba_table_b_score(1, 1, 1)
        assert score == 1

    def test_reba_table_b_score_mid_range(self):
        """REBA Table B 중간 범위 테스트"""
        # upper_arm=3, lower_arm=2, wrist=2 → 5
        score = get_reba_table_b_score(3, 2, 2)
        assert score == 5

    def test_reba_table_c_score_basic(self):
        """REBA Table C 기본 점수 조회"""
        # score_a=1, score_b=1 → 1
        score = get_reba_table_c_score(1, 1)
        assert score == 1

    def test_reba_table_c_score_mid_range(self):
        """REBA Table C 중간 범위 테스트"""
        # score_a=5, score_b=5 → 6
        score = get_reba_table_c_score(5, 5)
        assert score == 6

    def test_reba_risk_level_negligible(self):
        """REBA 위험 수준: negligible (1)"""
        assert get_reba_risk_level(1) == 'negligible'

    def test_reba_risk_level_low(self):
        """REBA 위험 수준: low (2-3)"""
        assert get_reba_risk_level(2) == 'low'
        assert get_reba_risk_level(3) == 'low'

    def test_reba_risk_level_medium(self):
        """REBA 위험 수준: medium (4-7)"""
        assert get_reba_risk_level(4) == 'medium'
        assert get_reba_risk_level(7) == 'medium'

    def test_reba_risk_level_high(self):
        """REBA 위험 수준: high (8-10)"""
        assert get_reba_risk_level(8) == 'high'
        assert get_reba_risk_level(10) == 'high'

    def test_reba_risk_level_very_high(self):
        """REBA 위험 수준: very_high (11+)"""
        assert get_reba_risk_level(11) == 'very_high'
        assert get_reba_risk_level(12) == 'very_high'


class TestOWASScoreCalculator:
    """OWAS 점수 계산 테스트"""

    def test_owas_action_category_normal(self):
        """OWAS AC 1 (정상)"""
        # back=1, arms=1, legs=1 → AC 1
        ac = get_owas_action_category(1, 1, 1)
        assert ac == 1

    def test_owas_action_category_slight(self):
        """OWAS AC 2 (약간 유해)"""
        # back=2, arms=1, legs=1 → AC 2
        ac = get_owas_action_category(2, 1, 1)
        assert ac == 2

    def test_owas_action_category_harmful(self):
        """OWAS AC 3 (유해)"""
        # back=4, arms=2, legs=3 → AC 3
        ac = get_owas_action_category(4, 2, 3)
        assert ac == 3

    def test_owas_action_category_very_harmful(self):
        """OWAS AC 4 (매우 유해)"""
        # back=4, arms=3, legs=3 → AC 4
        ac = get_owas_action_category(4, 3, 3)
        assert ac == 4

    def test_owas_risk_level_normal(self):
        """OWAS 위험 수준: normal (AC 1)"""
        assert get_owas_risk_level(1) == 'normal'

    def test_owas_risk_level_slight(self):
        """OWAS 위험 수준: slight (AC 2)"""
        assert get_owas_risk_level(2) == 'slight'

    def test_owas_risk_level_harmful(self):
        """OWAS 위험 수준: harmful (AC 3)"""
        assert get_owas_risk_level(3) == 'harmful'

    def test_owas_risk_level_very_harmful(self):
        """OWAS 위험 수준: very_harmful (AC 4)"""
        assert get_owas_risk_level(4) == 'very_harmful'


class TestEdgeCases:
    """경계값 및 예외 테스트"""

    def test_rula_table_a_boundary_values(self):
        """RULA Table A 경계값 테스트"""
        # 최소값
        score = get_rula_table_a_score(1, 1, 1, 1)
        assert score >= 1

        # 최대값
        score = get_rula_table_a_score(6, 3, 4, 2)
        assert score <= 9

    def test_reba_table_a_boundary_values(self):
        """REBA Table A 경계값 테스트"""
        # 최소값
        score = get_reba_table_a_score(1, 1, 1)
        assert score >= 1

        # 최대값
        score = get_reba_table_a_score(3, 5, 4)
        assert score <= 12

    def test_owas_invalid_codes_handled(self):
        """OWAS 잘못된 코드 처리"""
        # 범위 밖의 값도 기본값 반환
        ac = get_owas_action_category(0, 0, 0)
        assert ac >= 1

        ac = get_owas_action_category(5, 4, 8)
        assert ac >= 1
