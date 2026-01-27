# Skeleton Analyzer 사용법

> 📅 마지막 갱신: 2026-01-27

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/swish1995/Safety_Doc.git
cd Safety_Doc
git checkout skeleton-analyzer
cd skeleton-analyzer
```

### 2. 가상환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (macOS/Linux)
source venv/bin/activate

# 활성화 (Windows)
venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 실행

```bash
python main.py
```

## 사용 방법

### 동영상 열기

1. **메뉴**: 파일 → 열기 (Cmd+O / Ctrl+O)
2. **버튼**: "파일 열기" 버튼 클릭
3. **드래그 앤 드롭**: 동영상 파일을 창에 드롭

### 지원 형식

- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)

### 재생 컨트롤

| 동작 | 방법 |
|------|------|
| 재생/일시정지 | Space 또는 ▶/⏸ 버튼 |
| 정지 | ■ 버튼 |
| 5초 뒤로 | ← 화살표 |
| 5초 앞으로 | → 화살표 |
| 위치 이동 | 시크바 드래그 |

## 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  [파일 열기]                                    메뉴바      │
├─────────────────────────────┬───────────────────────────────┤
│                             │                               │
│                             │      스켈레톤 시각화          │
│       동영상 재생           │                               │
│                             ├───────────────────────────────┤
│                             │                               │
│                             │      관절 각도 정보           │
│                             │                               │
├─────────────────────────────┴───────────────────────────────┤
│  [▶] [⏸] [■]  00:00 ══════════════════════════════ 05:30   │
└─────────────────────────────────────────────────────────────┘
```

### 왼쪽 패널: 동영상 플레이어
- 원본 동영상 재생
- 재생 컨트롤 (재생/일시정지/정지)
- 시크바 및 시간 표시

### 오른쪽 상단: 스켈레톤 시각화
- 감지된 인체 스켈레톤 표시
- 33개 랜드마크 연결선

### 오른쪽 하단: 관절 각도
- 13개 주요 관절 각도 표시
- 실시간 업데이트

## 감지되는 관절

| 관절 | 설명 |
|------|------|
| 목 (Neck) | 머리-목-척추 각도 |
| 왼쪽 어깨 | 팔꿈치-어깨-골반 |
| 오른쪽 어깨 | 팔꿈치-어깨-골반 |
| 왼쪽 팔꿈치 | 어깨-팔꿈치-손목 |
| 오른쪽 팔꿈치 | 어깨-팔꿈치-손목 |
| 왼쪽 골반 | 어깨-골반-무릎 |
| 오른쪽 골반 | 어깨-골반-무릎 |
| 왼쪽 무릎 | 골반-무릎-발목 |
| 오른쪽 무릎 | 골반-무릎-발목 |

## 문제 해결

### MediaPipe 모델 다운로드 오류

```bash
# 수동 다운로드
wget https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task
mv pose_landmarker_lite.task src/core/pose_landmarker.task
```

### PyQt6 설치 오류 (macOS)

```bash
pip install --upgrade pip
pip install PyQt6 --force-reinstall
```

### 영상 재생 안 됨

- 코덱 문제: FFmpeg 설치 필요
- 파일 손상: 다른 플레이어에서 재생 확인

## 개발자 가이드

### 테스트 실행

```bash
pytest tests/ -v
```

### 커버리지 확인

```bash
pytest tests/ --cov=src --cov-report=html
```

### 패키징

```bash
pyinstaller skeleton_analyzer.spec
# 결과: dist/skeleton_analyzer.app (macOS) 또는 dist/skeleton_analyzer.exe (Windows)
```
