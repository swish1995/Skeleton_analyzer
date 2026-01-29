# Skeleton Analyzer 배포 가이드

## 개요

이 문서는 Skeleton Analyzer를 윈도우 사용자에게 배포하는 방법을 설명합니다.

GitHub Actions를 통해 윈도우용 실행 파일(.exe)을 자동으로 빌드하고 배포할 수 있습니다.

---

## 사전 준비

1. GitHub 저장소에 코드가 푸시되어 있어야 합니다
2. `.github/workflows/build-windows.yml` 워크플로우 파일이 있어야 합니다

---

## 배포 방법

### 방법 1: 태그를 통한 Release 배포 (권장)

정식 버전을 배포할 때 사용합니다. Releases 페이지에 영구 보관됩니다.

```bash
# 1. 변경사항 커밋 및 푸시
git add .
git commit -m "feat: 새 기능 추가"
git push origin main

# 2. 버전 태그 생성
git tag v1.0.0

# 3. 태그 푸시 (빌드 자동 시작)
git push origin v1.0.0
```

#### 버전 태그 규칙
- `v1.0.0` - 정식 릴리즈
- `v1.0.1` - 패치 버전
- `v1.1.0` - 마이너 업데이트
- `v2.0.0` - 메이저 업데이트

#### 다운로드 위치
```
https://github.com/{username}/{repo}/releases
```

---

### 방법 2: 수동 빌드 (테스트용)

개발 중 테스트 빌드가 필요할 때 사용합니다.

1. GitHub 저장소 접속
2. **Actions** 탭 클릭
3. 왼쪽 목록에서 **Build Windows Executable** 선택
4. **Run workflow** 버튼 클릭
5. 브랜치 선택 후 **Run workflow** 확인

#### 다운로드 위치
- Actions → 해당 워크플로우 실행 클릭 → 페이지 하단 **Artifacts** 섹션
- 보관 기간: 90일

---

## 빌드 과정

GitHub Actions가 자동으로 수행하는 작업:

1. Windows 환경에서 Python 3.11 설정
2. 의존성 패키지 설치 (`requirements.txt`)
3. MediaPipe 모델 파일 다운로드 (`pose_landmarker_lite.task`)
4. PyInstaller로 실행 파일 생성
5. Artifact 업로드 또는 Release 생성

---

## 배포 파일

| 파일명 | 설명 |
|--------|------|
| `SkeletonAnalyzer.exe` | 윈도우용 실행 파일 (단일 파일) |

---

## 사용자에게 배포하기

### Release 링크 공유
```
https://github.com/{username}/{repo}/releases/latest
```

### 직접 다운로드 링크
```
https://github.com/{username}/{repo}/releases/download/v1.0.0/SkeletonAnalyzer.exe
```

---

## 문제 해결

### 빌드 실패 시
1. Actions 탭에서 실패한 워크플로우 클릭
2. 빨간색으로 표시된 단계 확인
3. 로그에서 오류 메시지 확인

### 일반적인 오류
| 오류 | 원인 | 해결 방법 |
|------|------|----------|
| ModuleNotFoundError | 의존성 누락 | `requirements.txt` 확인 |
| Model download failed | 네트워크 오류 | 워크플로우 재실행 |
| PyInstaller error | spec 파일 오류 | `skeleton_analyzer.spec` 확인 |

---

## 로컬 빌드 (윈도우 환경)

윈도우 PC에서 직접 빌드하는 경우:

```powershell
# 1. 저장소 클론
git clone https://github.com/{username}/{repo}.git
cd skeleton-analyzer

# 2. 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 빌드
pyinstaller skeleton_analyzer.spec

# 5. 실행 파일 확인
dir dist\SkeletonAnalyzer.exe
```

빌드된 파일은 `dist/SkeletonAnalyzer.exe`에 생성됩니다.
