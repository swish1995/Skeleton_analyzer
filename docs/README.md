# Skeleton Analyzer 문서

> 📅 마지막 갱신: 2026-01-29
> 🔍 소스: 코드베이스 자동 분석

## 프로젝트 개요

**Skeleton Analyzer**는 동영상에서 인체를 감지하여 스켈레톤을 실시간으로 추출하고, 각 관절의 각도를 분석하는 크로스 플랫폼 데스크톱 애플리케이션입니다.

## 주요 기능

- 동영상 파일 재생 및 제어
- MediaPipe 기반 실시간 인체 포즈 감지
- 33개 랜드마크 추출 및 시각화
- 13개 주요 관절 각도 계산
- 스켈레톤 오버레이 표시

## 문서 목록

| 문서 | 설명 |
|------|------|
| [아키텍처](./architecture.md) | 시스템 구조 및 컴포넌트 |
| [기술 스택](./tech-stack.md) | 사용 기술 및 의존성 |
| [사용법](./usage.md) | 설치 및 실행 가이드 |
| [배포 가이드](./DEPLOYMENT.md) | 윈도우 빌드 및 배포 방법 |

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

| 키 | 기능 |
|----|------|
| Space | 재생/일시정지 |
| ← | 5초 뒤로 |
| → | 5초 앞으로 |
| Cmd+O | 파일 열기 |
| Cmd+Q | 종료 |
