"""
Excel 세부 항목 합산 수식 테스트

Phase 5.2: Excel 수식 테스트
- RULA/REBA 세부 항목 합산 수식 정확성 검증
- 기존 수식과 통합 테스트
"""

import pytest
from src.utils.excel_formulas import (
    # 기존 수식
    get_rula_score_a_formula,
    get_rula_score_b_formula,
    get_rula_final_formula,
    get_rula_risk_formula,
    get_reba_score_a_formula,
    get_reba_score_b_formula,
    get_reba_final_formula,
    get_reba_risk_formula,
    # 세부 항목 합산 수식
    get_rula_upper_arm_total_formula,
    get_rula_lower_arm_total_formula,
    get_rula_wrist_total_formula,
    get_rula_neck_total_formula,
    get_rula_trunk_total_formula,
    get_reba_neck_total_formula,
    get_reba_trunk_total_formula,
    get_reba_leg_total_formula,
    get_reba_upper_arm_total_formula,
    get_reba_wrist_total_formula,
)


class TestRULADetailFormulas:
    """RULA 세부 항목 합산 수식 테스트"""

    def test_upper_arm_total_formula_structure(self):
        """상박 총점 수식 구조 테스트"""
        cols = {
            'base': 'A',
            'shoulder_raised': 'B',
            'abducted': 'C',
            'supported': 'D',
        }
        formula = get_rula_upper_arm_total_formula(2, cols)

        assert formula.startswith('=')
        assert 'A2' in formula
        assert 'B2' in formula
        assert 'C2' in formula
        assert 'D2' in formula

    def test_upper_arm_total_formula_is_sum(self):
        """상박 총점 수식이 합산인지 테스트"""
        cols = {
            'base': 'A',
            'shoulder_raised': 'B',
            'abducted': 'C',
            'supported': 'D',
        }
        formula = get_rula_upper_arm_total_formula(2, cols)

        # 수식: =A2+B2+C2+D2
        assert formula == '=A2+B2+C2+D2'

    def test_lower_arm_total_formula_structure(self):
        """하박 총점 수식 구조 테스트"""
        cols = {
            'base': 'E',
            'working_across': 'F',
        }
        formula = get_rula_lower_arm_total_formula(3, cols)

        assert formula.startswith('=')
        assert 'E3' in formula
        assert 'F3' in formula
        assert formula == '=E3+F3'

    def test_wrist_total_formula_structure(self):
        """손목 총점 수식 구조 테스트"""
        cols = {
            'base': 'G',
            'bent_midline': 'H',
        }
        formula = get_rula_wrist_total_formula(4, cols)

        assert formula == '=G4+H4'

    def test_neck_total_formula_structure(self):
        """목 총점 수식 구조 테스트"""
        cols = {
            'base': 'I',
            'twisted': 'J',
            'side_bending': 'K',
        }
        formula = get_rula_neck_total_formula(5, cols)

        assert formula == '=I5+J5+K5'

    def test_trunk_total_formula_structure(self):
        """몸통 총점 수식 구조 테스트"""
        cols = {
            'base': 'L',
            'twisted': 'M',
            'side_bending': 'N',
        }
        formula = get_rula_trunk_total_formula(6, cols)

        assert formula == '=L6+M6+N6'

    def test_formula_with_different_rows(self):
        """다른 행 번호에서 수식 테스트"""
        cols = {
            'base': 'A',
            'shoulder_raised': 'B',
            'abducted': 'C',
            'supported': 'D',
        }

        formula_row_10 = get_rula_upper_arm_total_formula(10, cols)
        formula_row_100 = get_rula_upper_arm_total_formula(100, cols)

        assert 'A10' in formula_row_10
        assert 'A100' in formula_row_100


