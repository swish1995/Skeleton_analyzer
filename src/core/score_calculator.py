"""
점수 계산기 모듈

RULA, REBA, OWAS 평가의 Table A/B/C 점수 조회 및 위험 수준 계산.
CaptureRecord에서 사용하기 위한 독립 모듈.
"""

from typing import Dict, Tuple

# =============================================================================
# RULA Tables
# =============================================================================

# RULA Table A: 상완/전완/손목/손목비틀림 조합 → A그룹 점수
# [upper_arm][lower_arm][wrist][wrist_twist]
RULA_TABLE_A = [
    # Upper Arm 1
    [[[1, 2], [2, 2], [2, 3], [3, 3]],   # Lower Arm 1
     [[2, 2], [2, 2], [3, 3], [3, 3]],   # Lower Arm 2
     [[2, 3], [3, 3], [3, 3], [4, 4]]],  # Lower Arm 3
    # Upper Arm 2
    [[[2, 3], [3, 3], [3, 4], [4, 4]],
     [[3, 3], [3, 3], [3, 4], [4, 4]],
     [[3, 4], [4, 4], [4, 4], [5, 5]]],
    # Upper Arm 3
    [[[3, 3], [4, 4], [4, 4], [5, 5]],
     [[3, 4], [4, 4], [4, 4], [5, 5]],
     [[4, 4], [4, 4], [4, 5], [5, 5]]],
    # Upper Arm 4
    [[[4, 4], [4, 4], [4, 5], [5, 5]],
     [[4, 4], [4, 4], [4, 5], [5, 5]],
     [[4, 4], [4, 5], [5, 5], [6, 6]]],
    # Upper Arm 5
    [[[5, 5], [5, 5], [5, 6], [6, 7]],
     [[5, 6], [6, 6], [6, 7], [7, 7]],
     [[6, 6], [6, 7], [7, 7], [7, 8]]],
    # Upper Arm 6
    [[[7, 7], [7, 7], [7, 8], [8, 9]],
     [[8, 8], [8, 8], [8, 9], [9, 9]],
     [[9, 9], [9, 9], [9, 9], [9, 9]]],
]

# RULA Table B: 목/몸통/다리 조합 → B그룹 점수
# [neck][trunk][legs]
RULA_TABLE_B = [
    # Neck 1
    [[1, 3], [2, 3], [3, 4], [5, 5], [6, 6], [7, 7]],
    # Neck 2
    [[2, 3], [2, 3], [4, 5], [5, 5], [6, 7], [7, 7]],
    # Neck 3
    [[3, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 7]],
    # Neck 4
    [[5, 5], [5, 6], [6, 7], [7, 7], [7, 7], [8, 8]],
    # Neck 5
    [[7, 7], [7, 7], [7, 8], [8, 8], [8, 8], [8, 8]],
    # Neck 6
    [[8, 8], [8, 8], [8, 8], [8, 9], [9, 9], [9, 9]],
]

# RULA Table C: A그룹/B그룹 → 최종 점수
RULA_TABLE_C = [
    [1, 2, 3, 3, 4, 5, 5],  # A=1
    [2, 2, 3, 4, 4, 5, 5],  # A=2
    [3, 3, 3, 4, 4, 5, 6],  # A=3
    [3, 3, 3, 4, 5, 6, 6],  # A=4
    [4, 4, 4, 5, 6, 7, 7],  # A=5
    [4, 4, 5, 6, 6, 7, 7],  # A=6
    [5, 5, 6, 6, 7, 7, 7],  # A=7
    [5, 5, 6, 7, 7, 7, 7],  # A=8
]

# =============================================================================
# REBA Tables
# =============================================================================

# REBA Table A: 목/몸통/다리 조합
# [neck][trunk][legs]
REBA_TABLE_A = [
    # Neck 1
    [[1, 2, 3, 4], [2, 3, 4, 5], [2, 4, 5, 6], [3, 5, 6, 7], [4, 6, 7, 8]],
    # Neck 2
    [[1, 2, 3, 4], [3, 4, 5, 6], [4, 5, 6, 7], [5, 6, 7, 8], [6, 7, 8, 9]],
    # Neck 3
    [[3, 3, 5, 6], [4, 5, 6, 7], [5, 6, 7, 8], [6, 7, 8, 9], [7, 8, 9, 9]],
]

# REBA Table B: 상완/전완/손목 조합
# [upper_arm][lower_arm][wrist]
REBA_TABLE_B = [
    # Upper Arm 1
    [[1, 2], [1, 2], [3, 4]],
    # Upper Arm 2
    [[1, 2], [2, 3], [4, 5]],
    # Upper Arm 3
    [[3, 4], [4, 5], [5, 6]],
    # Upper Arm 4
    [[4, 5], [5, 6], [7, 8]],
    # Upper Arm 5
    [[6, 7], [7, 8], [8, 9]],
    # Upper Arm 6
    [[7, 8], [8, 9], [9, 9]],
]

