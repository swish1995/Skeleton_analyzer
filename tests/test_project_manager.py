"""ProjectManager 테스트 (Phase 2)"""

import pytest
import json
import tempfile
import zipfile
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.project_manager import (
    ProjectManager,
    ProjectLoadError,
    LoadResult,
    LoadInfo,
)
from core.capture_model import CaptureRecord, CaptureDataModel


class TestProjectManagerBasic:
    """ProjectManager 기본 기능 테스트"""

    def test_project_manager_creation(self):
        """ProjectManager 인스턴스 생성"""
        pm = ProjectManager()
        assert pm is not None
        assert pm.current_path is None
        assert pm.is_dirty is False

    def test_project_name_without_path(self):
        """경로 없을 때 프로젝트 이름은 None"""
        pm = ProjectManager()
        assert pm.project_name is None

    def test_mark_dirty(self):
        """더티 플래그 설정"""
        pm = ProjectManager()
        assert pm.is_dirty is False
        pm.mark_dirty()
        assert pm.is_dirty is True

    def test_mark_clean(self):
        """더티 플래그 해제"""
        pm = ProjectManager()
        pm.mark_dirty()
        pm.mark_clean()
        assert pm.is_dirty is False


class TestProjectManagerSave:
    """ProjectManager 저장 기능 테스트"""

    def test_save_creates_zip_file(self, tmp_path):
        """save()가 ZIP 파일 생성"""
        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        # 최소한의 상태 설정
        pm.set_state(
            video_path="/path/to/video.mp4",
            frame_position=100,
            fps=30.0,
            capture_model=CaptureDataModel(),
            ui_state={},
        )

        result = pm.save(zip_path)

        assert result is True
        assert zip_path.exists()
        assert zipfile.is_zipfile(zip_path)

    def test_save_contains_required_files(self, tmp_path):
        """ZIP 파일에 필수 파일 포함"""
        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        pm.set_state(
            video_path="/path/to/video.mp4",
            frame_position=100,
            fps=30.0,
            capture_model=CaptureDataModel(),
            ui_state={},
        )
        pm.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            assert 'project.json' in names
            assert 'video.json' in names
            assert 'captures.json' in names
            assert 'ui_state.json' in names

    def test_save_project_json_content(self, tmp_path):
        """project.json 내용 검증"""
        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        pm.set_state(
            video_path="/path/to/video.mp4",
            frame_position=100,
            fps=30.0,
            capture_model=CaptureDataModel(),
            ui_state={},
        )
        pm.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            content = json.loads(zf.read('project.json'))
            assert 'version' in content
            assert content['version'] == '1.0'
            assert 'created_at' in content
            assert 'modified_at' in content

    def test_save_video_json_content(self, tmp_path):
        """video.json에 절대 경로 저장"""
        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"
        video_path = "/absolute/path/to/video.mp4"

        pm.set_state(
            video_path=video_path,
            frame_position=500,
            fps=29.97,
            capture_model=CaptureDataModel(),
            ui_state={},
        )
        pm.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            content = json.loads(zf.read('video.json'))
            assert content['path'] == video_path
            assert content['frame_position'] == 500
            assert content['fps'] == 29.97

    def test_save_with_captures(self, tmp_path):
        """캡처 데이터 저장"""
        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        model = CaptureDataModel()
        model.add_record(CaptureRecord(
            timestamp=5.0,
            frame_number=150,
            capture_time=datetime.now(),
            rula_score=4,
        ))

        pm.set_state(
            video_path="/path/to/video.mp4",
            frame_position=100,
            fps=30.0,
            capture_model=model,
            ui_state={},
        )
        pm.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            content = json.loads(zf.read('captures.json'))
            assert 'records' in content
            assert len(content['records']) == 1
            assert content['records'][0]['rula_score'] == 4

    def test_save_clears_dirty_flag(self, tmp_path):
        """저장 후 더티 플래그 해제"""
        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        pm.set_state(
            video_path="/path/to/video.mp4",
            frame_position=100,
            fps=30.0,
            capture_model=CaptureDataModel(),
            ui_state={},
        )
        pm.mark_dirty()
        pm.save(zip_path)

        assert pm.is_dirty is False

    def test_save_updates_current_path(self, tmp_path):
        """저장 후 current_path 업데이트"""
        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        pm.set_state(
            video_path="/path/to/video.mp4",
            frame_position=100,
            fps=30.0,
            capture_model=CaptureDataModel(),
            ui_state={},
        )
        pm.save(zip_path)

        assert pm.current_path == zip_path
        assert pm.project_name == "test_project"


