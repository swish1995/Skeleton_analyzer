# RULA (Rapid Upper Limb Assessment)

> 📅 마지막 갱신: 2026-01-30

## 개요

RULA는 McAtamney와 Corlett가 1993년에 개발한 상지(Upper Limb) 작업 부하 평가 도구입니다. 반복적인 상지 작업이나 고정 자세 작업에서 발생할 수 있는 근골격계 질환(MSDs) 위험을 평가합니다.

## 평가 구조

RULA는 두 개의 그룹으로 나뉘어 평가합니다:

### A그룹 (상지)
- 상완 (Upper Arm): 1-6점
- 전완 (Lower Arm): 1-3점
- 손목 (Wrist): 1-4점
- 손목 비틀림 (Wrist Twist): 1-2점

### B그룹 (목/몸통)
- 목 (Neck): 1-6점
- 몸통 (Trunk): 1-6점
- 다리 (Legs): 1-2점

## 부위별 점수 기준

### 상완 (Upper Arm) - 1~6점

| 점수 | 자세 |
|------|------|
| 1 | 20° 굴곡 ~ 20° 신전 |
| 2 | 20° 이상 신전 또는 20°~45° 굴곡 |
| 3 | 45°~90° 굴곡 |
| 4 | 90° 이상 굴곡 |
| +1 | 어깨 올림 또는 상완 외전 |
| +1 | 팔 지지가 있는 경우 -1 |

### 전완 (Lower Arm) - 1~3점

| 점수 | 자세 |
|------|------|
| 1 | 60°~100° 굴곡 |
| 2 | 60° 미만 또는 100° 초과 굴곡 |
| +1 | 전완이 몸 중심선을 넘어 작업 |

### 손목 (Wrist) - 1~4점

| 점수 | 자세 |
|------|------|
| 1 | 중립 위치 (±5°) |
| 2 | 5°~15° 굴곡/신전 |
| 3 | 15° 초과 굴곡/신전 |
| +1 | 손목 측굴 |

### 손목 비틀림 (Wrist Twist) - 1~2점

| 점수 | 자세 |
|------|------|
| 1 | 회전 범위 중앙 |
| 2 | 회전 범위 끝 |

### 목 (Neck) - 1~6점

| 점수 | 자세 |
|------|------|
| 1 | 0°~10° 굴곡 |
| 2 | 10°~20° 굴곡 |
| 3 | 20° 이상 굴곡 |
| 4 | 신전 |
| +1 | 측굴 또는 회전 |

### 몸통 (Trunk) - 1~6점

| 점수 | 자세 |
|------|------|
| 1 | 0°~5° 굴곡 (직립) |
| 2 | 5°~20° 굴곡 |
| 3 | 20°~60° 굴곡 |
| 4 | 60° 이상 굴곡 |
| +1 | 측굴 또는 회전 |

### 다리 (Legs) - 1~2점

| 점수 | 자세 |
|------|------|
| 1 | 양다리로 균형 있게 서 있음 |
| 2 | 한 다리에 체중 실림 또는 앉아있음 |

## 점수 산출

### Table A (A그룹 점수)

상완, 전완, 손목, 손목 비틀림 조합으로 A그룹 점수 산출 (1-8점)

### Table B (B그룹 점수)

목, 몸통, 다리 조합으로 B그룹 점수 산출 (1-7점)

### Table C (최종 점수)

A그룹 점수와 B그룹 점수 조합으로 최종 점수 산출 (1-7점)

## 위험 수준 및 조치

| 점수 | 위험 수준 | 색상 | 조치 |
|------|-----------|------|------|
| 1-2 | 허용 가능 (acceptable) | 🟢 초록 | 현재 자세는 허용 가능한 수준입니다 |
| 3-4 | 추가 조사 필요 (investigate) | 🟡 노랑 | 작업 자세에 대한 추가 조사가 필요합니다 |
| 5-6 | 빠른 개선 필요 (change_soon) | 🟠 주황 | 가까운 시일 내에 작업 자세 개선이 필요합니다 |
| 7 | 즉시 개선 필요 (change_now) | 🔴 빨강 | 즉시 작업 자세를 변경해야 합니다 |

## 코드 구조

### RULACalculator (`src/core/ergonomic/rula_calculator.py`)

```python
class RULACalculator(BaseAssessment):
    """RULA 점수 계산기"""

    # 점수 테이블
    TABLE_A = [...]  # [upper_arm][lower_arm][wrist][wrist_twist]
    TABLE_B = [...]  # [neck][trunk][legs]
    TABLE_C = [...]  # [a_score][b_score]

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> RULAResult:
        """RULA 점수 계산"""
        # 부위별 점수 계산
        upper_arm = self._calculate_upper_arm_score(angles, landmarks)
        lower_arm = self._calculate_lower_arm_score(angles)
        wrist = self._calculate_wrist_score(angles)
        wrist_twist = self._calculate_wrist_twist_score(angles)
        neck = self._calculate_neck_score(angles, landmarks)
        trunk = self._calculate_trunk_score(angles, landmarks)
        leg = self._calculate_leg_score(angles, landmarks)

        # 테이블 조회
        arm_wrist_score = self._get_table_a_score(...)
        neck_trunk_score = self._get_table_b_score(...)
        final_score = self._get_table_c_score(...)

        return RULAResult(...)
```

### RULAResult (`src/core/ergonomic/rula_calculator.py`)

```python
@dataclass
class RULAResult(AssessmentResult):
    """RULA 평가 결과"""
    arm_wrist_score: int = 0      # A그룹 점수
    neck_trunk_score: int = 0     # B그룹 점수

    # 상세 점수
    upper_arm_score: int = 0
    lower_arm_score: int = 0
    wrist_score: int = 0
    wrist_twist_score: int = 0
    neck_score: int = 0
    trunk_score: int = 0
    leg_score: int = 0
```

### RULAWidget (`src/ui/ergonomic/rula_widget.py`)

```python
class RULAWidget(QWidget):
    """RULA 평가 결과 표시 위젯"""

    # 색상 정의
    COLORS = {
        'acceptable': '#4CAF50',      # 초록
        'investigate': '#FFC107',      # 노랑
        'change_soon': '#FF9800',      # 주황
        'change_now': '#F44336',       # 빨강
    }

    def update_result(self, result: RULAResult):
        """결과 업데이트"""
        # 최종 점수, 그룹 점수, 부위별 점수 표시
```

## 참고 문헌

- McAtamney, L., & Corlett, E. N. (1993). RULA: a survey method for the investigation of work-related upper limb disorders. *Applied Ergonomics*, 24(2), 91-99.