# REBA Table C: A그룹/B그룹 → 최종 점수
REBA_TABLE_C = [
    [1, 1, 1, 2, 3, 3, 4, 5, 6, 7, 7, 7],   # A=1
    [1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],   # A=2
    [2, 3, 3, 3, 4, 5, 6, 7, 7, 8, 8, 8],   # A=3
    [3, 4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9],   # A=4
    [4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9, 9],   # A=5
    [6, 6, 6, 7, 8, 8, 9, 9, 10, 10, 10, 10],  # A=6
    [7, 7, 7, 8, 9, 9, 9, 10, 10, 11, 11, 11],  # A=7
    [8, 8, 8, 9, 10, 10, 10, 10, 10, 11, 11, 11],  # A=8
    [9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12, 12],  # A=9
    [10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12],  # A=10
    [11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12],  # A=11
    [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12],  # A=12
]

# =============================================================================
# OWAS Action Category Table
# =============================================================================

# OWAS 조치 카테고리 테이블
# [back][arms][legs] → AC
OWAS_AC_TABLE: Dict[Tuple[int, int, int], int] = {
    # Back 1 (직립)
    (1, 1, 1): 1, (1, 1, 2): 1, (1, 1, 3): 1, (1, 1, 4): 1, (1, 1, 5): 1, (1, 1, 6): 1, (1, 1, 7): 1,
    (1, 2, 1): 1, (1, 2, 2): 1, (1, 2, 3): 1, (1, 2, 4): 1, (1, 2, 5): 1, (1, 2, 6): 1, (1, 2, 7): 1,
    (1, 3, 1): 1, (1, 3, 2): 1, (1, 3, 3): 1, (1, 3, 4): 1, (1, 3, 5): 1, (1, 3, 6): 1, (1, 3, 7): 1,
    # Back 2 (굴곡)
    (2, 1, 1): 2, (2, 1, 2): 2, (2, 1, 3): 2, (2, 1, 4): 2, (2, 1, 5): 2, (2, 1, 6): 2, (2, 1, 7): 2,
    (2, 2, 1): 2, (2, 2, 2): 2, (2, 2, 3): 2, (2, 2, 4): 2, (2, 2, 5): 2, (2, 2, 6): 2, (2, 2, 7): 2,
    (2, 3, 1): 2, (2, 3, 2): 2, (2, 3, 3): 2, (2, 3, 4): 2, (2, 3, 5): 2, (2, 3, 6): 3, (2, 3, 7): 3,
    # Back 3 (회전)
    (3, 1, 1): 1, (3, 1, 2): 1, (3, 1, 3): 1, (3, 1, 4): 1, (3, 1, 5): 1, (3, 1, 6): 2, (3, 1, 7): 2,
    (3, 2, 1): 2, (3, 2, 2): 2, (3, 2, 3): 2, (3, 2, 4): 2, (3, 2, 5): 2, (3, 2, 6): 2, (3, 2, 7): 2,
    (3, 3, 1): 2, (3, 3, 2): 2, (3, 3, 3): 3, (3, 3, 4): 3, (3, 3, 5): 3, (3, 3, 6): 3, (3, 3, 7): 3,
    # Back 4 (굴곡+회전)
    (4, 1, 1): 2, (4, 1, 2): 2, (4, 1, 3): 3, (4, 1, 4): 3, (4, 1, 5): 3, (4, 1, 6): 3, (4, 1, 7): 3,
    (4, 2, 1): 3, (4, 2, 2): 3, (4, 2, 3): 3, (4, 2, 4): 3, (4, 2, 5): 3, (4, 2, 6): 3, (4, 2, 7): 3,
    (4, 3, 1): 3, (4, 3, 2): 3, (4, 3, 3): 4, (4, 3, 4): 4, (4, 3, 5): 4, (4, 3, 6): 4, (4, 3, 7): 4,
}


# =============================================================================
# RULA Functions
# =============================================================================

def get_rula_table_a_score(upper_arm: int, lower_arm: int, wrist: int, wrist_twist: int) -> int:
    """
    RULA Table A에서 A그룹(상지) 점수 조회

    Args:
        upper_arm: 상완 점수 (1-6)
        lower_arm: 전완 점수 (1-3)
        wrist: 손목 점수 (1-4)
        wrist_twist: 손목 비틀림 점수 (1-2)

    Returns:
        A그룹 점수
    """
    ua = min(max(upper_arm - 1, 0), 5)
    la = min(max(lower_arm - 1, 0), 2)
    w = min(max(wrist - 1, 0), 3)
    wt = min(max(wrist_twist - 1, 0), 1)

    try:
        return RULA_TABLE_A[ua][la][w][wt]
    except IndexError:
        return 1


