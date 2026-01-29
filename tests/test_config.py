"""Config 설정 관리 테스트"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import Config


class TestConfigDirectorySettings:
    """디렉토리 설정 테스트"""

    @pytest.fixture
    def temp_config(self, tmp_path, monkeypatch):
        """임시 설정 파일을 사용하는 Config"""
        # Config가 tmp_path를 설정 디렉토리로 사용하도록 설정
        config = Config(app_name="TestApp")
        # 설정 파일 경로를 tmp_path로 변경
        config._config_dir = tmp_path
        config._config_file = tmp_path / "config.json"
        config._config = {}
        return config

    def test_config_directory_video_open(self, temp_config):
        """동영상 열기 디렉토리 설정 테스트"""
        # Arrange
        config = temp_config

        # Act
        config.set("directories.video_open", "/path/to/videos")
        config.save()

        # Reload
        config2 = Config(app_name="TestApp")
        config2._config_dir = config._config_dir
        config2._config_file = config._config_file
        config2._load()

        # Assert
        assert config2.get("directories.video_open") == "/path/to/videos"

    def test_config_directory_capture_save(self, temp_config):
        """캡처 저장 디렉토리 설정 테스트"""
        # Arrange
        config = temp_config

        # Act
        config.set("directories.capture_save", "/path/to/captures")
        config.save()

        # Reload
        config2 = Config(app_name="TestApp")
        config2._config_dir = config._config_dir
        config2._config_file = config._config_file
        config2._load()

        # Assert
        assert config2.get("directories.capture_save") == "/path/to/captures"

    def test_config_directory_export(self, temp_config):
        """내보내기 디렉토리 설정 테스트"""
        # Arrange
        config = temp_config

        # Act
        config.set("directories.export", "/path/to/exports")
        config.save()

        # Reload
        config2 = Config(app_name="TestApp")
        config2._config_dir = config._config_dir
        config2._config_file = config._config_file
        config2._load()

        # Assert
        assert config2.get("directories.export") == "/path/to/exports"

    def test_config_directory_all_settings(self, temp_config):
        """모든 디렉토리 설정 동시 저장/로드"""
        # Arrange
        config = temp_config

        # Act
        config.set("directories.video_open", "/path/to/videos")
        config.set("directories.capture_save", "/path/to/captures")
        config.set("directories.export", "/path/to/exports")
        config.save()

        # Reload
        config2 = Config(app_name="TestApp")
        config2._config_dir = config._config_dir
        config2._config_file = config._config_file
        config2._load()

        # Assert
        assert config2.get("directories.video_open") == "/path/to/videos"
        assert config2.get("directories.capture_save") == "/path/to/captures"
        assert config2.get("directories.export") == "/path/to/exports"


class TestConfigDefaultValues:
    """설정 기본값 테스트"""

    @pytest.fixture
    def empty_config(self, tmp_path):
        """빈 설정 파일을 사용하는 Config"""
        config = Config(app_name="TestApp")
        config._config_dir = tmp_path
        config._config_file = tmp_path / "config.json"
        config._config = {}
        return config

    def test_config_default_video_open(self, empty_config):
        """동영상 열기 디렉토리 기본값"""
        assert empty_config.get("directories.video_open", "") == ""

    def test_config_default_capture_save(self, empty_config):
        """캡처 저장 디렉토리 기본값"""
        assert empty_config.get("directories.capture_save", "captures") == "captures"

    def test_config_default_export(self, empty_config):
        """내보내기 디렉토리 기본값"""
        assert empty_config.get("directories.export", "") == ""

    def test_config_nonexistent_key_returns_default(self, empty_config):
        """존재하지 않는 키는 기본값 반환"""
        assert empty_config.get("nonexistent.key", "default_value") == "default_value"
        assert empty_config.get("nonexistent.key") is None


class TestConfigImageSettings:
    """이미지 관리 설정 테스트"""

    @pytest.fixture
    def temp_config(self, tmp_path):
        """임시 설정 파일을 사용하는 Config"""
        config = Config(app_name="TestApp")
        config._config_dir = tmp_path
        config._config_file = tmp_path / "config.json"
        config._config = {}
        return config

    def test_config_auto_delete_on_row_delete(self, temp_config):
        """행 삭제 시 이미지 자동 삭제 설정"""
        # Arrange
        config = temp_config

        # Act
        config.set("images.auto_delete_on_row_delete", True)
        config.save()

        # Reload
        config2 = Config(app_name="TestApp")
        config2._config_dir = config._config_dir
        config2._config_file = config._config_file
        config2._load()

        # Assert
        assert config2.get("images.auto_delete_on_row_delete") is True

    def test_config_confirm_before_delete(self, temp_config):
        """이미지 삭제 전 확인 설정"""
        # Arrange
        config = temp_config

        # Act
        config.set("images.confirm_before_delete", False)
        config.save()

        # Reload
        config2 = Config(app_name="TestApp")
        config2._config_dir = config._config_dir
        config2._config_file = config._config_file
        config2._load()

        # Assert
        assert config2.get("images.confirm_before_delete") is False

    def test_config_image_settings_default_values(self, temp_config):
        """이미지 설정 기본값"""
        config = temp_config

        # 기본값 테스트
        assert config.get("images.auto_delete_on_row_delete", False) is False
        assert config.get("images.confirm_before_delete", True) is True

    def test_config_all_image_settings(self, temp_config):
        """모든 이미지 설정 동시 저장/로드"""
        # Arrange
        config = temp_config

        # Act
        config.set("images.auto_delete_on_row_delete", True)
        config.set("images.confirm_before_delete", False)
        config.save()

        # Reload
        config2 = Config(app_name="TestApp")
        config2._config_dir = config._config_dir
        config2._config_file = config._config_file
        config2._load()

        # Assert
        assert config2.get("images.auto_delete_on_row_delete") is True
        assert config2.get("images.confirm_before_delete") is False
