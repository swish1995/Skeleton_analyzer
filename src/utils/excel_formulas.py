"""
Excel 수식 생성 모듈

RULA/REBA/OWAS 평가를 위한 Excel 수식을 생성합니다.
INDEX 함수를 사용하여 조회 테이블에서 값을 가져옵니다.
"""

from typing import Dict


def get_rula_score_a_formula(row: int, cols: Dict[str, str]) -> str:
    """
    RULA Score A 수식 생성

    수식 로직:
        INDEX(RULA_A, (upper_arm-1)*12 + (lower_arm-1)*4 + wrist, wrist_twist) + muscle_a + force_a

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - upper_arm: 상완 점수 컬럼
            - lower_arm: 전완 점수 컬럼
            - wrist: 손목 점수 컬럼
            - wrist_twist: 손목 비틀림 점수 컬럼
            - muscle_a: A그룹 근육 사용 점수 컬럼
            - force_a: A그룹 힘/부하 점수 컬럼

    Returns:
        Excel 수식 문자열
    """
    ua = f"{cols['upper_arm']}{row}"
    la = f"{cols['lower_arm']}{row}"
    w = f"{cols['wrist']}{row}"
    wt = f"{cols['wrist_twist']}{row}"
    ma = f"{cols['muscle_a']}{row}"
    fa = f"{cols['force_a']}{row}"

    # 행 인덱스: (upper_arm-1)*12 + (lower_arm-1)*4 + wrist
    row_idx = f"({ua}-1)*12+({la}-1)*4+{w}"

    return f"=INDEX(RULA_A,{row_idx},{wt})+{ma}+{fa}"


def get_rula_score_b_formula(row: int, cols: Dict[str, str]) -> str:
    """
    RULA Score B 수식 생성

    수식 로직:
        INDEX(RULA_B, neck, (trunk-1)*2 + leg) + muscle_b + force_b

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - neck: 목 점수 컬럼
            - trunk: 몸통 점수 컬럼
            - leg: 다리 점수 컬럼
            - muscle_b: B그룹 근육 사용 점수 컬럼
            - force_b: B그룹 힘/부하 점수 컬럼

    Returns:
        Excel 수식 문자열
    """
    n = f"{cols['neck']}{row}"
    t = f"{cols['trunk']}{row}"
    l = f"{cols['leg']}{row}"
    mb = f"{cols['muscle_b']}{row}"
    fb = f"{cols['force_b']}{row}"

    # 열 인덱스: (trunk-1)*2 + leg
    col_idx = f"({t}-1)*2+{l}"

    return f"=INDEX(RULA_B,{n},{col_idx})+{mb}+{fb}"


def get_rula_final_formula(row: int, cols: Dict[str, str]) -> str:
    """
    RULA Final Score 수식 생성

    수식 로직:
        INDEX(RULA_C, MIN(score_a, 8), MIN(score_b, 7))

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - score_a: A그룹 점수 컬럼
            - score_b: B그룹 점수 컬럼

    Returns:
        Excel 수식 문자열
    """
    sa = f"{cols['score_a']}{row}"
    sb = f"{cols['score_b']}{row}"

    # 테이블 범위 제한 (A: 1-8, B: 1-7)
    return f"=INDEX(RULA_C,MIN({sa},8),MIN({sb},7))"


def get_rula_risk_formula(row: int, score_col: str) -> str:
    """
    RULA Risk 수식 생성

    수식 로직:
        IF(score<=2, "acceptable", IF(score<=4, "investigate", IF(score<=6, "change_soon", "change_now")))

    Args:
        row: Excel 행 번호
        score_col: 최종 점수 컬럼

    Returns:
        Excel 수식 문자열
    """
    s = f"{score_col}{row}"

    return f'=IF({s}<=2,"acceptable",IF({s}<=4,"investigate",IF({s}<=6,"change_soon","change_now")))'


def get_reba_score_a_formula(row: int, cols: Dict[str, str]) -> str:
    """
    REBA Score A 수식 생성

    수식 로직:
        INDEX(REBA_A, (neck-1)*5 + trunk, leg) + load

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - neck: 목 점수 컬럼
            - trunk: 몸통 점수 컬럼
            - leg: 다리 점수 컬럼
            - load: 부하/힘 점수 컬럼

    Returns:
        Excel 수식 문자열
    """
    n = f"{cols['neck']}{row}"
    t = f"{cols['trunk']}{row}"
    l = f"{cols['leg']}{row}"
    load = f"{cols['load']}{row}"

    # 행 인덱스: (neck-1)*5 + trunk
    row_idx = f"({n}-1)*5+{t}"

    return f"=INDEX(REBA_A,{row_idx},{l})+{load}"


