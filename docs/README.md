# Skeleton Analyzer 문서

> 📅 마지막 갱신: 2026-02-01
> 🔍 소스: 코드베이스 자동 분석

## 프로젝트 개요

**Skeleton Analyzer**는 동영상에서 인체를 감지하여 스켈레톤을 실시간으로 추출하고, 각 관절의 각도를 분석하며, 국제 표준 인체공학적 평가(RULA/REBA/OWAS)를 수행하는 크로스 플랫폼 데스크톱 애플리케이션입니다.

## 주요 기능

- 동영상 파일 재생 및 제어
- MediaPipe 기반 실시간 인체 포즈 감지
- 33개 랜드마크 추출 및 시각화
- 13개 주요 관절 각도 계산
- 스켈레톤 오버레이 표시
- **RULA/REBA/OWAS 인체공학적 평가** (실시간)
- **NLE/SI 작업 기반 평가** (수동 입력)
- 캡처 데이터 스프레드시트 저장
- **Excel 내보내기** (수식 포함)
- 프로젝트 저장/로드 (.skpx)
- **하드웨어 기반 라이센스 시스템**
- 도움말 시스템 (사용 방법, 프로그램 정보)

## 문서 목록

| 문서 | 설명 |
|------|------|
| [아키텍처](./architecture.md) | 시스템 구조 및 컴포넌트 |
| [기술 스택](./tech-stack.md) | 사용 기술 및 의존성 |
| [사용법](./usage.md) | 설치 및 실행 가이드 |
| [배포 가이드](./DEPLOYMENT.md) | 윈도우 빌드 및 배포 방법 |
| [라이센스 시스템](./license.md) | 라이센스 관리 및 기능 권한 |

### 인체공학적 평가 문서

| 문서 | 설명 |
|------|------|
| [인체공학적 평가 개요](./ergonomic/README.md) | 5가지 평가 방법 개요 및 비교 |
| [RULA](./ergonomic/rula.md) | Rapid Upper Limb Assessment |
| [REBA](./ergonomic/reba.md) | Rapid Entire Body Assessment |
| [OWAS](./ergonomic/owas.md) | Ovako Working Posture Analysis System |
| [NLE](./ergonomic/nle.md) | NIOSH Lifting Equation (들기 작업) |
| [SI](./ergonomic/si.md) | Strain Index (반복 작업) |

## 빠른 시작

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py
```

## 단축키

### 재생 제어

| 키 | 기능 |
|----|------|
| Space | 재생/일시정지 |
| ← | 5초 뒤로 |
| → | 5초 앞으로 |
| Enter | 현재 상태 캡처 |

### 파일/프로젝트

| 키 | 기능 |
|----|------|
| Ctrl+O | 동영상 파일 열기 |
| Ctrl+Shift+O | 프로젝트 열기 |
| Ctrl+N | 새 프로젝트 |
| Ctrl+S | 프로젝트 저장 |
| Ctrl+Shift+S | 다른 이름으로 저장 |
| Ctrl+Q | 종료 |

### 보기 (패널 토글)

| 키 | 기능 |
|----|------|
| Ctrl+1 | 상태 패널 (스켈레톤 + 각도) |
| Ctrl+2 | 데이터 패널 (스프레드시트) |
| Ctrl+3 | 안전지표 패널 (RULA/REBA/OWAS) |

> macOS에서는 `Ctrl` 대신 `Cmd(⌘)` 사용