def get_rula_table_b_score(neck: int, trunk: int, leg: int) -> int:
    """
    RULA Table B에서 B그룹(목/몸통/다리) 점수 조회

    Args:
        neck: 목 점수 (1-6)
        trunk: 몸통 점수 (1-6)
        leg: 다리 점수 (1-2)

    Returns:
        B그룹 점수
    """
    n = min(max(neck - 1, 0), 5)
    t = min(max(trunk - 1, 0), 5)
    l = min(max(leg - 1, 0), 1)

    try:
        return RULA_TABLE_B[n][t][l]
    except IndexError:
        return 1


def get_rula_table_c_score(score_a: int, score_b: int) -> int:
    """
    RULA Table C에서 최종 점수 조회

    Args:
        score_a: A그룹 점수 (1-8+)
        score_b: B그룹 점수 (1-7+)

    Returns:
        최종 점수
    """
    a = min(max(score_a - 1, 0), 7)
    b = min(max(score_b - 1, 0), 6)

    try:
        return RULA_TABLE_C[a][b]
    except IndexError:
        return 1


def get_rula_risk_level(score: int) -> str:
    """
    RULA 점수에 따른 위험 수준 반환

    Args:
        score: RULA 최종 점수

    Returns:
        위험 수준 문자열
    """
    if score <= 2:
        return 'acceptable'
    elif score <= 4:
        return 'investigate'
    elif score <= 6:
        return 'change_soon'
    else:
        return 'change_now'


# =============================================================================
# REBA Functions
# =============================================================================

def get_reba_table_a_score(neck: int, trunk: int, leg: int) -> int:
    """
    REBA Table A에서 A그룹(목/몸통/다리) 점수 조회

    Args:
        neck: 목 점수 (1-3)
        trunk: 몸통 점수 (1-5)
        leg: 다리 점수 (1-4)

    Returns:
        A그룹 점수
    """
    n = min(max(neck - 1, 0), 2)
    t = min(max(trunk - 1, 0), 4)
    l = min(max(leg - 1, 0), 3)

    try:
        return REBA_TABLE_A[n][t][l]
    except IndexError:
        return 1


def get_reba_table_b_score(upper_arm: int, lower_arm: int, wrist: int) -> int:
    """
    REBA Table B에서 B그룹(상지) 점수 조회

    Args:
        upper_arm: 상완 점수 (1-6)
        lower_arm: 전완 점수 (1-2)
        wrist: 손목 점수 (1-3)

    Returns:
        B그룹 점수
    """
    ua = min(max(upper_arm - 1, 0), 5)
    la = min(max(lower_arm - 1, 0), 2)
    w = min(max(wrist - 1, 0), 1)

    try:
        return REBA_TABLE_B[ua][la][w]
    except IndexError:
        return 1


def get_reba_table_c_score(score_a: int, score_b: int) -> int:
    """
    REBA Table C에서 최종 점수 조회

    Args:
        score_a: A그룹 점수 (1-12+)
        score_b: B그룹 점수 (1-12+)

    Returns:
        최종 점수
    """
    a = min(max(score_a - 1, 0), 11)
    b = min(max(score_b - 1, 0), 11)

    try:
        return REBA_TABLE_C[a][b]
    except IndexError:
        return 1


def get_reba_risk_level(score: int) -> str:
    """
    REBA 점수에 따른 위험 수준 반환

    Args:
        score: REBA 최종 점수

    Returns:
        위험 수준 문자열
    """
    if score == 1:
        return 'negligible'
    elif score <= 3:
        return 'low'
    elif score <= 7:
        return 'medium'
    elif score <= 10:
        return 'high'
    else:
        return 'very_high'


# =============================================================================
# OWAS Functions
# =============================================================================

def get_owas_action_category(back: int, arms: int, legs: int) -> int:
    """
    OWAS 조치 카테고리(AC) 조회

    Args:
        back: 등 코드 (1-4)
        arms: 팔 코드 (1-3)
        legs: 다리 코드 (1-7)

    Returns:
        조치 카테고리 (1-4)
    """
    # 범위 제한
    b = min(max(back, 1), 4)
    a = min(max(arms, 1), 3)
    l = min(max(legs, 1), 7)

    return OWAS_AC_TABLE.get((b, a, l), 1)


def get_owas_risk_level(ac: int) -> str:
    """
    OWAS 조치 카테고리에 따른 위험 수준 반환

    Args:
        ac: 조치 카테고리 (1-4)

    Returns:
        위험 수준 문자열
    """
    if ac == 1:
        return 'normal'
    elif ac == 2:
        return 'slight'
    elif ac == 3:
        return 'harmful'
    else:
        return 'very_harmful'
