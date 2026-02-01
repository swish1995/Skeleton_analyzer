"""라이센스 매니저 테스트

TDD Red Phase - 실패하는 테스트 먼저 작성
"""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
import json
import os


@pytest.fixture
def reset_license_manager():
    """LicenseManager 상태 초기화"""
    from src.license.license_manager import LicenseManager
    LicenseManager._reset_for_testing()
    yield
    LicenseManager._reset_for_testing()


@pytest.fixture
def mock_hardware_id():
    """하드웨어 ID 모킹"""
    with patch('src.license.license_manager.get_hardware_id') as mock:
        mock.return_value = "TESTHARDWARE01"
        yield mock


@pytest.fixture
def temp_config_dir(tmp_path):
    """임시 설정 디렉토리"""
    config_dir = tmp_path / "SkeletonAnalyzer"
    config_dir.mkdir()
    with patch('src.license.license_manager.LicenseManager._get_config_path') as mock:
        mock.return_value = config_dir / "license.json"
        yield config_dir


class TestSingleton:
    """싱글톤 패턴 테스트"""

    def test_singleton_instance(self, reset_license_manager):
        """인스턴스가 하나만 존재"""
        from src.license.license_manager import LicenseManager

        instance1 = LicenseManager.instance()
        instance2 = LicenseManager.instance()

        assert instance1 is instance2