def get_reba_score_b_formula(row: int, cols: Dict[str, str]) -> str:
    """
    REBA Score B 수식 생성

    수식 로직:
        INDEX(REBA_B, (upper_arm-1)*3 + lower_arm, wrist) + coupling

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - upper_arm: 상완 점수 컬럼
            - lower_arm: 전완 점수 컬럼
            - wrist: 손목 점수 컬럼
            - coupling: 커플링 점수 컬럼

    Returns:
        Excel 수식 문자열
    """
    ua = f"{cols['upper_arm']}{row}"
    la = f"{cols['lower_arm']}{row}"
    w = f"{cols['wrist']}{row}"
    cp = f"{cols['coupling']}{row}"

    # 행 인덱스: (upper_arm-1)*3 + lower_arm
    row_idx = f"({ua}-1)*3+{la}"

    return f"=INDEX(REBA_B,{row_idx},{w})+{cp}"


def get_reba_final_formula(row: int, cols: Dict[str, str]) -> str:
    """
    REBA Final Score 수식 생성

    수식 로직:
        INDEX(REBA_C, MIN(score_a, 12), MIN(score_b, 12)) + activity

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - score_a: A그룹 점수 컬럼
            - score_b: B그룹 점수 컬럼
            - activity: 활동 점수 컬럼

    Returns:
        Excel 수식 문자열
    """
    sa = f"{cols['score_a']}{row}"
    sb = f"{cols['score_b']}{row}"
    act = f"{cols['activity']}{row}"

    # 테이블 범위 제한 (A: 1-12, B: 1-12)
    return f"=INDEX(REBA_C,MIN({sa},12),MIN({sb},12))+{act}"


def get_reba_risk_formula(row: int, score_col: str) -> str:
    """
    REBA Risk 수식 생성

    수식 로직:
        IF(score=1, "negligible", IF(score<=3, "low", IF(score<=7, "medium", IF(score<=10, "high", "very_high"))))

    Args:
        row: Excel 행 번호
        score_col: 최종 점수 컬럼

    Returns:
        Excel 수식 문자열
    """
    s = f"{score_col}{row}"

    return f'=IF({s}=1,"negligible",IF({s}<=3,"low",IF({s}<=7,"medium",IF({s}<=10,"high","very_high"))))'


def get_owas_code_formula(row: int, cols: Dict[str, str]) -> str:
    """
    OWAS Code 수식 생성 (4자리 자세 코드)

    수식 로직:
        back & arms & legs & load (문자열 연결)

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - back: 등 코드 컬럼
            - arms: 팔 코드 컬럼
            - legs: 다리 코드 컬럼
            - load: 부하 코드 컬럼

    Returns:
        Excel 수식 문자열
    """
    b = f"{cols['back']}{row}"
    a = f"{cols['arms']}{row}"
    l = f"{cols['legs']}{row}"
    load = f"{cols['load']}{row}"

    return f"={b}&{a}&{l}&{load}"


def get_owas_ac_formula(row: int, cols: Dict[str, str]) -> str:
    """
    OWAS Action Category 수식 생성

    수식 로직:
        INDEX(OWAS_AC, (back-1)*3 + arms, legs)

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - back: 등 코드 컬럼
            - arms: 팔 코드 컬럼
            - legs: 다리 코드 컬럼

    Returns:
        Excel 수식 문자열
    """
    b = f"{cols['back']}{row}"
    a = f"{cols['arms']}{row}"
    l = f"{cols['legs']}{row}"

    # 행 인덱스: (back-1)*3 + arms
    row_idx = f"({b}-1)*3+{a}"

    return f"=INDEX(OWAS_AC,{row_idx},{l})"


def get_owas_risk_formula(row: int, ac_col: str) -> str:
    """
    OWAS Risk 수식 생성

    수식 로직:
        IF(ac=1, "normal", IF(ac=2, "slight", IF(ac=3, "harmful", "very_harmful")))

    Args:
        row: Excel 행 번호
        ac_col: Action Category 컬럼

    Returns:
        Excel 수식 문자열
    """
    ac = f"{ac_col}{row}"

    return f'=IF({ac}=1,"normal",IF({ac}=2,"slight",IF({ac}=3,"harmful","very_harmful")))'


def get_nle_risk_formula(row: int, li_col: str) -> str:
    """
    NLE Risk 수식 생성

    수식 로직:
        IF(li<=1, "safe", IF(li<=3, "increased", "high"))

    Args:
        row: Excel 행 번호
        li_col: LI (Lifting Index) 컬럼

    Returns:
        Excel 수식 문자열
    """
    li = f"{li_col}{row}"

    return f'=IF({li}<=1,"safe",IF({li}<=3,"increased","high"))'


def get_si_score_formula(row: int, cols: Dict[str, str]) -> str:
    """
    SI Score 수식 생성

    수식 로직:
        INDEX(SI_IE,ie) * INDEX(SI_DE,de) * INDEX(SI_EM,em) *
        INDEX(SI_HWP,hwp) * INDEX(SI_SW,sw) * INDEX(SI_DD,dd)

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - ie: Intensity of Exertion 컬럼 (1-5)
            - de: Duration of Exertion 컬럼 (1-5)
            - em: Efforts per Minute 컬럼 (1-5)
            - hwp: Hand/Wrist Posture 컬럼 (1-5)
            - sw: Speed of Work 컬럼 (1-5)
            - dd: Duration per Day 컬럼 (1-5)

    Returns:
        Excel 수식 문자열
    """
    ie = f"{cols['ie']}{row}"
    de = f"{cols['de']}{row}"
    em = f"{cols['em']}{row}"
    hwp = f"{cols['hwp']}{row}"
    sw = f"{cols['sw']}{row}"
    dd = f"{cols['dd']}{row}"

    return f"=INDEX(SI_IE,{ie})*INDEX(SI_DE,{de})*INDEX(SI_EM,{em})*INDEX(SI_HWP,{hwp})*INDEX(SI_SW,{sw})*INDEX(SI_DD,{dd})"


