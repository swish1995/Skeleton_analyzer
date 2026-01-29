"""ImageSaver 이미지 저장 유틸리티 테스트"""

import pytest
import numpy as np
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.image_saver import ImageSaver


class TestImageSaverFilename:
    """파일명 생성 테스트"""

    def test_generate_filename_format(self):
        """파일명 형식 확인 (5.123초 = 00:05.123)"""
        saver = ImageSaver()
        filename = saver.generate_filename(5.123, "frame")
        assert filename == "frame_00_05_123.png"

    def test_generate_filename_large_timestamp(self):
        """큰 타임스탬프 파일명 확인 (125.456초 = 02:05.456)"""
        saver = ImageSaver()
        filename = saver.generate_filename(125.456, "skeleton")
        assert filename == "skeleton_02_05_456.png"

    def test_generate_filename_zero(self):
        """0초 타임스탬프"""
        saver = ImageSaver()
        filename = saver.generate_filename(0.0, "frame")
        assert filename == "frame_00_00_000.png"

    def test_generate_filename_exact_second(self):
        """정확히 n초인 경우"""
        saver = ImageSaver()
        filename = saver.generate_filename(10.0, "frame")
        assert filename == "frame_00_10_000.png"


class TestImageSaverDirectory:
    """디렉토리 생성 테스트"""

    def test_ensure_capture_directory_creates_folder(self, tmp_path, monkeypatch):
        """저장 폴더 생성 확인"""
        monkeypatch.chdir(tmp_path)
        saver = ImageSaver()
        path = saver.ensure_capture_directory("test_video")
        assert Path(path).exists()
        assert Path(path).is_dir()

    def test_ensure_capture_directory_returns_correct_path(self, tmp_path, monkeypatch):
        """올바른 경로 반환 확인"""
        monkeypatch.chdir(tmp_path)
        saver = ImageSaver()
        path = saver.ensure_capture_directory("my_video")
        assert "captures" in path
        assert "my_video" in path

    def test_ensure_capture_directory_idempotent(self, tmp_path, monkeypatch):
        """이미 존재해도 에러 없이 동작"""
        monkeypatch.chdir(tmp_path)
        saver = ImageSaver()
        path1 = saver.ensure_capture_directory("test_video")
        path2 = saver.ensure_capture_directory("test_video")
        assert path1 == path2


class TestImageSaverSaveFrame:
    """프레임 저장 테스트"""

    @pytest.fixture
    def sample_frame(self):
        """테스트용 샘플 프레임 (BGR 형식)"""
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def test_save_frame_creates_file(self, tmp_path, sample_frame):
        """프레임 저장 시 파일 생성 확인"""
        saver = ImageSaver()
        path = str(tmp_path / "frame.png")
        result = saver.save_frame(sample_frame, path)
        assert result is True
        assert Path(path).exists()

    def test_save_frame_invalid_path_returns_false(self, sample_frame):
        """잘못된 경로 시 False 반환"""
        saver = ImageSaver()
        result = saver.save_frame(sample_frame, "/invalid/nonexistent/path/frame.png")
        assert result is False

    def test_save_frame_file_is_valid_image(self, tmp_path, sample_frame):
        """저장된 파일이 유효한 이미지인지 확인"""
        import cv2
        saver = ImageSaver()
        path = str(tmp_path / "frame.png")
        saver.save_frame(sample_frame, path)
        loaded = cv2.imread(path)
        assert loaded is not None
        assert loaded.shape == sample_frame.shape


class TestImageSaverSavePixmap:
    """QPixmap 저장 테스트"""

    @pytest.fixture
    def app(self):
        """QApplication fixture"""
        from PyQt6.QtWidgets import QApplication
        return QApplication.instance() or QApplication([])

    @pytest.fixture
    def sample_pixmap(self, app):
        """테스트용 샘플 QPixmap"""
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(100, 100)
        pixmap.fill()
        return pixmap

    def test_save_pixmap_creates_file(self, tmp_path, sample_pixmap):
        """QPixmap 저장 시 파일 생성 확인"""
        saver = ImageSaver()
        path = str(tmp_path / "skeleton.png")
        result = saver.save_pixmap(sample_pixmap, path)
        assert result is True
        assert Path(path).exists()

    def test_save_pixmap_invalid_path_returns_false(self, sample_pixmap):
        """잘못된 경로 시 False 반환"""
        saver = ImageSaver()
        result = saver.save_pixmap(sample_pixmap, "/invalid/nonexistent/path/skeleton.png")
        assert result is False