class TestREBADetailFormulas:
    """REBA 세부 항목 합산 수식 테스트"""

    def test_neck_total_formula_structure(self):
        """목 총점 수식 구조 테스트"""
        cols = {
            'base': 'A',
            'twist_side': 'B',
        }
        formula = get_reba_neck_total_formula(2, cols)

        assert formula == '=A2+B2'

    def test_trunk_total_formula_structure(self):
        """몸통 총점 수식 구조 테스트"""
        cols = {
            'base': 'C',
            'twist_side': 'D',
        }
        formula = get_reba_trunk_total_formula(3, cols)

        assert formula == '=C3+D3'

    def test_leg_total_formula_structure(self):
        """다리 총점 수식 구조 테스트"""
        cols = {
            'base': 'E',
            'knee_30_60': 'F',
            'knee_over_60': 'G',
        }
        formula = get_reba_leg_total_formula(4, cols)

        assert formula == '=E4+F4+G4'

    def test_upper_arm_total_formula_structure(self):
        """상완 총점 수식 구조 테스트"""
        cols = {
            'base': 'H',
            'shoulder_raised': 'I',
            'abducted': 'J',
            'supported': 'K',
        }
        formula = get_reba_upper_arm_total_formula(5, cols)

        assert formula == '=H5+I5+J5+K5'

    def test_wrist_total_formula_structure(self):
        """손목 총점 수식 구조 테스트"""
        cols = {
            'base': 'L',
            'twisted': 'M',
        }
        formula = get_reba_wrist_total_formula(6, cols)

        assert formula == '=L6+M6'


