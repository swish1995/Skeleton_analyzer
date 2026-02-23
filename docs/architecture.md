# Skeleton Analyzer 아키텍처

> 📅 마지막 갱신: 2026-02-21
> 🔍 소스: 코드베이스 자동 분석

## 시스템 개요

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  MainWindow                                      │
├─────────────────────────────────┬───────────────────────────────────────────────┤
│       PlayerWidget              │              StatusWidget                      │
│  ┌─────────────────────────┐   │  ┌──────────────────┬──────────────────────┐  │
│  │  VideoPlayer / ImageSlide│   │  │  SkeletonWidget  │    AngleWidget       │  │
│  │     Player (OpenCV)     │   │  │                  │                      │  │
│  └─────────────────────────┘   │  └──────────────────┴──────────────────────┤  │
│                                 │  ┌────────────────────────────────────────┤  │
│                                 │  │          ErgonomicWidget               │  │
│                                 │  │  ┌────┬────┬────┬────┬────┐           │  │
│                                 │  │  │RULA│REBA│OWAS│NLE │ SI │           │  │
│                                 │  │  └────┴────┴────┴────┴────┘           │  │
│                                 │  ├────────────────────────────────────────┤  │
│                                 │  │     CaptureSpreadsheetWidget          │  │
│                                 │  └────────────────────────────────────────┘  │
└─────────────────────────────────┴───────────────────────────────────────────────┘
                │                                        │
                ▼                                        ▼
        ┌───────────────┐                        ┌───────────────┐
        │  VideoPlayer  │                        │ PoseDetector  │
        │   (Core)      │                        │  (MediaPipe)  │
        └───────────────┘                        └───────────────┘
        ┌───────────────┐
        │ImageSlidePlayer│
        │   (Core)      │
        └───────────────┘
                                                         │
                                                         ▼
                                                 ┌───────────────┐
                                                 │AngleCalculator│
                                                 └───────────────┘
                                                         │
                          ┌──────────┬──────────┬──────────┐
                          ▼          ▼          ▼          │
                   ┌──────────┐ ┌──────────┐ ┌──────────┐ │
                   │RULA Calc │ │REBA Calc │ │OWAS Calc │ │
                   └──────────┘ └──────────┘ └──────────┘ │
                                                          │
                    사용자 입력 ──────────────────────────┘
                          │
                          ├──────────────────┐
                          ▼                  ▼
                   ┌──────────────┐   ┌──────────────┐
                   │NLE Calculator│   │ SI Calculator│
                   └──────────────┘   └──────────────┘
```

## 레이어 구조

### UI Layer (`src/ui/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| MainWindow | `main_window.py` | 메인 윈도우, 메뉴, 툴바, 단축키 |
| PlayerWidget | `player_widget.py` | 영상 재생 컨트롤 |
| StatusWidget | `status_widget.py` | 스켈레톤 + 각도 + 안전지표 컨테이너 |
| SkeletonWidget | `skeleton_widget.py` | 스켈레톤 시각화 |
| AngleWidget | `angle_widget.py` | 관절 각도 표시 |
| CaptureSpreadsheetWidget | `capture_spreadsheet_widget.py` | 캡처 데이터 스프레드시트 + Excel 내보내기 |
| SettingsDialog | `settings_dialog.py` | 설정 다이얼로그 |
| HelpDialog | `help_dialog.py` | 도움말 다이얼로그 (프로그램 정보, 사용 방법) |

### UI Layer - Ergonomic (`src/ui/ergonomic/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| ErgonomicWidget | `ergonomic_widget.py` | 인체공학적 평가 통합 컨테이너 (5개 탭) |
| RULAWidget | `rula_widget.py` | RULA 평가 결과 표시 |
| REBAWidget | `reba_widget.py` | REBA 평가 결과 표시 |
| OWASWidget | `owas_widget.py` | OWAS 자세 코드 및 결과 표시 |
| NLEWidget | `nle_widget.py` | NLE 입력 및 결과 표시 |
| SIWidget | `si_widget.py` | SI 입력 및 결과 표시 |

