"""라이센스 키 검증 테스트

TDD Red Phase - 실패하는 테스트 먼저 작성
"""

import pytest
from unittest.mock import patch


class TestValidateFormat:
    """라이센스 키 형식 검증 테스트"""

    def test_validate_format_valid(self):
        """유효한 형식 (XXXX-XXXX-XXXX-XXXX)"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_format("ABCD-1234-EFGH-5678")

        assert result is True

    def test_validate_format_too_short(self):
        """짧은 키 → 실패"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_format("ABCD-1234-EFGH")

        assert result is False

    def test_validate_format_too_long(self):
        """긴 키 → 실패"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_format("ABCD-1234-EFGH-5678-IJKL")

        assert result is False

    def test_validate_format_no_hyphens(self):
        """하이픈 없는 키 → 실패"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_format("ABCD1234EFGH5678")

        assert result is False

    def test_validate_format_wrong_hyphens(self):
        """잘못된 위치의 하이픈 → 실패"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_format("ABC-D1234-EFGH-5678")

        assert result is False

    def test_validate_format_lowercase(self):
        """소문자 키 → 대문자로 변환 후 성공"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_format("abcd-1234-efgh-5678")

        assert result is True

    def test_validate_format_with_spaces(self):
        """공백 포함 키 → 제거 후 성공"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_format(" ABCD-1234-EFGH-5678 ")

        assert result is True

    def test_validate_format_empty(self):
        """빈 문자열 → 실패"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_format("")

        assert result is False

    def test_validate_format_none(self):
        """None → 실패"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_format(None)

        assert result is False


class TestValidateChecksum:
    """체크섬 검증 테스트"""

    def test_validate_checksum_valid(self):
        """유효한 체크섬"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        # 유효한 체크섬을 가진 키 (마지막 4자리가 체크섬)
        valid_key = validator.generate_test_key("TESTHARDWARE01")

        result = validator.validate_checksum(valid_key)

        assert result is True

    def test_validate_checksum_invalid(self):
        """잘못된 체크섬 → 실패"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.validate_checksum("ABCD-1234-EFGH-0000")

        assert result is False

    def test_validate_checksum_tampered(self):
        """변조된 키 → 체크섬 불일치"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        valid_key = validator.generate_test_key("TESTHARDWARE01")

        # 키의 일부를 변조
        tampered_key = "XXXX" + valid_key[4:]

        result = validator.validate_checksum(tampered_key)

        assert result is False


class TestValidateHardware:
    """하드웨어 매칭 테스트"""

    def test_validate_hardware_match(self):
        """하드웨어 ID 일치"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        hardware_id = "TESTHARDWARE01"
        key = validator.generate_test_key(hardware_id)

        result = validator.validate_hardware(key, hardware_id)

        assert result is True

    def test_validate_hardware_mismatch(self):
        """하드웨어 ID 불일치 → 실패"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        key = validator.generate_test_key("HARDWARE_A")

        result = validator.validate_hardware(key, "HARDWARE_B")

        assert result is False


class TestValidate:
    """종합 검증 테스트"""

    def test_validate_valid_key(self):
        """유효한 키 → VALID"""
        from src.license.license_validator import LicenseValidator, ValidationResult

        validator = LicenseValidator()
        hardware_id = "TESTHARDWARE01"
        key = validator.generate_test_key(hardware_id)

        result = validator.validate(key, hardware_id)

        assert result == ValidationResult.VALID

    def test_validate_invalid_format(self):
        """형식 오류 → INVALID_FORMAT"""
        from src.license.license_validator import LicenseValidator, ValidationResult

        validator = LicenseValidator()

        result = validator.validate("invalid-key", "TESTHARDWARE01")

        assert result == ValidationResult.INVALID_FORMAT

    def test_validate_invalid_checksum(self):
        """체크섬 오류 → INVALID_CHECKSUM"""
        from src.license.license_validator import LicenseValidator, ValidationResult

        validator = LicenseValidator()
        # 형식은 맞지만 체크섬이 틀린 키
        result = validator.validate("ABCD-1234-EFGH-0000", "TESTHARDWARE01")

        assert result == ValidationResult.INVALID_CHECKSUM

    def test_validate_hardware_mismatch(self):
        """하드웨어 불일치 → HARDWARE_MISMATCH"""
        from src.license.license_validator import LicenseValidator, ValidationResult

        validator = LicenseValidator()
        key = validator.generate_test_key("HARDWARE_A")

        result = validator.validate(key, "HARDWARE_B")

        assert result == ValidationResult.HARDWARE_MISMATCH


class TestNormalizeKey:
    """키 정규화 테스트"""

    def test_normalize_uppercase(self):
        """소문자 → 대문자 변환"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.normalize_key("abcd-1234-efgh-5678")

        assert result == "ABCD-1234-EFGH-5678"

    def test_normalize_strip_spaces(self):
        """공백 제거"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.normalize_key("  ABCD-1234-EFGH-5678  ")

        assert result == "ABCD-1234-EFGH-5678"

    def test_normalize_combined(self):
        """소문자 + 공백 → 정규화"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        result = validator.normalize_key("  abcd-1234-efgh-5678  ")

        assert result == "ABCD-1234-EFGH-5678"


class TestGenerateTestKey:
    """테스트 키 생성 테스트"""

    def test_generate_test_key_format(self):
        """생성된 키가 올바른 형식"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        key = validator.generate_test_key("TESTHARDWARE01")

        assert len(key) == 19  # XXXX-XXXX-XXXX-XXXX
        assert key[4] == '-'
        assert key[9] == '-'
        assert key[14] == '-'

    def test_generate_test_key_valid(self):
        """생성된 키가 검증 통과"""
        from src.license.license_validator import LicenseValidator, ValidationResult

        validator = LicenseValidator()
        hardware_id = "TESTHARDWARE01"
        key = validator.generate_test_key(hardware_id)

        result = validator.validate(key, hardware_id)

        assert result == ValidationResult.VALID

    def test_generate_test_key_deterministic(self):
        """동일한 하드웨어 ID로 동일한 키 생성"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        key1 = validator.generate_test_key("TESTHARDWARE01")
        key2 = validator.generate_test_key("TESTHARDWARE01")

        assert key1 == key2

    def test_generate_test_key_different_hardware(self):
        """다른 하드웨어 ID로 다른 키 생성"""
        from src.license.license_validator import LicenseValidator

        validator = LicenseValidator()
        key1 = validator.generate_test_key("HARDWARE_A")
        key2 = validator.generate_test_key("HARDWARE_B")

        assert key1 != key2