class TestImageSaverConfigIntegration:
    """ImageSaver Config 연동 테스트"""

    def test_image_saver_with_config(self, tmp_path):
        """Config에서 캡처 디렉토리 설정 연동"""
        from utils.config import Config

        # Arrange
        config = Config(app_name="TestApp")
        config._config_dir = tmp_path
        config._config_file = tmp_path / "config.json"
        config._config = {}
        config.set("directories.capture_save", str(tmp_path / "custom_captures"))

        # Act
        saver = ImageSaver(config=config)

        # Assert
        assert saver._base_dir == str(tmp_path / "custom_captures")

    def test_image_saver_default_base_dir(self):
        """Config 없을 때 기본 디렉토리 사용"""
        # Act
        saver = ImageSaver()

        # Assert
        assert saver._base_dir == "captures"

    def test_image_saver_config_without_capture_save(self, tmp_path):
        """Config에 capture_save 설정 없을 때 기본값 사용"""
        from utils.config import Config

        # Arrange
        config = Config(app_name="TestApp")
        config._config_dir = tmp_path
        config._config_file = tmp_path / "config.json"
        config._config = {}

        # Act
        saver = ImageSaver(config=config)

        # Assert
        assert saver._base_dir == "captures"


class TestImageSaverUniqueFilename:
    """파일명 중복 방지 테스트"""

    def test_generate_unique_filename_no_conflict(self, tmp_path):
        """충돌 없는 경우 원본 이름 반환"""
        # Arrange
        saver = ImageSaver(base_dir=str(tmp_path))
        video_dir = tmp_path / "test_video"
        video_dir.mkdir()

        # Act
        unique_name = saver.generate_unique_filename(
            dir_path=str(video_dir),
            base_name="frame_00_05_123.png"
        )

        # Assert
        assert unique_name == "frame_00_05_123.png"

    def test_generate_unique_filename_single_conflict(self, tmp_path):
        """파일 1개 존재 시 _1 추가"""
        # Arrange
        saver = ImageSaver(base_dir=str(tmp_path))
        video_dir = tmp_path / "test_video"
        video_dir.mkdir()

        # 기존 파일 생성
        (video_dir / "frame_00_05_123.png").touch()

        # Act
        unique_name = saver.generate_unique_filename(
            dir_path=str(video_dir),
            base_name="frame_00_05_123.png"
        )

        # Assert
        assert unique_name == "frame_00_05_123_1.png"

    def test_generate_unique_filename_multiple_conflicts(self, tmp_path):
        """여러 파일 존재 시 다음 시퀀스 번호"""
        # Arrange
        saver = ImageSaver(base_dir=str(tmp_path))
        video_dir = tmp_path / "test_video"
        video_dir.mkdir()

        # 기존 파일 생성
        (video_dir / "frame_00_05_123.png").touch()
        (video_dir / "frame_00_05_123_1.png").touch()

        # Act
        unique_name = saver.generate_unique_filename(
            dir_path=str(video_dir),
            base_name="frame_00_05_123.png"
        )

        # Assert
        assert unique_name == "frame_00_05_123_2.png"

    def test_save_capture_no_overwrite(self, tmp_path):
        """동일 타임스탬프 캡처 시 덮어쓰기 방지"""
        # Arrange
        saver = ImageSaver(base_dir=str(tmp_path))
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        # Act - 같은 타임스탬프로 2번 저장
        path1, _ = saver.save_capture("test_video", 5.123, frame=frame)
        path2, _ = saver.save_capture("test_video", 5.123, frame=frame)

        # Assert
        assert path1 != path2
        assert os.path.exists(path1)
        assert os.path.exists(path2)
        assert "_1" in path2