### Core Layer (`src/core/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| VideoPlayer | `video_player.py` | OpenCV 영상 재생 |
| PoseDetector | `pose_detector.py` | MediaPipe 포즈 감지 |
| AngleCalculator | `angle_calculator.py` | 관절 각도 계산 |
| ProjectManager | `project_manager.py` | 프로젝트 저장/로드 |
| CaptureModel | `capture_model.py` | 캡처 데이터 모델 |
| ImageSlidePlayer | `image_slide_player.py` | 이미지 슬라이드 플레이어 (폴더/ZIP 로드) |
| Logger | `logger.py` | 로깅 유틸리티 |

### Core Layer - Ergonomic (`src/core/ergonomic/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| BaseAssessment | `base_assessment.py` | 인체공학적 평가 추상 기본 클래스 |
| RULACalculator | `rula_calculator.py` | RULA 점수 계산 (Table A/B/C) |
| REBACalculator | `reba_calculator.py` | REBA 점수 계산 (Table A/B/C) |
| OWASCalculator | `owas_calculator.py` | OWAS 자세 코드 및 조치 카테고리 계산 |
| NLECalculator | `nle_calculator.py` | NIOSH Lifting Equation 계산 (RWL/LI) |
| SICalculator | `si_calculator.py` | Strain Index 계산 |
| ScoreCalculator | `score_calculator.py` | 공통 점수 계산 함수 |

### Utils Layer (`src/utils/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| Config | `config.py` | 설정 관리 |
| ImageSaver | `image_saver.py` | 캡처 이미지 저장 |
| History | `history.py` | 작업 이력 관리 |
| ExcelFormulas | `excel_formulas.py` | Excel 수식 생성 (INDEX 함수) |
| ExcelTables | `excel_tables.py` | RULA/REBA/OWAS 조회 테이블 변환 |

### License Layer (`src/license/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| HardwareId | `hardware_id.py` | 크로스 플랫폼 하드웨어 ID 생성 |
| LicenseValidator | `license_validator.py` | 라이센스 키 형식/체크섬/하드웨어 검증 |
| LicenseManager | `license_manager.py` | 라이센스 상태 관리 (싱글톤) |
| LicenseDialog | `license_dialog.py` | 라이센스 등록 UI |

### UI Components (`src/ui/components/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| LicenseOverlay | `license_overlay.py` | 기능 제한 오버레이 표시 |

## 디렉토리 구조