class TestInitialState:
    """초기 상태 테스트"""

    def test_initial_state_unlicensed(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """초기 상태는 미등록"""
        from src.license.license_manager import LicenseManager

        manager = LicenseManager.instance()

        assert manager.is_licensed is False

    def test_initial_mode_free(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """초기 모드는 free"""
        from src.license.license_manager import LicenseManager, LicenseMode

        manager = LicenseManager.instance()

        assert manager.license_mode == LicenseMode.FREE


class TestRegister:
    """등록 테스트"""

    def test_register_valid_key(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """유효한 키로 등록 → 성공"""
        from src.license.license_manager import LicenseManager
        from src.license.license_validator import LicenseValidator

        manager = LicenseManager.instance()
        validator = LicenseValidator()
        valid_key = validator.generate_test_key("TESTHARDWARE01")

        result = manager.register(valid_key)

        assert result is True
        assert manager.is_licensed is True

    def test_register_invalid_key(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """무효한 키로 등록 → 실패"""
        from src.license.license_manager import LicenseManager

        manager = LicenseManager.instance()

        result = manager.register("INVALID-KEY-1234-5678")

        assert result is False
        assert manager.is_licensed is False

    def test_register_wrong_hardware(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """다른 하드웨어용 키로 등록 → 실패"""
        from src.license.license_manager import LicenseManager
        from src.license.license_validator import LicenseValidator

        manager = LicenseManager.instance()
        validator = LicenseValidator()
        # 다른 하드웨어 ID로 생성된 키
        wrong_key = validator.generate_test_key("OTHERHARDWARE")

        result = manager.register(wrong_key)

        assert result is False

    def test_unregister(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """등록 해제 → 미등록 상태"""
        from src.license.license_manager import LicenseManager
        from src.license.license_validator import LicenseValidator

        manager = LicenseManager.instance()
        validator = LicenseValidator()
        valid_key = validator.generate_test_key("TESTHARDWARE01")
        manager.register(valid_key)

        manager.unregister()

        assert manager.is_licensed is False


class TestFeatureCheck:
    """기능 권한 테스트"""

    def test_check_feature_unlicensed(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """미등록 상태에서 제한 기능 → False"""
        from src.license.license_manager import LicenseManager

        manager = LicenseManager.instance()

        assert manager.check_feature('excel_export') is False
        assert manager.check_feature('project_save') is False
        assert manager.check_feature('nle_analysis') is False
        assert manager.check_feature('si_analysis') is False

    def test_check_feature_licensed(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """등록 상태에서 제한 기능 → True"""
        from src.license.license_manager import LicenseManager
        from src.license.license_validator import LicenseValidator

        manager = LicenseManager.instance()
        validator = LicenseValidator()
        valid_key = validator.generate_test_key("TESTHARDWARE01")
        manager.register(valid_key)

        assert manager.check_feature('excel_export') is True
        assert manager.check_feature('project_save') is True
        assert manager.check_feature('nle_analysis') is True
        assert manager.check_feature('si_analysis') is True

    def test_check_feature_free_features(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """무료 기능은 항상 True"""
        from src.license.license_manager import LicenseManager

        manager = LicenseManager.instance()

        assert manager.check_feature('video_load') is True
        assert manager.check_feature('rula_analysis') is True
        assert manager.check_feature('reba_analysis') is True
        assert manager.check_feature('owas_analysis') is True

    def test_check_unknown_feature(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """알 수 없는 기능 → False"""
        from src.license.license_manager import LicenseManager

        manager = LicenseManager.instance()

        assert manager.check_feature('unknown_feature') is False


class TestDevMode:
    """개발 모드 테스트"""

    def test_dev_mode_all_features(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """개발 모드에서 모든 기능 True"""
        from src.license.license_manager import LicenseManager, LicenseMode

        manager = LicenseManager.instance()
        manager.set_mode(LicenseMode.DEV)

        assert manager.check_feature('excel_export') is True
        assert manager.check_feature('nle_analysis') is True
        assert manager.check_feature('unknown_feature') is True

    def test_licensed_mode_all_features(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """강제 등록 모드에서 모든 기능 True"""
        from src.license.license_manager import LicenseManager, LicenseMode

        manager = LicenseManager.instance()
        manager.set_mode(LicenseMode.LICENSED)

        assert manager.check_feature('excel_export') is True
        assert manager.check_feature('nle_analysis') is True

    def test_mode_from_environment(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """환경변수에서 모드 읽기"""
        from src.license.license_manager import LicenseManager, LicenseMode

        with patch.dict(os.environ, {'SKELETON_ANALYZER_LICENSE_MODE': 'dev'}):
            LicenseManager._reset_for_testing()
            manager = LicenseManager.instance()

            assert manager.license_mode == LicenseMode.DEV


class TestPersistence:
    """저장/로드 테스트"""

    def test_save_license(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """라이센스 정보 저장"""
        from src.license.license_manager import LicenseManager
        from src.license.license_validator import LicenseValidator

        manager = LicenseManager.instance()
        validator = LicenseValidator()
        valid_key = validator.generate_test_key("TESTHARDWARE01")
        manager.register(valid_key)

        # 설정 파일이 생성되었는지 확인
        config_path = temp_config_dir / "license.json"
        assert config_path.exists()

    def test_load_license(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """저장된 라이센스 로드"""
        from src.license.license_manager import LicenseManager
        from src.license.license_validator import LicenseValidator

        # 먼저 등록
        manager = LicenseManager.instance()
        validator = LicenseValidator()
        valid_key = validator.generate_test_key("TESTHARDWARE01")
        manager.register(valid_key)

        # 매니저 리셋 후 다시 로드
        LicenseManager._reset_for_testing()
        manager = LicenseManager.instance()

        assert manager.is_licensed is True

    def test_load_tampered_license(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """변조된 설정 파일 → 로드 실패"""
        from src.license.license_manager import LicenseManager
        from src.license.license_validator import LicenseValidator

        # 등록
        manager = LicenseManager.instance()
        validator = LicenseValidator()
        valid_key = validator.generate_test_key("TESTHARDWARE01")
        manager.register(valid_key)

        # 설정 파일 변조
        config_path = temp_config_dir / "license.json"
        with open(config_path, 'w') as f:
            json.dump({"license_key": "TAMPERED-KEY", "checksum": "invalid"}, f)

        # 리셋 후 로드 시도
        LicenseManager._reset_for_testing()
        manager = LicenseManager.instance()

        assert manager.is_licensed is False


class TestSignal:
    """시그널 테스트"""

    def test_register_emits_signal(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """등록 시 license_changed 시그널 발생"""
        from src.license.license_manager import LicenseManager
        from src.license.license_validator import LicenseValidator

        manager = LicenseManager.instance()
        validator = LicenseValidator()
        valid_key = validator.generate_test_key("TESTHARDWARE01")

        # 시그널 수신 확인
        signal_received = []
        manager.license_changed.connect(lambda: signal_received.append(True))

        manager.register(valid_key)

        assert len(signal_received) == 1

    def test_unregister_emits_signal(self, reset_license_manager, mock_hardware_id, temp_config_dir):
        """등록 해제 시 license_changed 시그널 발생"""
        from src.license.license_manager import LicenseManager
        from src.license.license_validator import LicenseValidator

        manager = LicenseManager.instance()
        validator = LicenseValidator()
        valid_key = validator.generate_test_key("TESTHARDWARE01")
        manager.register(valid_key)

        signal_received = []
        manager.license_changed.connect(lambda: signal_received.append(True))

        manager.unregister()

        assert len(signal_received) == 1
