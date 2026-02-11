# 움직임 빈도 분석 (Movement Frequency Analysis)

> 📅 마지막 갱신: 2026-02-10

## 개요

동영상 전체를 순차 스캔하여 신체 부위별 움직임 횟수와 고위험 자세 노출 비율을 자동으로 분석하는 기능입니다. 기존 실시간 캡처와 달리, 별도 `cv2.VideoCapture`를 사용하여 프레임 0부터 끝까지 독립적으로 분석합니다.

---

## 알고리즘

### 움직임 카운팅

연속된 분석 프레임 간 관절 각도 변화량(delta)을 비교하여 유의미한 움직임을 감지합니다.

```
delta = |angle[frame_n] - angle[frame_n-1]|

if delta > THRESHOLD:
    movement_count += 1
```

- **임계값**: 15° (기본값)
- 첫 프레임은 비교 대상이 없으므로 카운트하지 않음
- 샘플링 시에도 이전 **분석된** 프레임과 비교 (건너뛴 프레임 무시)

### 고위험 자세 집계

프레임별 RULA/REBA 부위 점수를 평가하여 고위험 프레임을 집계합니다.

| 평가 도구 | 고위험 기준 | 대상 부위 점수 |
|-----------|------------|---------------|
| RULA | 점수 ≥ 4 | upper_arm, lower_arm, wrist, neck, trunk |
| REBA | 점수 ≥ 4 | leg (RULA에 없는 부위만 추가) |

고위험 비율 = 고위험 프레임 수 / 총 분석 프레임 수

### 누적 위험 점수

움직임 빈도와 위험 수준을 결합한 복합 지표입니다.

```
cumulative_score = movement_count × avg_risk_score
```

- `avg_risk_score`: 해당 관절의 RULA 부위 점수 평균
- 움직임이 많으면서 위험 점수도 높은 부위가 상위에 위치

---

## 임계값 근거

### 움직임 감지 임계값 (15°)

| 출처 | 내용 |
|------|------|
| Peppoloni et al. (2020) | OCRA 빈도 요인 자동 계산 시 관절 각도 변화 15°를 유의미한 움직임으로 사용, 오차 5.7% 미만 |
| Mudiyanselage et al. (2024) | 관절 각도 변화 임계값 기반 자동 반복 동작 카운팅, 91.5% 정확도 달성 |

### 고위험 기준 (점수 ≥ 4)

- RULA/REBA 부위 점수 범위는 1~6
- 점수 4 이상은 "높은 위험" 또는 "즉시 개선 필요" 수준에 해당
- RULA 원저 (McAtamney & Corlett, 1993) 기반

### 감지 실패율 경고 (30%)

- 감지 실패 30% 초과 시 결과 신뢰도가 낮아짐
- MediaPipe Pose의 평균 감지 성공률(~95%)보다 현저히 낮은 경우 경고

---

## 데이터 구조

### BodyPartStats

13개 관절 각각에 대한 통계 데이터입니다.

```python
@dataclass
class BodyPartStats:
    joint_name: str           # 내부 식별자 (예: 'left_shoulder')
    display_name: str         # 한글 표시명 (예: '좌측 어깨')
    total_frames: int         # 분석된 프레임 수
    movement_count: int       # 움직임 횟수
    high_risk_frames: int     # 고위험 프레임 수
    high_risk_ratio: float    # 고위험 비율 (0.0~1.0)
    max_angle: float          # 최대 각도
    min_angle: float          # 최소 각도
    avg_angle: float          # 평균 각도
    cumulative_score: float   # 누적 위험 점수 (movement_count × avg_risk)
```

### MovementAnalysisResult

전체 분석 결과를 담는 컨테이너입니다.

```python
@dataclass
class MovementAnalysisResult:
    body_parts: Dict[str, BodyPartStats]  # 관절명 → 통계
    total_frames: int          # 전체 프레임 수
    analyzed_frames: int       # 포즈 감지 성공 프레임 수
    skipped_frames: int        # 포즈 감지 실패 프레임 수
    sample_interval: int       # 샘플링 간격 (1=전체, 2=매 2프레임, 3=매 3프레임)
    duration_seconds: float    # 분석 소요 시간
```

### 분석 대상 관절 (13개)

