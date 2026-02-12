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
# [upper_arm 1-6][lower_arm 1-2][wrist 1-3]
REBA_TABLE_B = [
    # Upper Arm 1
    [[1, 2, 2], [1, 2, 3]],
    # Upper Arm 2
    [[1, 2, 3], [2, 3, 4]],
    # Upper Arm 3
    [[3, 4, 5], [4, 5, 5]],
    # Upper Arm 4
    [[4, 5, 5], [5, 6, 7]],
    # Upper Arm 5
    [[6, 7, 8], [7, 8, 8]],
    # Upper Arm 6
    [[7, 8, 8], [8, 9, 9]],
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
    la = min(max(lower_arm - 1, 0), 1)
    w = min(max(wrist - 1, 0), 2)

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


# =============================================================================
# NLE (NIOSH Lifting Equation) Tables and Functions
# =============================================================================

# LC (Load Constant) = 23 kg
NLE_LC = 23.0

# FM (Frequency Multiplier) Table
# FM_TABLE[frequency][duration_index][v_position]
# duration_index: 0=≤1hr, 1=1-2hr, 2=2-8hr
# v_position: 0=V<75cm, 1=V≥75cm
NLE_FM_TABLE = {
    0.2: [[1.00, 1.00], [0.95, 0.95], [0.85, 0.85]],
    0.5: [[0.97, 0.97], [0.92, 0.92], [0.81, 0.81]],
    1:   [[0.94, 0.94], [0.88, 0.88], [0.75, 0.75]],
    2:   [[0.91, 0.91], [0.84, 0.84], [0.65, 0.65]],
    3:   [[0.88, 0.88], [0.79, 0.79], [0.55, 0.55]],
    4:   [[0.84, 0.84], [0.72, 0.72], [0.45, 0.45]],
    5:   [[0.80, 0.80], [0.60, 0.60], [0.35, 0.35]],
    6:   [[0.75, 0.75], [0.50, 0.50], [0.27, 0.27]],
    7:   [[0.70, 0.70], [0.42, 0.42], [0.22, 0.22]],
    8:   [[0.60, 0.60], [0.35, 0.35], [0.18, 0.18]],
    9:   [[0.52, 0.52], [0.30, 0.30], [0.00, 0.15]],
    10:  [[0.45, 0.45], [0.26, 0.26], [0.00, 0.13]],
    11:  [[0.41, 0.41], [0.00, 0.23], [0.00, 0.00]],
    12:  [[0.37, 0.37], [0.00, 0.21], [0.00, 0.00]],
    13:  [[0.00, 0.34], [0.00, 0.00], [0.00, 0.00]],
    14:  [[0.00, 0.31], [0.00, 0.00], [0.00, 0.00]],
    15:  [[0.00, 0.28], [0.00, 0.00], [0.00, 0.00]],
}

# CM (Coupling Multiplier) Table
# CM_TABLE[coupling][v_position]
# coupling: 1=Good, 2=Fair, 3=Poor
# v_position: 0=V<75cm, 1=V≥75cm
NLE_CM_TABLE = {
    1: [1.00, 1.00],   # Good
    2: [0.95, 1.00],   # Fair
    3: [0.90, 0.90],   # Poor
}


def calculate_nle_hm(h: float) -> float:
    """
    HM (Horizontal Multiplier) 계산

    Args:
        h: 수평 거리 (cm)

    Returns:
        HM 값 (최대 1.0)
    """
    if h <= 0:
        return 0.0
    hm = 25.0 / h
    return min(hm, 1.0)


def calculate_nle_vm(v: float) -> float:
    """
    VM (Vertical Multiplier) 계산

    Args:
        v: 수직 높이 (cm)

    Returns:
        VM 값
    """
    vm = 1.0 - 0.003 * abs(v - 75.0)
    return max(vm, 0.0)


def calculate_nle_dm(d: float) -> float:
    """
    DM (Distance Multiplier) 계산

    Args:
        d: 이동 거리 (cm)

    Returns:
        DM 값 (최대 1.0)
    """
    if d <= 0:
        return 1.0
    dm = 0.82 + 4.5 / d
    return min(dm, 1.0)


def calculate_nle_am(a: float) -> float:
    """
    AM (Asymmetry Multiplier) 계산

    Args:
        a: 비틀림 각도 (°)

    Returns:
        AM 값 (최소 0.0)
    """
    am = 1.0 - 0.0032 * abs(a)
    return max(am, 0.0)


def calculate_nle_fm(frequency: float, duration_hours: float = 1.0, v: float = 75.0) -> float:
    """
    FM (Frequency Multiplier) 조회

    Args:
        frequency: 들기 빈도 (회/분)
        duration_hours: 작업 지속 시간 (시간)
        v: 수직 높이 (cm)

    Returns:
        FM 값
    """
    # Duration index
    if duration_hours <= 1:
        dur_idx = 0
    elif duration_hours <= 2:
        dur_idx = 1
    else:
        dur_idx = 2

    # V position index
    v_idx = 1 if v >= 75 else 0

    # 가장 가까운 frequency 키 찾기
    freq_keys = sorted(NLE_FM_TABLE.keys())
    closest_freq = min(freq_keys, key=lambda x: abs(x - frequency))

    return NLE_FM_TABLE[closest_freq][dur_idx][v_idx]


def calculate_nle_cm(coupling: int, v: float = 75.0) -> float:
    """
    CM (Coupling Multiplier) 조회

    Args:
        coupling: 커플링 등급 (1=Good, 2=Fair, 3=Poor)
        v: 수직 높이 (cm)

    Returns:
        CM 값
    """
    coupling = max(1, min(3, coupling))
    v_idx = 1 if v >= 75 else 0
    return NLE_CM_TABLE[coupling][v_idx]


def calculate_nle_rwl(
    h: float, v: float, d: float, a: float,
    frequency: float = 1.0, duration_hours: float = 1.0, coupling: int = 1
) -> float:
    """
    RWL (Recommended Weight Limit) 계산

    Args:
        h: 수평 거리 (cm)
        v: 수직 높이 (cm)
        d: 이동 거리 (cm)
        a: 비틀림 각도 (°)
        frequency: 들기 빈도 (회/분)
        duration_hours: 작업 지속 시간 (시간)
        coupling: 커플링 등급 (1=Good, 2=Fair, 3=Poor)

    Returns:
        RWL (kg)
    """
    hm = calculate_nle_hm(h)
    vm = calculate_nle_vm(v)
    dm = calculate_nle_dm(d)
    am = calculate_nle_am(a)
    fm = calculate_nle_fm(frequency, duration_hours, v)
    cm = calculate_nle_cm(coupling, v)

    rwl = NLE_LC * hm * vm * dm * am * fm * cm
    return rwl


def calculate_nle_li(load: float, rwl: float) -> float:
    """
    LI (Lifting Index) 계산

    Args:
        load: 실제 중량 (kg)
        rwl: 권장 중량 (kg)

    Returns:
        LI 값
    """
    if rwl <= 0:
        return 0.0 if load <= 0 else float('inf')
    return load / rwl


def get_nle_risk_level(li: float) -> str:
    """
    NLE 위험 수준 반환

    Args:
        li: Lifting Index

    Returns:
        위험 수준 문자열
    """
    if li <= 1.0:
        return 'safe'
    elif li <= 3.0:
        return 'increased'
    else:
        return 'high'


# =============================================================================
# SI (Strain Index) Tables and Functions
# =============================================================================

# SI Multiplier Tables
SI_MULTIPLIERS = {
    'ie': [1.0, 3.0, 6.0, 9.0, 13.0],     # Intensity of Exertion
    'de': [0.5, 1.0, 1.5, 2.0, 3.0],      # Duration of Exertion
    'em': [0.5, 1.0, 1.5, 2.0, 3.0],      # Efforts per Minute
    'hwp': [1.0, 1.0, 1.5, 2.0, 3.0],     # Hand/Wrist Posture
    'sw': [1.0, 1.0, 1.0, 1.5, 2.0],      # Speed of Work
    'dd': [0.25, 0.50, 0.75, 1.00, 1.50]  # Duration per Day
}


def get_si_multiplier(param: str, level: int) -> float:
    """
    SI Multiplier 값 조회

    Args:
        param: 파라미터 이름 ('ie', 'de', 'em', 'hwp', 'sw', 'dd')
        level: 레벨 (1-5)

    Returns:
        Multiplier 값
    """
    if param not in SI_MULTIPLIERS:
        return 1.0
    level = max(1, min(5, level))
    return SI_MULTIPLIERS[param][level - 1]


def calculate_si_score(
    ie: int = 1, de: int = 1, em: int = 1,
    hwp: int = 1, sw: int = 1, dd: int = 1
) -> float:
    """
    SI Score 계산

    Args:
        ie: Intensity of Exertion (1-5)
        de: Duration of Exertion (1-5)
        em: Efforts per Minute (1-5)
        hwp: Hand/Wrist Posture (1-5)
        sw: Speed of Work (1-5)
        dd: Duration per Day (1-5)

    Returns:
        SI Score
    """
    ie_m = get_si_multiplier('ie', ie)
    de_m = get_si_multiplier('de', de)
    em_m = get_si_multiplier('em', em)
    hwp_m = get_si_multiplier('hwp', hwp)
    sw_m = get_si_multiplier('sw', sw)
    dd_m = get_si_multiplier('dd', dd)

    return ie_m * de_m * em_m * hwp_m * sw_m * dd_m


def get_si_risk_level(score: float) -> str:
    """
    SI 위험 수준 반환

    Args:
        score: SI Score

    Returns:
        위험 수준 문자열
    """
    if score < 3:
        return 'safe'
    elif score < 7:
        return 'uncertain'
    else:
        return 'hazardous'
