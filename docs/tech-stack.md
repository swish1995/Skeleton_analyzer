# IMAS 기술 스택

> 📅 마지막 갱신: 2026-02-01
> 🔍 소스: requirements.txt

## 런타임 의존성

| 패키지 | 버전 | 카테고리 | 용도 |
|--------|------|----------|------|
| PyQt6 | >=6.6.0 | GUI | 크로스 플랫폼 데스크톱 UI |
| PyQt6-WebEngine | >=6.6.0 | GUI | 도움말 HTML 렌더링 |
| opencv-python | >=4.8.0 | 영상처리 | 동영상 로드 및 프레임 처리 |
| mediapipe | >=0.10.0 | ML | 인체 포즈 감지 (33개 랜드마크) |
| numpy | >=1.24.0 | 수치계산 | 각도 계산, 벡터 연산 |
| markdown | >=3.5.0 | 문서처리 | 마크다운 파싱 |

## 개발 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| pytest | >=7.0.0 | 단위 테스트 |
| pytest-qt | >=4.2.0 | PyQt 위젯 테스트 |
| pytest-cov | >=4.0.0 | 테스트 커버리지 |
| pyinstaller | >=6.0.0 | exe/app 패키징 |

## 플랫폼별 의존성

| 패키지 | 버전 | 플랫폼 | 용도 |
|--------|------|--------|------|
| pyobjc-framework-Cocoa | >=11.0 | macOS | 네이티브 API 연동 |
| setproctitle | >=1.3.0 | macOS | 프로세스 이름 설정 |

## 기술 선택 이유

### PyQt6
- **선택 이유**: 크로스 플랫폼 지원 (Windows, macOS, Linux)
- **대안**: Tkinter (기능 제한), PySide6 (유사), Electron (무거움)

### OpenCV
- **선택 이유**: 영상 처리 업계 표준, Python 바인딩 우수
- **대안**: FFmpeg (저수준), MoviePy (기능 제한)

### MediaPipe
- **선택 이유**: Google 개발, 실시간 포즈 감지, 높은 정확도
- **대안**: OpenPose (무거움), YOLO-Pose (별도 학습 필요)

### NumPy
- **선택 이유**: 수치 계산 표준, 벡터/행렬 연산 최적화
- **대안**: 없음 (사실상 필수)

### PyQt6-WebEngine
- **선택 이유**: 도움말 HTML 콘텐츠 렌더링, Qt 통합
- **대안**: QTextBrowser (제한적), 외부 브라우저

### Markdown
- **선택 이유**: 도움말 마크다운 → HTML 변환
- **대안**: Python-Markdown2, mistune

## 시스템 요구사항

### 최소 사양
- Python 3.9+
- RAM 4GB
- CPU: 듀얼코어

### 권장 사양
- Python 3.10+
- RAM 8GB
- CPU: 쿼드코어
- GPU: 선택적 (CUDA 지원 시 가속)

## 지원 플랫폼

| 플랫폼 | 지원 | 비고 |
|--------|------|------|
| Windows 10/11 | ✅ | 주 타겟 |
| macOS 12+ | ✅ | Intel/Apple Silicon |
| Linux (Ubuntu 20.04+) | ✅ | X11/Wayland |

## 빌드 도구

```bash
# 개발 환경
python -m venv venv
pip install -r requirements.txt

# 테스트
pytest tests/ -v

# 패키징 (Windows)
pyinstaller skeleton_analyzer.spec

# 패키징 (macOS)
pyinstaller skeleton_analyzer.spec --windowed
```