class TestProjectManagerLoad:
    """ProjectManager 로드 기능 테스트"""

    def _create_test_project(self, tmp_path, video_path="/path/to/video.mp4"):
        """테스트용 프로젝트 파일 생성"""
        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        model = CaptureDataModel()
        model.add_record(CaptureRecord(
            timestamp=5.0,
            frame_number=150,
            capture_time=datetime.now(),
            rula_score=4,
        ))

        pm.set_state(
            video_path=video_path,
            frame_position=200,
            fps=30.0,
            capture_model=model,
            ui_state={'panels': {'angle': True}},
        )
        pm.save(zip_path)
        return zip_path

    def test_load_returns_load_info(self, tmp_path):
        """load()가 LoadInfo 반환"""
        zip_path = self._create_test_project(tmp_path)

        pm = ProjectManager()
        info = pm.load(zip_path)

        assert isinstance(info, LoadInfo)

    def test_load_restores_video_info(self, tmp_path):
        """로드 시 동영상 정보 복원"""
        zip_path = self._create_test_project(tmp_path, "/original/video.mp4")

        pm = ProjectManager()
        info = pm.load(zip_path)

        state = pm.get_state()
        assert state['video_path'] == "/original/video.mp4"
        assert state['frame_position'] == 200
        assert state['fps'] == 30.0

    def test_load_restores_captures(self, tmp_path):
        """로드 시 캡처 데이터 복원"""
        zip_path = self._create_test_project(tmp_path)

        pm = ProjectManager()
        pm.load(zip_path)

        state = pm.get_state()
        model = state['capture_model']
        assert len(model) == 1
        assert model.get_record(0).rula_score == 4

    def test_load_restores_ui_state(self, tmp_path):
        """로드 시 UI 상태 복원"""
        zip_path = self._create_test_project(tmp_path)

        pm = ProjectManager()
        pm.load(zip_path)

        state = pm.get_state()
        assert state['ui_state']['panels']['angle'] is True

    def test_load_invalid_file_raises_error(self, tmp_path):
        """잘못된 파일 로드 시 예외"""
        invalid_path = tmp_path / "not_a_zip.skpx"
        invalid_path.write_text("not a zip file")

        pm = ProjectManager()
        with pytest.raises(ProjectLoadError):
            pm.load(invalid_path)

    def test_load_missing_file_raises_error(self, tmp_path):
        """존재하지 않는 파일 로드 시 예외"""
        pm = ProjectManager()
        with pytest.raises(ProjectLoadError):
            pm.load(tmp_path / "nonexistent.skpx")

    def test_load_incomplete_zip_raises_error(self, tmp_path):
        """필수 파일 없는 ZIP 로드 시 예외"""
        zip_path = tmp_path / "incomplete.skpx"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('project.json', '{"version": "1.0"}')
            # video.json 누락

        pm = ProjectManager()
        with pytest.raises(ProjectLoadError):
            pm.load(zip_path)


