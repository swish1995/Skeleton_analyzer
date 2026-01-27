# Skeleton Analyzer 아키텍처

> 📅 마지막 갱신: 2026-01-27
> 🔍 소스: 코드베이스 자동 분석

## 시스템 개요

```
┌─────────────────────────────────────────────────────────────┐
│                      MainWindow                              │
├─────────────────────────────┬───────────────────────────────┤
│      PlayerWidget           │        StatusWidget           │
│  ┌───────────────────┐      │  ┌─────────────┬─────────────┤
│  │   VideoPlayer     │      │  │ SkeletonWidget│ AngleWidget│
│  │   (OpenCV)        │      │  │             │             │
│  └───────────────────┘      │  └─────────────┴─────────────┤
└─────────────────────────────┴───────────────────────────────┘
                │                           │
                ▼                           ▼
        ┌───────────────┐           ┌───────────────┐
        │  VideoPlayer  │           │ PoseDetector  │
        │   (Core)      │           │  (MediaPipe)  │
        └───────────────┘           └───────────────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │AngleCalculator│
                                    └───────────────┘
```

## 레이어 구조

### UI Layer (`src/ui/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| MainWindow | `main_window.py` | 메인 윈도우, 메뉴, 단축키 |
| PlayerWidget | `player_widget.py` | 영상 재생 컨트롤 |
| StatusWidget | `status_widget.py` | 스켈레톤 + 각도 컨테이너 |
| SkeletonWidget | `skeleton_widget.py` | 스켈레톤 시각화 |
| AngleWidget | `angle_widget.py` | 관절 각도 표시 |

### Core Layer (`src/core/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| VideoPlayer | `video_player.py` | OpenCV 영상 재생 |
| PoseDetector | `pose_detector.py` | MediaPipe 포즈 감지 |
| AngleCalculator | `angle_calculator.py` | 관절 각도 계산 |

### Utils Layer (`src/utils/`)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| Config | `config.py` | 설정 관리 |
| History | `history.py` | 최근 파일 이력 |

## 디렉토리 구조

```
skeleton-analyzer/
├── main.py                 # 앱 진입점
├── requirements.txt        # 의존성
├── pytest.ini             # 테스트 설정
├── skeleton_analyzer.spec # PyInstaller 설정
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── video_player.py     # 영상 재생
│   │   ├── pose_detector.py    # 포즈 감지
│   │   └── angle_calculator.py # 각도 계산
│   ├── ui/
│   │   ├── main_window.py      # 메인 윈도우
│   │   ├── player_widget.py    # 플레이어
│   │   ├── status_widget.py    # 상태 컨테이너
│   │   ├── skeleton_widget.py  # 스켈레톤
│   │   └── angle_widget.py     # 각도 표시
│   └── utils/
│       ├── config.py           # 설정
│       └── history.py          # 이력
├── tests/                  # 테스트 코드
├── resources/              # 리소스 파일
└── docs/                   # 문서
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
               └── PoseDetector.detect()
               └── AngleCalculator.calculate_all_angles()
               └── SkeletonWidget.set_landmarks()
               └── AngleWidget.set_angles()
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