```
skeleton-analyzer/
├── main.py                 # 앱 진입점
├── requirements.txt        # 의존성
├── pytest.ini             # 테스트 설정
├── skeleton_analyzer.spec  # PyInstaller 설정
├── .github/
│   └── workflows/
│       └── build-windows.yml  # 윈도우 빌드 CI/CD
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── video_player.py     # 영상 재생
│   │   ├── pose_detector.py    # 포즈 감지
│   │   ├── angle_calculator.py # 각도 계산
│   │   ├── project_manager.py  # 프로젝트 관리
│   │   ├── capture_model.py    # 캡처 모델
│   │   ├── image_slide_player.py # 이미지 슬라이드 플레이어
│   │   ├── logger.py           # 로깅
│   │   ├── score_calculator.py # 공통 점수 계산
│   │   └── ergonomic/          # 인체공학적 평가
│   │       ├── __init__.py
│   │       ├── base_assessment.py   # 기본 클래스
│   │       ├── rula_calculator.py   # RULA 계산
│   │       ├── reba_calculator.py   # REBA 계산
│   │       ├── owas_calculator.py   # OWAS 계산
│   │       ├── nle_calculator.py    # NLE 계산
│   │       └── si_calculator.py     # SI 계산
│   ├── ui/
│   │   ├── main_window.py      # 메인 윈도우
│   │   ├── player_widget.py    # 플레이어
│   │   ├── status_widget.py    # 상태 컨테이너
│   │   ├── skeleton_widget.py  # 스켈레톤
│   │   ├── angle_widget.py     # 각도 표시
│   │   ├── capture_spreadsheet_widget.py  # 스프레드시트 + Excel
│   │   ├── settings_dialog.py  # 설정
│   │   ├── help_dialog.py      # 도움말
│   │   └── ergonomic/          # 인체공학적 평가 UI
│   │       ├── __init__.py
│   │       ├── ergonomic_widget.py  # 통합 컨테이너
│   │       ├── rula_widget.py       # RULA 표시
│   │       ├── reba_widget.py       # REBA 표시
│   │       ├── owas_widget.py       # OWAS 표시
│   │       ├── nle_widget.py        # NLE 입력/표시
│   │       └── si_widget.py         # SI 입력/표시
│   ├── utils/
│   │   ├── config.py           # 설정
│   │   ├── image_saver.py      # 이미지 저장
│   │   ├── history.py          # 작업 이력
│   │   ├── excel_formulas.py   # Excel 수식 생성
│   │   └── excel_tables.py     # 조회 테이블 변환
│   ├── license/                # 라이센스 시스템
│   │   ├── hardware_id.py      # 하드웨어 ID 생성
│   │   ├── license_validator.py # 키 검증
│   │   ├── license_manager.py  # 상태 관리
│   │   └── license_dialog.py   # 등록 UI
│   └── resources/              # 리소스 파일
│       ├── icons/              # SVG 아이콘
│       └── help/               # HTML 도움말
├── tests/                  # 테스트 코드
│   └── license/            # 라이센스 시스템 테스트
├── tools/                  # 개발/관리 도구
│   └── license_keygen.py   # 라이센스 키 생성 도구
├── captures/               # 캡처 이미지 임시 저장
├── dev/                   # 개발 작업 관리
│   └── active/            # 진행 중 작업
└── docs/                   # 문서
    ├── README.md
    ├── architecture.md
    ├── usage.md
    ├── tech-stack.md
    ├── DEPLOYMENT.md
    └── ergonomic/          # 인체공학적 평가 문서
        ├── README.md
        ├── rula.md
        ├── reba.md
        ├── owas.md
        ├── nle.md
        └── si.md
```

## 데이터 흐름

```
1. 사용자가 동영상 파일 열기
   └── MainWindow._open_file()
       └── PlayerWidget.load_video()
           └── VideoPlayer.load()

2. 재생 버튼 클릭
   └── PlayerWidget.play()
       └── VideoPlayer.play()
       └── QTimer 시작

3. 타이머 콜백 (프레임마다)
   └── PlayerWidget._on_timer()
       └── VideoPlayer.read_frame()
       └── frame_changed 시그널 발생
           └── StatusWidget.process_frame()
               ├── PoseDetector.detect()
               │   └── 33개 랜드마크 반환
               ├── AngleCalculator.calculate_all_angles()
               │   └── 13개 관절 각도 계산
               ├── SkeletonWidget.set_landmarks()
               ├── AngleWidget.set_angles()
               └── ErgonomicWidget.update_assessment()
                   ├── RULACalculator.calculate()
                   │   └── RULAWidget.update_result()
                   ├── REBACalculator.calculate()
                   │   └── REBAWidget.update_result()
                   └── OWASCalculator.calculate()
                       └── OWASWidget.update_result()

4. 캡처 요청 (Enter 키)
   └── PlayerWidget.capture_requested 시그널
       └── MainWindow._on_capture_requested()
           └── StatusWidget.capture_current_state()
               └── CaptureSpreadsheetWidget.add_record()

5. 이미지 폴더/압축 파일 열기
   └── MainWindow._open_image_folder() / _open_archive_file()
       └── PlayerWidget.load_images() / load_archive()
           └── ImageSlidePlayer.load_folder() / load_archive()

6. 이미지 네비게이션
   └── PlayerWidget._on_next_image() / _on_prev_image()
       └── ImageSlidePlayer.next() / prev()
       └── frame_changed 시그널 발생
           └── (동영상과 동일한 흐름)
```

## 주요 클래스

### PoseDetector

```python
class PoseDetector:
    """MediaPipe 기반 인체 포즈 감지"""

    def detect(self, image: np.ndarray) -> PoseResult:
        """이미지에서 인체 포즈 감지"""
        # 33개 랜드마크 반환
```

