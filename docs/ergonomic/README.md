# 인체공학적 평가 (Ergonomic Assessment)

> 📅 마지막 갱신: 2026-01-30

## 개요

Skeleton Analyzer는 동영상에서 추출한 인체 자세를 기반으로 다섯 가지 국제 표준 인체공학적 평가 방법을 실시간으로 계산합니다:

### 자세 기반 평가 (실시간)
- **RULA** (Rapid Upper Limb Assessment) - 상지 중심 평가
- **REBA** (Rapid Entire Body Assessment) - 전신 평가
- **OWAS** (Ovako Working Posture Analysis System) - 작업 자세 분석

### 작업 기반 평가 (수동 입력)
- **NLE** (NIOSH Lifting Equation) - 들기 작업 위험도 평가
- **SI** (Strain Index) - 상지 반복 작업 위험도 평가

## 평가 방법 비교

| 항목 | RULA | REBA | OWAS | NLE | SI |
|------|------|------|------|-----|-----|
| **목적** | 상지 부하 평가 | 전신 부하 평가 | 자세 유해성 평가 | 들기 작업 위험 | 반복 작업 위험 |
| **개발** | McAtamney (1993) | Hignett (2000) | Karhu (1977) | NIOSH (1993) | Moore (1995) |
| **입력 방식** | 자동 (자세) | 자동 (자세) | 자동 (자세) | 수동 입력 | 수동 입력 |
| **점수 범위** | 1-7점 | 1-12점 | AC1-AC4 | LI (연속) | SI (연속) |
| **적용 상황** | 반복 상지 작업 | 전신 부하 작업 | 다양한 산업 | 물체 들기 | 상지 반복 작업 |

## 위험 수준 색상 코드

모든 평가 방법에서 동일한 색상 체계를 사용합니다:

| 색상 | 의미 | 코드 |
|------|------|------|
| 🟢 초록 | 안전 / 정상 | `#4CAF50` |
| 🟡 노랑 | 주의 / 조사 필요 | `#FFC107` |
| 🟠 주황 | 경고 / 개선 필요 | `#FF9800` |
| 🔴 빨강 | 위험 / 즉시 개선 | `#F44336` |

## 문서 목록

### 자세 기반 평가

| 문서 | 설명 |
|------|------|
| [RULA](./rula.md) | RULA 평가 방법 상세 |
| [REBA](./reba.md) | REBA 평가 방법 상세 |
| [OWAS](./owas.md) | OWAS 평가 방법 상세 |

### 작업 기반 평가

| 문서 | 설명 |
|------|------|
| [NLE](./nle.md) | NIOSH Lifting Equation - 들기 작업 위험도 |
| [SI](./si.md) | Strain Index - 상지 반복 작업 위험도 |

## 코드 구조

### Core 모듈 (`src/core/ergonomic/`)

```
ergonomic/
├── __init__.py           # 모듈 export
├── base_assessment.py    # 추상 기본 클래스
├── rula_calculator.py    # RULA 점수 계산
├── reba_calculator.py    # REBA 점수 계산
├── owas_calculator.py    # OWAS 점수 계산
├── nle_calculator.py     # NLE (NIOSH) 계산
└── si_calculator.py      # SI (Strain Index) 계산
```

### UI 모듈 (`src/ui/ergonomic/`)

```
ergonomic/
├── __init__.py           # 모듈 export
├── ergonomic_widget.py   # 통합 컨테이너 (탭 위젯)
├── rula_widget.py        # RULA 결과 표시
├── reba_widget.py        # REBA 결과 표시
├── owas_widget.py        # OWAS 결과 표시
├── nle_widget.py         # NLE 입력/결과 표시
└── si_widget.py          # SI 입력/결과 표시
```

## 데이터 흐름

### 자세 기반 평가 (자동)

```
PoseDetector.detect()
       │
       ▼
AngleCalculator.calculate_all_angles()
       │
       ├──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
RULACalculator      REBACalculator      OWASCalculator
       │                  │                  │
       ▼                  ▼                  ▼
  RULAResult         REBAResult         OWASResult
       │                  │                  │
       ▼                  ▼                  ▼
  RULAWidget         REBAWidget         OWASWidget
```

### 작업 기반 평가 (수동 입력)

```
사용자 입력 (UI)
       │
       ├──────────────────┐
       ▼                  ▼
  NLECalculator      SICalculator
       │                  │
       ▼                  ▼
   NLEResult          SIResult
       │                  │
       ▼                  ▼
   NLEWidget          SIWidget
```

## 사용 방법

1. 동영상을 로드하면 자동으로 인체 감지 및 평가가 시작됩니다
2. 안전지표 패널에서 RULA, REBA, OWAS 결과를 실시간으로 확인합니다
3. 원하는 시점에서 `Enter` 키를 눌러 현재 상태를 캡처합니다
4. 캡처된 데이터는 스프레드시트에 저장되어 분석에 활용할 수 있습니다

## 보기 옵션

| 단축키 | 기능 |
|--------|------|
| `Ctrl+1` | 상태 패널 (스켈레톤 + 각도) 토글 |
| `Ctrl+2` | 데이터 패널 (스프레드시트) 토글 |
| `Ctrl+3` | 안전지표 패널 (RULA/REBA/OWAS) 토글 |

개별 평가 방법(RULA, REBA, OWAS)은 툴바 버튼으로 토글할 수 있습니다.
