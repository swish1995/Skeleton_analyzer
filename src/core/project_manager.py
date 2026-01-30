"""
프로젝트 매니저

프로젝트 상태를 ZIP 파일(.skpx)로 저장하고 로드하는 기능을 제공합니다.

ZIP 구조:
    project.skpx
    ├── project.json    # 메타데이터 (버전, 생성일 등)
    ├── video.json      # 동영상 정보 (절대 경로)
    ├── captures.json   # 캡처 데이터
    ├── ui_state.json   # UI 상태
    └── images/         # 캡처 이미지 파일들
"""

import json
import zipfile
import tempfile
import shutil
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Set

from .capture_model import CaptureDataModel, CaptureRecord


class LoadResult(Enum):
    """프로젝트 로드 결과"""
    FULL = "full"           # 완전 로드 성공
    PARTIAL = "partial"     # 동영상 없이 부분 로드
    CANCELLED = "cancelled" # 사용자 취소


@dataclass
class LoadInfo:
    """프로젝트 로드 정보"""
    result: LoadResult
    video_path: Optional[str] = None
    video_missing: bool = False
    capture_count: int = 0
    image_count: int = 0


class ProjectLoadError(Exception):
    """프로젝트 로드 오류"""
    pass


class ProjectManager:
    """프로젝트 저장/로드 관리자 (ZIP 형식)"""

    VERSION = "1.0"
    REQUIRED_FILES = ['project.json', 'video.json', 'captures.json', 'ui_state.json']

    def __init__(self):
        self._current_path: Optional[Path] = None
        self._is_dirty: bool = False

        # 상태 저장용
        self._video_path: Optional[str] = None
        self._frame_position: int = 0
        self._fps: float = 30.0
        self._capture_model: Optional[CaptureDataModel] = None
        self._ui_state: Dict[str, Any] = {}
        self._capture_dir: Optional[Path] = None

    # === 속성 ===

    @property
    def is_dirty(self) -> bool:
        """변경사항 있음 여부"""
        return self._is_dirty

    @property
    def current_path(self) -> Optional[Path]:
        """현재 프로젝트 경로"""
        return self._current_path

    @property
    def project_name(self) -> Optional[str]:
        """프로젝트 이름 (파일명에서 확장자 제외)"""
        if self._current_path:
            return self._current_path.stem
        return None

    # === 변경 추적 ===

    def mark_dirty(self) -> None:
        """변경사항 있음으로 표시"""
        self._is_dirty = True

    def mark_clean(self) -> None:
        """변경사항 없음으로 표시"""
        self._is_dirty = False

    # === 상태 관리 ===

    def set_state(
        self,
        video_path: Optional[str],
        frame_position: int,
        fps: float,
        capture_model: CaptureDataModel,
        ui_state: Dict[str, Any],
        capture_dir: Optional[Path] = None,
    ) -> None:
        """저장할 상태 설정"""
        self._video_path = video_path
        self._frame_position = frame_position
        self._fps = fps
        self._capture_model = capture_model
        self._ui_state = ui_state
        self._capture_dir = capture_dir

    def get_state(self) -> Dict[str, Any]:
        """현재 상태 반환"""
        return {
            'video_path': self._video_path,
            'frame_position': self._frame_position,
            'fps': self._fps,
            'capture_model': self._capture_model,
            'ui_state': self._ui_state,
        }

    # === 저장 ===

    def save(self, path: Optional[Path] = None) -> bool:
        """
        프로젝트를 ZIP 파일로 저장

        Args:
            path: 저장 경로. None이면 current_path 사용.

        Returns:
            성공 여부
        """
        if path is None:
            path = self._current_path
        if path is None:
            return False

        path = Path(path)

        try:
            # 임시 파일에 먼저 저장 (안전한 저장)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.skpx') as tmp:
                tmp_path = Path(tmp.name)

            self._write_zip(tmp_path)

            # 성공하면 원본 교체
            shutil.move(str(tmp_path), str(path))

            self._current_path = path
            self.mark_clean()
            return True

        except Exception as e:
            # 임시 파일 정리
            if 'tmp_path' in locals() and tmp_path.exists():
                tmp_path.unlink()
            raise

    def _write_zip(self, path: Path) -> None:
        """ZIP 파일 작성"""
        now = datetime.now().isoformat()

        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # project.json
            project_data = {
                'version': self.VERSION,
                'created_at': now,
                'modified_at': now,
                'app_version': '1.0.0',
            }
            zf.writestr('project.json', json.dumps(project_data, indent=2))

            # video.json
            video_data = {
                'path': self._video_path,
                'frame_position': self._frame_position,
                'fps': self._fps,
            }
            zf.writestr('video.json', json.dumps(video_data, indent=2))

            # captures.json
            if self._capture_model:
                base_path = self._capture_dir or Path('.')
                captures_data = self._capture_model.to_project_dict(base_path)
            else:
                captures_data = {'records': []}
            zf.writestr('captures.json', json.dumps(captures_data, indent=2, ensure_ascii=False))

            # ui_state.json
            zf.writestr('ui_state.json', json.dumps(self._ui_state, indent=2))

            # 이미지 복사
            if self._capture_model and self._capture_dir:
                self._copy_images_to_zip(zf)

    def _copy_images_to_zip(self, zf: zipfile.ZipFile) -> None:
        """캡처 이미지를 ZIP에 복사"""
        if not self._capture_model:
            return

        copied: Set[str] = set()

        for record in self._capture_model.get_all_records():
            for path_attr in ('video_frame_path', 'skeleton_image_path'):
                path = getattr(record, path_attr)
                if path and path not in copied:
                    img_path = Path(path)
                    if img_path.exists():
                        # 상대 경로로 저장
                        try:
                            rel_path = img_path.relative_to(self._capture_dir)
                            archive_path = f"images/{rel_path}"
                        except ValueError:
                            archive_path = f"images/{img_path.name}"

                        zf.write(str(img_path), archive_path)
                        copied.add(path)

    # === 로드 ===

    def load(
        self,
        path: Path,
        check_video: bool = True,
        load_video: bool = True,
        capture_dir: Optional[Path] = None,
    ) -> LoadInfo:
        """
        프로젝트 파일 로드

        Args:
            path: 프로젝트 파일 경로
            check_video: 동영상 파일 존재 여부 확인
            load_video: 동영상 정보 로드 여부 (False면 부분 로드)
            capture_dir: 이미지 추출 디렉토리

        Returns:
            LoadInfo 객체

        Raises:
            ProjectLoadError: 로드 실패 시
        """
        path = Path(path)

        if not path.exists():
            raise ProjectLoadError(f"파일을 찾을 수 없습니다: {path}")

        if not zipfile.is_zipfile(path):
            raise ProjectLoadError(f"유효한 프로젝트 파일이 아닙니다: {path}")

        try:
            with zipfile.ZipFile(path, 'r') as zf:
                # 필수 파일 확인
                self._validate_zip(zf)

                # 데이터 로드
                project_data = json.loads(zf.read('project.json'))
                video_data = json.loads(zf.read('video.json'))
                captures_data = json.loads(zf.read('captures.json'))
                ui_state = json.loads(zf.read('ui_state.json'))

                # 동영상 존재 확인
                video_path = video_data.get('path')
                video_missing = False
                if check_video and video_path:
                    video_missing = not Path(video_path).exists()

                # 캡처 디렉토리 설정
                if capture_dir is None:
                    capture_dir = path.parent / 'captures' / path.stem
                capture_dir.mkdir(parents=True, exist_ok=True)
                self._capture_dir = capture_dir

                # 이미지 추출
                image_count = self._extract_images(zf, capture_dir)

                # CaptureDataModel 복원
                capture_model = CaptureDataModel.from_project_dict(
                    captures_data,
                    base_path=capture_dir,
                )

                # 상태 설정
                self._video_path = video_path if load_video else None
                self._frame_position = video_data.get('frame_position', 0)
                self._fps = video_data.get('fps', 30.0)
                self._capture_model = capture_model
                self._ui_state = ui_state
                self._current_path = path
                self.mark_clean()

                # 결과 결정
                if video_missing and not load_video:
                    result = LoadResult.PARTIAL
                elif video_missing:
                    result = LoadResult.PARTIAL
                else:
                    result = LoadResult.FULL

                return LoadInfo(
                    result=result,
                    video_path=video_path,
                    video_missing=video_missing,
                    capture_count=len(capture_model),
                    image_count=image_count,
                )

        except zipfile.BadZipFile:
            raise ProjectLoadError(f"손상된 프로젝트 파일입니다: {path}")
        except json.JSONDecodeError as e:
            raise ProjectLoadError(f"프로젝트 파일을 읽을 수 없습니다: {e}")
        except KeyError as e:
            raise ProjectLoadError(f"프로젝트 파일에 필수 데이터가 없습니다: {e}")

    def _validate_zip(self, zf: zipfile.ZipFile) -> None:
        """ZIP 파일 유효성 검사"""
        names = zf.namelist()
        for required in self.REQUIRED_FILES:
            if required not in names:
                raise ProjectLoadError(f"필수 파일이 없습니다: {required}")

    def _extract_images(self, zf: zipfile.ZipFile, target_dir: Path) -> int:
        """이미지를 캡처 디렉토리로 추출"""
        count = 0
        for name in zf.namelist():
            if name.startswith('images/') and not name.endswith('/'):
                # images/ 접두사 제거
                relative_path = name[7:]  # 'images/' 제거
                target_path = target_dir / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)

                with zf.open(name) as src, open(target_path, 'wb') as dst:
                    dst.write(src.read())
                count += 1

        return count

    # === 새 프로젝트 ===

    def new_project(self) -> None:
        """새 프로젝트 시작 (상태 초기화)"""
        self._current_path = None
        self._is_dirty = False
        self._video_path = None
        self._frame_position = 0
        self._fps = 30.0
        self._capture_model = CaptureDataModel()
        self._ui_state = {}
        self._capture_dir = None