### AngleCalculator

```python
class AngleCalculator:
    """관절 각도 계산"""

    ANGLE_DEFINITIONS = {
        'left_elbow': (11, 13, 15),   # 어깨-팔꿈치-손목
        'right_elbow': (12, 14, 16),
        'left_shoulder': (13, 11, 23),
        # ... 13개 관절
    }

    def calculate_all_angles(self, landmarks) -> dict:
        """모든 관절 각도 계산"""
```

### RULACalculator

```python
class RULACalculator(BaseAssessment):
    """RULA (Rapid Upper Limb Assessment) 점수 계산"""

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> RULAResult:
        """
        RULA 점수 계산

        - A그룹 (상지): 상완, 전완, 손목, 손목 비틀림
        - B그룹 (목/몸통): 목, 몸통, 다리
        - Table A/B/C로 최종 점수 산출 (1-7점)
        """
```

### REBACalculator

```python
class REBACalculator(BaseAssessment):
    """REBA (Rapid Entire Body Assessment) 점수 계산"""

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> REBAResult:
        """
        REBA 점수 계산

        - A그룹: 목, 몸통, 다리
        - B그룹 (상지): 상완, 전완, 손목
        - Table A/B/C로 최종 점수 산출 (1-12점)
        """
```

### OWASCalculator

```python
class OWASCalculator(BaseAssessment):
    """OWAS (Ovako Working Posture Analysis System) 점수 계산"""

    def calculate(self, angles: Dict[str, float], landmarks: List[Dict]) -> OWASResult:
        """
        OWAS 자세 코드 및 조치 카테고리 계산

        - 4자리 자세 코드: 등(1-4) / 팔(1-3) / 다리(1-7) / 하중(1-3)
        - 조치 카테고리: AC1-AC4
        """
```

## MediaPipe 랜드마크 (33개)

```
0: 코
1-10: 얼굴
11-12: 어깨
13-14: 팔꿈치
15-16: 손목
17-22: 손
23-24: 골반
25-26: 무릎
27-28: 발목
29-32: 발
```

## 인체공학적 평가 위험 수준

### RULA

| 점수 | 위험 수준 | 조치 |
|------|-----------|------|
| 1-2 | 허용 가능 | 현재 자세 유지 가능 |
| 3-4 | 추가 조사 필요 | 작업 자세 검토 필요 |
| 5-6 | 빠른 개선 필요 | 가까운 시일 내 개선 |
| 7 | 즉시 개선 필요 | 즉시 작업 자세 변경 |

### REBA

| 점수 | 위험 수준 | 조치 |
|------|-----------|------|
| 1 | 무시 가능 | 조치 불필요 |
| 2-3 | 낮음 | 개선 고려 |
| 4-7 | 중간 | 개선 필요 |
| 8-10 | 높음 | 빠른 개선 필요 |
| 11-12 | 매우 높음 | 즉시 개선 필요 |

### OWAS

| AC | 위험 수준 | 조치 |
|----|-----------|------|
| 1 | 정상 | 조치 불필요 |
| 2 | 약간 유해 | 가까운 시일 내 개선 |
| 3 | 명백히 유해 | 가능한 빨리 개선 |
| 4 | 매우 유해 | 즉시 개선 |

## CI/CD 파이프라인

### GitHub Actions 워크플로우

윈도우용 실행 파일 빌드를 위한 GitHub Actions 워크플로우가 구성되어 있습니다.

```
트리거:
├── 태그 푸시 (v*)     → Release 자동 생성
└── 수동 실행         → Artifact 생성

빌드 과정:
1. Windows 환경 (windows-latest)
2. Python 3.11 설정
3. 의존성 설치
4. MediaPipe 모델 다운로드
5. PyInstaller 빌드
6. 배포 (Release 또는 Artifact)
```

### 빌드 결과물

| 파일 | 설명 |
|------|------|
| `SkeletonAnalyzer.exe` | 윈도우용 단일 실행 파일 |

자세한 배포 방법은 [배포 가이드](./DEPLOYMENT.md)를 참조하세요.