class TestProjectManagerPartialLoad:
    """동영상 누락 시 부분 로드 테스트"""

    def _create_project_with_missing_video(self, tmp_path):
        """동영상이 존재하지 않는 프로젝트 생성"""
        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        model = CaptureDataModel()
        model.add_record(CaptureRecord(
            timestamp=5.0,
            frame_number=150,
            capture_time=datetime.now(),
        ))

        pm.set_state(
            video_path="/nonexistent/video.mp4",  # 존재하지 않는 경로
            frame_position=100,
            fps=30.0,
            capture_model=model,
            ui_state={},
        )
        pm.save(zip_path)
        return zip_path

    def test_load_detects_missing_video(self, tmp_path):
        """동영상 누락 감지"""
        zip_path = self._create_project_with_missing_video(tmp_path)

        pm = ProjectManager()
        info = pm.load(zip_path, check_video=True)

        assert info.video_missing is True

    def test_load_without_video_returns_partial(self, tmp_path):
        """동영상 없이 로드 시 PARTIAL 결과"""
        zip_path = self._create_project_with_missing_video(tmp_path)

        pm = ProjectManager()
        info = pm.load(zip_path, check_video=True, load_video=False)

        assert info.result == LoadResult.PARTIAL

    def test_partial_load_restores_captures(self, tmp_path):
        """부분 로드 시에도 캡처 데이터 복원"""
        zip_path = self._create_project_with_missing_video(tmp_path)

        pm = ProjectManager()
        pm.load(zip_path, check_video=True, load_video=False)

        state = pm.get_state()
        assert len(state['capture_model']) == 1

    def test_load_info_contains_counts(self, tmp_path):
        """LoadInfo에 캡처/이미지 개수 포함"""
        zip_path = self._create_project_with_missing_video(tmp_path)

        pm = ProjectManager()
        info = pm.load(zip_path)

        assert info.capture_count == 1


class TestProjectManagerNewProject:
    """새 프로젝트 기능 테스트"""

    def test_new_project_clears_state(self, tmp_path):
        """new_project()가 상태 초기화"""
        pm = ProjectManager()

        # 먼저 상태 설정
        pm.set_state(
            video_path="/path/to/video.mp4",
            frame_position=100,
            fps=30.0,
            capture_model=CaptureDataModel(),
            ui_state={},
        )
        pm.save(tmp_path / "test.skpx")

        # 새 프로젝트
        pm.new_project()

        assert pm.current_path is None
        assert pm.is_dirty is False
        state = pm.get_state()
        assert state['video_path'] is None


class TestProjectManagerImages:
    """이미지 처리 테스트"""

    def test_save_copies_images_to_zip(self, tmp_path):
        """저장 시 이미지를 ZIP에 복사"""
        # 테스트 이미지 생성
        img_dir = tmp_path / "captures" / "video"
        img_dir.mkdir(parents=True)
        (img_dir / "frame_00_05_000.png").write_bytes(b"fake image data")

        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        model = CaptureDataModel()
        model.add_record(CaptureRecord(
            timestamp=5.0,
            frame_number=150,
            capture_time=datetime.now(),
            video_frame_path=str(img_dir / "frame_00_05_000.png"),
        ))

        pm.set_state(
            video_path="/path/to/video.mp4",
            frame_position=100,
            fps=30.0,
            capture_model=model,
            ui_state={},
            capture_dir=tmp_path / "captures",
        )
        pm.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            assert any('images/' in name for name in names)

    def test_load_extracts_images(self, tmp_path):
        """로드 시 이미지를 캡처 디렉토리로 추출"""
        # 먼저 이미지가 포함된 프로젝트 생성
        img_dir = tmp_path / "captures" / "video"
        img_dir.mkdir(parents=True)
        img_file = img_dir / "frame_00_05_000.png"
        img_file.write_bytes(b"fake image data")

        pm = ProjectManager()
        zip_path = tmp_path / "test_project.skpx"

        model = CaptureDataModel()
        model.add_record(CaptureRecord(
            timestamp=5.0,
            frame_number=150,
            capture_time=datetime.now(),
            video_frame_path=str(img_file),
        ))

        pm.set_state(
            video_path="/path/to/video.mp4",
            frame_position=100,
            fps=30.0,
            capture_model=model,
            ui_state={},
            capture_dir=tmp_path / "captures",
        )
        pm.save(zip_path)

        # 원본 이미지 삭제
        img_file.unlink()
        assert not img_file.exists()

        # 다른 위치로 로드
        extract_dir = tmp_path / "extracted_captures"
        pm2 = ProjectManager()
        pm2.load(zip_path, capture_dir=extract_dir)

        # 이미지가 추출되었는지 확인
        state = pm2.get_state()
        record = state['capture_model'].get_record(0)
        assert record.video_frame_path is not None
        assert Path(record.video_frame_path).exists()
