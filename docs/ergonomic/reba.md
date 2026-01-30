# REBA (Rapid Entire Body Assessment)

> 📅 마지막 갱신: 2026-01-30

## 개요

REBA는 Hignett과 McAtamney가 2000년에 개발한 전신 작업 부하 평가 도구입니다. RULA를 확장하여 전신(특히 하체)의 자세까지 포함하며, 의료/보건 분야에서 자주 사용됩니다.

## 평가 구조

REBA는 두 개의 그룹으로 나뉘어 평가합니다:

### A그룹 (목/몸통/다리)
- 목 (Neck): 1-3점
- 몸통 (Trunk): 1-5점
- 다리 (Legs): 1-4점

### B그룹 (상지)
- 상완 (Upper Arm): 1-6점
- 전완 (Lower Arm): 1-2점
- 손목 (Wrist): 1-3점

## 부위별 점수 기준

### 목 (Neck) - 1~3점

| 점수 | 자세 |
|------|------|
| 1 | 0°~20° 굴곡 |
| 2 | 20° 초과 굴곡 또는 신전 |
| +1 | 측굴 또는 회전 |

### 몸통 (Trunk) - 1~5점

| 점수 | 자세 |
|------|------|
| 1 | 직립 (0°~5° 굴곡) |
| 2 | 5°~20° 굴곡 |
| 3 | 20°~60° 굴곡 |
| 4 | 60° 초과 굴곡 |
| +1 | 측굴 또는 회전 |

### 다리 (Legs) - 1~4점

| 점수 | 자세 |
|------|------|
| 1 | 양다리 지지, 걷기/앉기 |
| 2 | 한 다리 지지 |
| +1 | 무릎 30°~60° 굴곡 |
| +2 | 무릎 60° 초과 굴곡 |

### 상완 (Upper Arm) - 1~6점

| 점수 | 자세 |
|------|------|
| 1 | 20° 굴곡 ~ 20° 신전 |
| 2 | 20° 초과 신전 또는 20°~45° 굴곡 |
| 3 | 45°~90° 굴곡 |
| 4 | 90° 초과 굴곡 |
| +1 | 외전 또는 어깨 올림 |
| -1 | 지지되어 있거나 기대어 있음 |

### 전완 (Lower Arm) - 1~2점

| 점수 | 자세 |
|------|------|
| 1 | 60°~100° 굴곡 |
| 2 | 60° 미만 또는 100° 초과 굴곡 |

### 손목 (Wrist) - 1~3점

| 점수 | 자세 |
|------|------|
| 1 | 0°~15° 굴곡/신전 |
| 2 | 15° 초과 굴곡/신전 |
| +1 | 측굴 또는 비틀림 |

## 점수 산출

### Table A (A그룹 점수)

목, 몸통, 다리 조합으로 A그룹 점수 산출 (1-9점)

### Table B (B그룹 점수)

상완, 전완, 손목 조합으로 B그룹 점수 산출 (1-9점)

### Table C (최종 점수)

A그룹 점수와 B그룹 점수 조합으로 최종 점수 산출 (1-12점)

## 위험 수준 및 조치

| 점수 | 위험 수준 | 색상 | 조치 |
|------|-----------|------|------|
| 1 | 무시 가능 (negligible) | 🟢 초록 | 조치 불필요 |
| 2-3 | 낮음 (low) | 🟢 연두 | 개선 고려 |
| 4-7 | 중간 (medium) | 🟡 노랑 | 개선 필요 |
| 8-10 | 높음 (high) | 🟠 주황 | 빠른 개선 필요 |
| 11-12 | 매우 높음 (very_high) | 🔴 빨강 | 즉시 개선 필요 |

## 코드 구조

### REBACalculator (`src/core/ergonomic/reba_calculator.py`)

```python
class REBACalculator(BaseAssessment):
    """REBA 점수 계산기"""

    # 점수 테이블
    TABLE_A = [...]  # [neck][trunk][legs]
    TABLE_B = [...]  # [upper_arm][lower_arm][wrist]
    TABLE_C = [...]  # [a_score][b_score]

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> REBAResult:
        """REBA 점수 계산"""
        # A그룹 점수 계산 (목/몸통/다리)
        neck = self._calculate_neck_score(angles, landmarks)
        trunk = self._calculate_trunk_score(angles, landmarks)
        leg = self._calculate_leg_score(angles, landmarks)

        # B그룹 점수 계산 (상지)
        upper_arm = self._calculate_upper_arm_score(angles, landmarks)
        lower_arm = self._calculate_lower_arm_score(angles)
        wrist = self._calculate_wrist_score(angles)

        # 테이블 조회
        group_a_score = self._get_table_a_score(...)
        group_b_score = self._get_table_b_score(...)
        final_score = self._get_table_c_score(...)

        return REBAResult(...)
```

### REBAResult (`src/core/ergonomic/reba_calculator.py`)

```python
@dataclass
class REBAResult(AssessmentResult):
    """REBA 평가 결과"""
    group_a_score: int = 0   # A그룹 점수 (목/몸통/다리)
    group_b_score: int = 0   # B그룹 점수 (상지)

    # 상세 점수
    neck_score: int = 0
    trunk_score: int = 0
    leg_score: int = 0
    upper_arm_score: int = 0
    lower_arm_score: int = 0
    wrist_score: int = 0
```

### REBAWidget (`src/ui/ergonomic/reba_widget.py`)

```python
class REBAWidget(QWidget):
    """REBA 평가 결과 표시 위젯"""

    # 색상 정의
    COLORS = {
        'negligible': '#4CAF50',    # 초록
        'low': '#8BC34A',           # 연두
        'medium': '#FFC107',        # 노랑
        'high': '#FF9800',          # 주황
        'very_high': '#F44336',     # 빨강
    }

    def update_result(self, result: REBAResult):
        """결과 업데이트"""
        # 최종 점수, 그룹 점수, 부위별 점수 표시
```

## RULA와의 차이점

| 항목 | RULA | REBA |
|------|------|------|
| 개발 연도 | 1993 | 2000 |
| 주요 평가 대상 | 상지 중심 | 전신 |
| A그룹 | 상지 | 목/몸통/다리 |
| B그룹 | 목/몸통 | 상지 |
| 최종 점수 범위 | 1-7 | 1-12 |
| 하체 평가 | 단순 (1-2점) | 상세 (1-4점) |

## 참고 문헌

- Hignett, S., & McAtamney, L. (2000). Rapid Entire Body Assessment (REBA). *Applied Ergonomics*, 31(2), 201-205.