def get_si_risk_formula(row: int, score_col: str) -> str:
    """
    SI Risk 수식 생성

    수식 로직:
        IF(score<3, "safe", IF(score<7, "uncertain", "hazardous"))

    Args:
        row: Excel 행 번호
        score_col: SI Score 컬럼

    Returns:
        Excel 수식 문자열
    """
    s = f"{score_col}{row}"

    return f'=IF({s}<3,"safe",IF({s}<7,"uncertain","hazardous"))'


# =============================================================================
# RULA 세부 항목 합산 수식
# =============================================================================

def get_rula_upper_arm_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    RULA 상박 총점 수식 생성

    수식 로직:
        base + shoulder_raised + abducted + supported

    Note:
        supported는 -1 또는 0 (팔 지지 시 감점)

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - shoulder_raised: 어깨 올림 컬럼
            - abducted: 외전 컬럼
            - supported: 팔 지지 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    raised = f"{cols['shoulder_raised']}{row}"
    abducted = f"{cols['abducted']}{row}"
    supported = f"{cols['supported']}{row}"

    return f"={base}+{raised}+{abducted}+{supported}"


def get_rula_lower_arm_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    RULA 하박 총점 수식 생성

    수식 로직:
        base + working_across

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - working_across: 중앙선 교차 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    across = f"{cols['working_across']}{row}"

    return f"={base}+{across}"


def get_rula_wrist_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    RULA 손목 총점 수식 생성

    수식 로직:
        base + bent_midline

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - bent_midline: 중립에서 꺾임 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    bent = f"{cols['bent_midline']}{row}"

    return f"={base}+{bent}"


def get_rula_neck_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    RULA 목 총점 수식 생성

    수식 로직:
        base + twisted + side_bending

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - twisted: 회전 컬럼
            - side_bending: 측굴 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    twisted = f"{cols['twisted']}{row}"
    side = f"{cols['side_bending']}{row}"

    return f"={base}+{twisted}+{side}"


def get_rula_trunk_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    RULA 몸통 총점 수식 생성

    수식 로직:
        base + twisted + side_bending

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - twisted: 회전 컬럼
            - side_bending: 측굴 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    twisted = f"{cols['twisted']}{row}"
    side = f"{cols['side_bending']}{row}"

    return f"={base}+{twisted}+{side}"


# =============================================================================
# REBA 세부 항목 합산 수식
# =============================================================================

def get_reba_neck_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    REBA 목 총점 수식 생성

    수식 로직:
        base + twist_side

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - twist_side: 회전/측굴 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    twist_side = f"{cols['twist_side']}{row}"

    return f"={base}+{twist_side}"


def get_reba_trunk_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    REBA 몸통 총점 수식 생성

    수식 로직:
        base + twist_side

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - twist_side: 회전/측굴 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    twist_side = f"{cols['twist_side']}{row}"

    return f"={base}+{twist_side}"


def get_reba_leg_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    REBA 다리 총점 수식 생성

    수식 로직:
        base + knee_30_60 + knee_over_60

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - knee_30_60: 무릎 30-60° 컬럼
            - knee_over_60: 무릎 60°+ 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    knee_30_60 = f"{cols['knee_30_60']}{row}"
    knee_over_60 = f"{cols['knee_over_60']}{row}"

    return f"={base}+{knee_30_60}+{knee_over_60}"


def get_reba_upper_arm_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    REBA 상완 총점 수식 생성

    수식 로직:
        base + shoulder_raised + abducted + supported

    Note:
        supported는 -1 또는 0 (팔 지지 시 감점)

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - shoulder_raised: 어깨 올림 컬럼
            - abducted: 외전 컬럼
            - supported: 팔 지지 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    raised = f"{cols['shoulder_raised']}{row}"
    abducted = f"{cols['abducted']}{row}"
    supported = f"{cols['supported']}{row}"

    return f"={base}+{raised}+{abducted}+{supported}"


def get_reba_wrist_total_formula(row: int, cols: Dict[str, str]) -> str:
    """
    REBA 손목 총점 수식 생성

    수식 로직:
        base + twisted

    Args:
        row: Excel 행 번호
        cols: 컬럼 매핑 딕셔너리
            - base: 기본 점수 컬럼
            - twisted: 비틀림 컬럼

    Returns:
        Excel 수식 문자열
    """
    base = f"{cols['base']}{row}"
    twisted = f"{cols['twisted']}{row}"

    return f"={base}+{twisted}"
