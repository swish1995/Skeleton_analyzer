"""하드웨어 ID 생성 테스트

TDD Red Phase - 실패하는 테스트 먼저 작성
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHardwareId:
    """하드웨어 ID 생성 테스트"""

    def test_get_hardware_id_returns_string(self):
        """하드웨어 ID가 문자열로 반환되어야 함"""
        from src.license.hardware_id import get_hardware_id

        result = get_hardware_id()

        assert isinstance(result, str)

    def test_get_hardware_id_consistent(self):
        """동일 머신에서 항상 같은 ID 반환"""
        from src.license.hardware_id import get_hardware_id

        result1 = get_hardware_id()
        result2 = get_hardware_id()

        assert result1 == result2

    def test_get_hardware_id_length(self):
        """ID가 16자리여야 함"""
        from src.license.hardware_id import get_hardware_id

        result = get_hardware_id()

        assert len(result) == 16

    def test_get_hardware_id_alphanumeric(self):
        """ID가 영숫자로만 구성되어야 함 (대문자 16진수)"""
        from src.license.hardware_id import get_hardware_id

        result = get_hardware_id()

        assert result.isalnum()
        # 16진수 문자만 포함
        assert all(c in '0123456789ABCDEF' for c in result.upper())

    def test_get_hardware_id_cached(self):
        """결과가 캐시되어야 함"""
        from src.license import hardware_id
        from src.license.hardware_id import get_hardware_id, clear_cache

        # 캐시 초기화
        clear_cache()

        with patch.object(hardware_id, '_get_raw_hardware_id') as mock_raw:
            mock_raw.return_value = "test-uuid-12345"

            # 첫 번째 호출
            result1 = get_hardware_id()

            # 두 번째 호출
            result2 = get_hardware_id()

            # _get_raw_hardware_id는 한 번만 호출되어야 함
            assert mock_raw.call_count == 1
            assert result1 == result2


class TestHardwareIdPlatform:
    """플랫폼별 하드웨어 ID 획득 테스트"""

    @patch('platform.system')
    @patch('subprocess.run')
    def test_macos_uses_system_profiler(self, mock_run, mock_system):
        """macOS에서 system_profiler 사용"""
        from src.license.hardware_id import _get_raw_hardware_id, clear_cache

        clear_cache()
        mock_system.return_value = 'Darwin'
        mock_run.return_value = MagicMock(
            stdout="Hardware UUID: ABCD1234-5678-90AB-CDEF-1234567890AB\n",
            returncode=0
        )

        result = _get_raw_hardware_id()

        mock_run.assert_called_once()
        assert 'system_profiler' in mock_run.call_args[0][0]
        assert result is not None

    @patch('platform.system')
    @patch('subprocess.run')
    def test_windows_uses_wmic(self, mock_run, mock_system):
        """Windows에서 WMIC 사용"""
        from src.license.hardware_id import _get_raw_hardware_id, clear_cache

        clear_cache()
        mock_system.return_value = 'Windows'
        mock_run.return_value = MagicMock(
            stdout="UUID\nABCD1234-5678-90AB-CDEF-1234567890AB\n",
            returncode=0
        )

        result = _get_raw_hardware_id()

        mock_run.assert_called_once()
        # wmic 또는 powershell 명령 사용
        assert result is not None

    @patch('platform.system')
    @patch('builtins.open', create=True)
    def test_linux_uses_machine_id(self, mock_open, mock_system):
        """Linux에서 /etc/machine-id 사용"""
        from src.license.hardware_id import _get_raw_hardware_id, clear_cache

        clear_cache()
        mock_system.return_value = 'Linux'
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.read = MagicMock(
            return_value="abcd1234567890abcdef1234567890ab\n"
        )

        result = _get_raw_hardware_id()

        assert result is not None


class TestHardwareIdHashing:
    """해시 생성 테스트"""

    def test_hash_is_sha256_prefix(self):
        """SHA-256 해시의 앞 16자리 사용"""
        from src.license.hardware_id import _hash_hardware_id
        import hashlib

        raw_id = "test-raw-hardware-id"
        result = _hash_hardware_id(raw_id)

        # 직접 계산한 해시와 비교
        expected = hashlib.sha256(raw_id.encode()).hexdigest()[:16].upper()

        assert result == expected

    def test_hash_is_uppercase(self):
        """해시 결과는 대문자"""
        from src.license.hardware_id import _hash_hardware_id

        result = _hash_hardware_id("test")

        assert result == result.upper()


class TestHardwareIdErrorHandling:
    """에러 처리 테스트"""

    @patch('platform.system')
    @patch('subprocess.run')
    def test_fallback_on_command_failure(self, mock_run, mock_system):
        """명령 실패 시 폴백 ID 생성"""
        from src.license.hardware_id import get_hardware_id, clear_cache

        clear_cache()
        mock_system.return_value = 'Darwin'
        mock_run.side_effect = Exception("Command failed")

        # 폴백으로도 16자리 ID 반환해야 함
        result = get_hardware_id()

        assert len(result) == 16
        assert result.isalnum()