class TestFormulaIntegration:
    """기존 수식과 통합 테스트"""

    def test_rula_score_a_formula_exists(self):
        """RULA Score A 수식이 존재하는지 테스트"""
        cols = {
            'upper_arm': 'A',
            'lower_arm': 'B',
            'wrist': 'C',
            'wrist_twist': 'D',
            'muscle_a': 'E',
            'force_a': 'F',
        }
        formula = get_rula_score_a_formula(2, cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'RULA_A' in formula

    def test_rula_score_b_formula_exists(self):
        """RULA Score B 수식이 존재하는지 테스트"""
        cols = {
            'neck': 'G',
            'trunk': 'H',
            'leg': 'I',
            'muscle_b': 'J',
            'force_b': 'K',
        }
        formula = get_rula_score_b_formula(2, cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'RULA_B' in formula

    def test_rula_final_formula_exists(self):
        """RULA Final 수식이 존재하는지 테스트"""
        cols = {
            'score_a': 'L',
            'score_b': 'M',
        }
        formula = get_rula_final_formula(2, cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'RULA_C' in formula

    def test_rula_risk_formula_exists(self):
        """RULA Risk 수식이 존재하는지 테스트"""
        formula = get_rula_risk_formula(2, 'N')

        assert formula.startswith('=')
        assert 'IF' in formula
        assert 'acceptable' in formula
        assert 'change_now' in formula

    def test_reba_score_a_formula_exists(self):
        """REBA Score A 수식이 존재하는지 테스트"""
        cols = {
            'neck': 'A',
            'trunk': 'B',
            'leg': 'C',
            'load': 'D',
        }
        formula = get_reba_score_a_formula(2, cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'REBA_A' in formula

    def test_reba_score_b_formula_exists(self):
        """REBA Score B 수식이 존재하는지 테스트"""
        cols = {
            'upper_arm': 'E',
            'lower_arm': 'F',
            'wrist': 'G',
            'coupling': 'H',
        }
        formula = get_reba_score_b_formula(2, cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'REBA_B' in formula

    def test_reba_final_formula_exists(self):
        """REBA Final 수식이 존재하는지 테스트"""
        cols = {
            'score_a': 'I',
            'score_b': 'J',
            'activity': 'K',
        }
        formula = get_reba_final_formula(2, cols)

        assert formula.startswith('=')
        assert 'INDEX' in formula
        assert 'REBA_C' in formula

    def test_reba_risk_formula_exists(self):
        """REBA Risk 수식이 존재하는지 테스트"""
        formula = get_reba_risk_formula(2, 'L')

        assert formula.startswith('=')
        assert 'IF' in formula
        assert 'negligible' in formula
        assert 'very_high' in formula


class TestFormulaConsistency:
    """수식 일관성 테스트"""

    def test_all_rula_detail_formulas_start_with_equals(self):
        """모든 RULA 세부 수식이 =로 시작하는지 테스트"""
        sample_cols_4 = {'base': 'A', 'shoulder_raised': 'B', 'abducted': 'C', 'supported': 'D'}
        sample_cols_2 = {'base': 'A', 'working_across': 'B'}
        sample_cols_2b = {'base': 'A', 'bent_midline': 'B'}
        sample_cols_3 = {'base': 'A', 'twisted': 'B', 'side_bending': 'C'}

        formulas = [
            get_rula_upper_arm_total_formula(2, sample_cols_4),
            get_rula_lower_arm_total_formula(2, sample_cols_2),
            get_rula_wrist_total_formula(2, sample_cols_2b),
            get_rula_neck_total_formula(2, sample_cols_3),
            get_rula_trunk_total_formula(2, sample_cols_3),
        ]

        for formula in formulas:
            assert formula.startswith('='), f"Formula should start with '=': {formula}"

    def test_all_reba_detail_formulas_start_with_equals(self):
        """모든 REBA 세부 수식이 =로 시작하는지 테스트"""
        sample_cols_2 = {'base': 'A', 'twist_side': 'B'}
        sample_cols_3 = {'base': 'A', 'knee_30_60': 'B', 'knee_over_60': 'C'}
        sample_cols_4 = {'base': 'A', 'shoulder_raised': 'B', 'abducted': 'C', 'supported': 'D'}
        sample_cols_2b = {'base': 'A', 'twisted': 'B'}

        formulas = [
            get_reba_neck_total_formula(2, sample_cols_2),
            get_reba_trunk_total_formula(2, sample_cols_2),
            get_reba_leg_total_formula(2, sample_cols_3),
            get_reba_upper_arm_total_formula(2, sample_cols_4),
            get_reba_wrist_total_formula(2, sample_cols_2b),
        ]

        for formula in formulas:
            assert formula.startswith('='), f"Formula should start with '=': {formula}"

    def test_formulas_use_plus_operator(self):
        """수식이 + 연산자를 사용하는지 테스트"""
        cols = {'base': 'A', 'twisted': 'B', 'side_bending': 'C'}
        formula = get_rula_neck_total_formula(2, cols)

        # 수식에 + 연산자가 있어야 함
        assert '+' in formula
        # - 연산자는 없어야 함 (supported 필드 제외하고는 모두 양수 가점)
        # Note: supported는 -1 또는 0이지만, 수식에서는 그냥 더함 (값 자체가 음수)


class TestColumnLetterVariations:
    """다양한 컬럼 문자 테스트"""

    def test_single_letter_columns(self):
        """단일 문자 컬럼 테스트"""
        cols = {'base': 'A', 'twist_side': 'B'}
        formula = get_reba_neck_total_formula(2, cols)

        assert 'A2' in formula
        assert 'B2' in formula

    def test_double_letter_columns(self):
        """두 글자 컬럼 테스트 (AA, AB 등)"""
        cols = {'base': 'AA', 'twist_side': 'AB'}
        formula = get_reba_neck_total_formula(2, cols)

        assert 'AA2' in formula
        assert 'AB2' in formula

    def test_mixed_letter_columns(self):
        """혼합 컬럼 테스트"""
        cols = {
            'base': 'Z',
            'shoulder_raised': 'AA',
            'abducted': 'AB',
            'supported': 'AC',
        }
        formula = get_rula_upper_arm_total_formula(5, cols)

        assert 'Z5' in formula
        assert 'AA5' in formula
        assert 'AB5' in formula
        assert 'AC5' in formula
