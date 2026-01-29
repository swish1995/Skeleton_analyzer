"""Excel 수식 생성 테스트"""

import pytest

from src.utils.excel_formulas import (
    get_rula_score_a_formula,
    get_rula_score_b_formula,
    get_rula_final_formula,
    get_rula_risk_formula,
    get_reba_score_a_formula,
    get_reba_score_b_formula,
    get_reba_final_formula,
    get_reba_risk_formula,
    get_owas_code_formula,
    get_owas_ac_formula,
    get_owas_risk_formula,
)


class TestRULAFormulas:
    """RULA 수식 생성 테스트"""

    def test_rula_score_a_formula_structure(self):
        """RULA Score A 수식 구조 검증"""
        cols = {
            'upper_arm': 'F', 'lower_arm': 'G', 'wrist': 'H',
            'wrist_twist': 'I', 'muscle_a': 'M', 'force_a': 'N'
        }
        formula = get_rula_score_a_formula(row=2, cols=cols)

        # 수식 구조 검증
        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'RULA_A' in formula
        assert 'F2' in formula
        assert 'G2' in formula
        assert 'H2' in formula
        assert 'I2' in formula
        assert 'M2' in formula
        assert 'N2' in formula

    def test_rula_score_a_formula_row_3(self):
        """RULA Score A 수식 행 번호 변경 검증"""
        cols = {
            'upper_arm': 'F', 'lower_arm': 'G', 'wrist': 'H',
            'wrist_twist': 'I', 'muscle_a': 'M', 'force_a': 'N'
        }
        formula = get_rula_score_a_formula(row=3, cols=cols)

        assert 'F3' in formula
        assert 'M3' in formula

    def test_rula_score_b_formula_structure(self):
        """RULA Score B 수식 구조 검증"""
        cols = {
            'neck': 'J', 'trunk': 'K', 'leg': 'L',
            'muscle_b': 'O', 'force_b': 'P'
        }
        formula = get_rula_score_b_formula(row=2, cols=cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'RULA_B' in formula
        assert 'J2' in formula
        assert 'K2' in formula
        assert 'L2' in formula
        assert 'O2' in formula
        assert 'P2' in formula

    def test_rula_final_formula_structure(self):
        """RULA Final Score 수식 구조 검증"""
        cols = {'score_a': 'Q', 'score_b': 'R'}
        formula = get_rula_final_formula(row=2, cols=cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'RULA_C' in formula
        assert 'Q2' in formula
        assert 'R2' in formula
        # Score A/B가 테이블 범위를 벗어나지 않도록 MIN 사용
        assert 'MIN' in formula

    def test_rula_risk_formula_structure(self):
        """RULA Risk 수식 구조 검증"""
        formula = get_rula_risk_formula(row=2, score_col='S')

        assert formula.startswith('=')
        assert 'IF' in formula
        assert 'S2' in formula
        assert 'acceptable' in formula
        assert 'investigate' in formula
        assert 'change_soon' in formula
        assert 'change_now' in formula


class TestREBAFormulas:
    """REBA 수식 생성 테스트"""

    def test_reba_score_a_formula_structure(self):
        """REBA Score A 수식 구조 검증"""
        cols = {
            'neck': 'U', 'trunk': 'V', 'leg': 'W',
            'load': 'X'
        }
        formula = get_reba_score_a_formula(row=2, cols=cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'REBA_A' in formula
        assert 'U2' in formula
        assert 'V2' in formula
        assert 'W2' in formula
        assert 'X2' in formula

    def test_reba_score_b_formula_structure(self):
        """REBA Score B 수식 구조 검증"""
        cols = {
            'upper_arm': 'Y', 'lower_arm': 'Z', 'wrist': 'AA',
            'coupling': 'AB'
        }
        formula = get_reba_score_b_formula(row=2, cols=cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'REBA_B' in formula
        assert 'Y2' in formula
        assert 'Z2' in formula
        assert 'AA2' in formula
        assert 'AB2' in formula

    def test_reba_final_formula_structure(self):
        """REBA Final Score 수식 구조 검증"""
        cols = {'score_a': 'AC', 'score_b': 'AD', 'activity': 'AE'}
        formula = get_reba_final_formula(row=2, cols=cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'REBA_C' in formula
        assert 'AC2' in formula
        assert 'AD2' in formula
        assert 'AE2' in formula  # activity 점수 추가

    def test_reba_risk_formula_structure(self):
        """REBA Risk 수식 구조 검증"""
        formula = get_reba_risk_formula(row=2, score_col='AF')

        assert formula.startswith('=')
        assert 'IF' in formula
        assert 'AF2' in formula
        assert 'negligible' in formula
        assert 'low' in formula
        assert 'medium' in formula
        assert 'high' in formula
        assert 'very_high' in formula


class TestOWASFormulas:
    """OWAS 수식 생성 테스트"""

    def test_owas_code_formula_structure(self):
        """OWAS Code 수식 구조 검증"""
        cols = {
            'back': 'AG', 'arms': 'AH', 'legs': 'AI', 'load': 'AJ'
        }
        formula = get_owas_code_formula(row=2, cols=cols)

        # 문자열 연결 수식
        assert formula.startswith('=')
        assert 'AG2' in formula
        assert 'AH2' in formula
        assert 'AI2' in formula
        assert 'AJ2' in formula

    def test_owas_ac_formula_structure(self):
        """OWAS AC 수식 구조 검증"""
        cols = {'back': 'AG', 'arms': 'AH', 'legs': 'AI'}
        formula = get_owas_ac_formula(row=2, cols=cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'OWAS_AC' in formula
        assert 'AG2' in formula
        assert 'AH2' in formula
        assert 'AI2' in formula

    def test_owas_risk_formula_structure(self):
        """OWAS Risk 수식 구조 검증"""
        formula = get_owas_risk_formula(row=2, ac_col='AK')

        assert formula.startswith('=')
        assert 'IF' in formula
        assert 'AK2' in formula
        assert 'normal' in formula
        assert 'slight' in formula
        assert 'harmful' in formula
        assert 'very_harmful' in formula