| 관절 | 식별자 | 표시명 |
|------|--------|--------|
| 목 | neck | 목 |
| 어깨 | left_shoulder / right_shoulder | 좌측/우측 어깨 |
| 팔꿈치 | left_elbow / right_elbow | 좌측/우측 팔꿈치 |
| 손목 | left_wrist / right_wrist | 좌측/우측 손목 |
| 엉덩이 | left_hip / right_hip | 좌측/우측 엉덩이 |
| 무릎 | left_knee / right_knee | 좌측/우측 무릎 |
| 발목 | left_ankle / right_ankle | 좌측/우측 발목 |

---

## 프레임 샘플링

긴 동영상의 분석 시간을 단축하기 위한 옵션입니다.

| 옵션 | sample_interval | 설명 |
|------|----------------|------|
| 전체 프레임 | 1 | 모든 프레임 분석 (가장 정확) |
| 매 2프레임 | 2 | 짝수 인덱스 프레임만 분석 (2배 빠름) |
| 매 3프레임 | 3 | 3의 배수 인덱스 프레임만 분석 (3배 빠름) |

- 샘플링 시에도 움직임 카운팅은 이전 **분석된** 프레임과 비교
- 건너뛴 프레임의 중간 움직임이 누락될 수 있어 결과가 다소 달라질 수 있음

---

## 모듈 구조

```
src/core/
├── movement_analyzer.py     # MovementAnalyzer, BodyPartStats, MovementAnalysisResult
└── analysis_worker.py       # AnalysisWorker (QThread)

src/ui/
├── movement_analysis_widget.py   # 3-상태 결과 탭 위젯
├── analysis_progress_dialog.py   # 분석 진행 모달 다이얼로그
└── bar_item_delegate.py          # 인라인 바 렌더링 델리게이트
```

### 실행 흐름

```
사용자 "분석 시작" 클릭
  → MovementAnalysisWidget.analysis_requested 시그널 emit
    → MainWindow._on_analysis_requested()
      → AnalysisProgressDialog (모달)
        → AnalysisWorker (QThread) 시작
          → cv2.VideoCapture로 프레임 순차 읽기
          → PoseDetector → AngleCalculator → RULACalculator/REBACalculator
          → MovementAnalyzer.update() 호출 (프레임별)
          → progress_updated 시그널 (진행률)
        → 완료: analysis_completed 시그널 (MovementAnalysisResult)
      → 모달 닫힘
    → MovementAnalysisWidget.set_result() 호출
    → "분석 결과" 탭으로 자동 전환
```

---

## 고위험 비율 색상 코드

| 색상 | 비율 범위 | 의미 |
|------|----------|------|
| 🔴 빨강 | ≥ 60% | 매우 위험 - 즉시 개선 필요 |
| 🟠 주황 | ≥ 40% | 위험 - 개선 권장 |
| 🟡 노랑 | ≥ 20% | 주의 - 모니터링 필요 |
| 🟢 초록 | < 20% | 양호 |

---

## 저장/복원

### 프로젝트 파일 (.skpx)

분석 결과는 `movement_analysis.json`으로 ZIP 내에 저장됩니다.

```
project.skpx
├── project.json
├── video.json
├── captures.json
├── ui_state.json
├── movement_analysis.json   ← 분석 결과
└── images/
```

### Excel 내보내기

"Movement Analysis" 시트에 부위별 통계 테이블이 포함됩니다.

- 행 1~6: 메타 정보 (분석 프레임 수, 실패 프레임, 샘플링 간격 등)
- 행 8~: 데이터 테이블 (부위, 관절명, 프레임 수, 움직임 횟수, 고위험 프레임/비율, 각도 통계, 누적 점수)

---

## 학술적 참조

1. **Occhipinti (1998)** - OCRA Index: 분당 기술적 동작 빈도 평가 (ISO 11228-3)
2. **Winkel & Mathiassen (1994)** - 노출의 3차원 모델: 수준 × 지속시간 × 빈도
3. **Mudiyanselage et al. (2024)** - 자동 반복 동작 카운팅 (관절 각도 기반, 91.5% 정확도)
4. **Peppoloni et al. (2020)** - OCRA 빈도 요인 자동 계산 (오차 5.7% 미만)
5. **McAtamney & Corlett (1993)** - RULA 원저
6. **Hignett & McAtamney (2000)** - REBA 원저
