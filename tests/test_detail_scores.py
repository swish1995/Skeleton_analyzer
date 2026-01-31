"""RULA/REBA 세부 점수 필드 테스트 (Phase 1)"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# 테스트 모듈 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.capture_model import CaptureRecord, CaptureDataModel


class TestRULADetailFields:
    """RULA 세부 필드 테스트"""

    def test_rula_upper_arm_detail_fields_exist(self):
        """RULA 상박 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, shoulder_raised, abducted, supported 필드 확인
        assert hasattr(record, 'rula_upper_arm_base')
        assert hasattr(record, 'rula_upper_arm_shoulder_raised')
        assert hasattr(record, 'rula_upper_arm_abducted')
        assert hasattr(record, 'rula_upper_arm_supported')

    def test_rula_lower_arm_detail_fields_exist(self):
        """RULA 하박 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, working_across 필드 확인
        assert hasattr(record, 'rula_lower_arm_base')
        assert hasattr(record, 'rula_lower_arm_working_across')

    def test_rula_wrist_detail_fields_exist(self):
        """RULA 손목 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, bent_midline 필드 확인
        assert hasattr(record, 'rula_wrist_base')
        assert hasattr(record, 'rula_wrist_bent_midline')

    def test_rula_neck_detail_fields_exist(self):
        """RULA 목 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, twisted, side_bending 필드 확인
        assert hasattr(record, 'rula_neck_base')
        assert hasattr(record, 'rula_neck_twisted')
        assert hasattr(record, 'rula_neck_side_bending')

    def test_rula_trunk_detail_fields_exist(self):
        """RULA 몸통 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, twisted, side_bending 필드 확인
        assert hasattr(record, 'rula_trunk_base')
        assert hasattr(record, 'rula_trunk_twisted')
        assert hasattr(record, 'rula_trunk_side_bending')

    def test_rula_detail_fields_default_to_zero(self):
        """RULA 세부 필드 기본값은 0"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # 모든 세부 필드 기본값 확인
        assert record.rula_upper_arm_base == 0
        assert record.rula_upper_arm_shoulder_raised == 0
        assert record.rula_upper_arm_abducted == 0
        assert record.rula_upper_arm_supported == 0
        assert record.rula_lower_arm_base == 0
        assert record.rula_lower_arm_working_across == 0
        assert record.rula_wrist_base == 0
        assert record.rula_wrist_bent_midline == 0
        assert record.rula_neck_base == 0
        assert record.rula_neck_twisted == 0
        assert record.rula_neck_side_bending == 0
        assert record.rula_trunk_base == 0
        assert record.rula_trunk_twisted == 0
        assert record.rula_trunk_side_bending == 0


class TestREBADetailFields:
    """REBA 세부 필드 테스트"""

    def test_reba_neck_detail_fields_exist(self):
        """REBA 목 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, twist_side 필드 확인
        assert hasattr(record, 'reba_neck_base')
        assert hasattr(record, 'reba_neck_twist_side')

    def test_reba_trunk_detail_fields_exist(self):
        """REBA 몸통 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, twist_side 필드 확인
        assert hasattr(record, 'reba_trunk_base')
        assert hasattr(record, 'reba_trunk_twist_side')

    def test_reba_leg_detail_fields_exist(self):
        """REBA 다리 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, knee_30_60, knee_over_60 필드 확인
        assert hasattr(record, 'reba_leg_base')
        assert hasattr(record, 'reba_leg_knee_30_60')
        assert hasattr(record, 'reba_leg_knee_over_60')

    def test_reba_upper_arm_detail_fields_exist(self):
        """REBA 상완 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, shoulder_raised, abducted, supported 필드 확인
        assert hasattr(record, 'reba_upper_arm_base')
        assert hasattr(record, 'reba_upper_arm_shoulder_raised')
        assert hasattr(record, 'reba_upper_arm_abducted')
        assert hasattr(record, 'reba_upper_arm_supported')

    def test_reba_wrist_detail_fields_exist(self):
        """REBA 손목 세부 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # base, twisted 필드 확인
        assert hasattr(record, 'reba_wrist_base')
        assert hasattr(record, 'reba_wrist_twisted')

    def test_reba_detail_fields_default_to_zero(self):
        """REBA 세부 필드 기본값은 0"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        # 모든 세부 필드 기본값 확인
        assert record.reba_neck_base == 0
        assert record.reba_neck_twist_side == 0
        assert record.reba_trunk_base == 0
        assert record.reba_trunk_twist_side == 0
        assert record.reba_leg_base == 0
        assert record.reba_leg_knee_30_60 == 0
        assert record.reba_leg_knee_over_60 == 0
        assert record.reba_upper_arm_base == 0
        assert record.reba_upper_arm_shoulder_raised == 0
        assert record.reba_upper_arm_abducted == 0
        assert record.reba_upper_arm_supported == 0
        assert record.reba_wrist_base == 0
        assert record.reba_wrist_twisted == 0


class TestDetailFieldsSerialization:
    """세부 필드 직렬화 테스트"""

    def test_to_dict_includes_rula_detail_fields(self):
        """to_dict()에 RULA 세부 필드 포함"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        record.rula_upper_arm_base = 2
        record.rula_upper_arm_shoulder_raised = 1
        record.rula_upper_arm_abducted = 1
        record.rula_upper_arm_supported = -1

        d = record.to_dict()

        assert 'rula_upper_arm_base' in d
        assert 'rula_upper_arm_shoulder_raised' in d
        assert 'rula_upper_arm_abducted' in d
        assert 'rula_upper_arm_supported' in d
        assert d['rula_upper_arm_base'] == 2
        assert d['rula_upper_arm_shoulder_raised'] == 1

    def test_to_dict_includes_reba_detail_fields(self):
        """to_dict()에 REBA 세부 필드 포함"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        record.reba_neck_base = 2
        record.reba_neck_twist_side = 1

        d = record.to_dict()

        assert 'reba_neck_base' in d
        assert 'reba_neck_twist_side' in d
        assert d['reba_neck_base'] == 2
        assert d['reba_neck_twist_side'] == 1

    def test_from_dict_loads_rula_detail_fields(self):
        """from_dict()에서 RULA 세부 필드 로드"""
        data = {
            'timestamp': 1.0,
            'frame_number': 30,
            'capture_time': '2026-01-30T10:35:00',
            'rula_upper_arm_base': 2,
            'rula_upper_arm_shoulder_raised': 1,
            'rula_upper_arm_abducted': 0,
            'rula_upper_arm_supported': -1,
            'rula_lower_arm_base': 1,
            'rula_lower_arm_working_across': 1,
        }

        record = CaptureRecord.from_dict(data)

        assert record.rula_upper_arm_base == 2
        assert record.rula_upper_arm_shoulder_raised == 1
        assert record.rula_upper_arm_supported == -1
        assert record.rula_lower_arm_base == 1
        assert record.rula_lower_arm_working_across == 1

    def test_from_dict_loads_reba_detail_fields(self):
        """from_dict()에서 REBA 세부 필드 로드"""
        data = {
            'timestamp': 1.0,
            'frame_number': 30,
            'capture_time': '2026-01-30T10:35:00',
            'reba_neck_base': 2,
            'reba_neck_twist_side': 1,
            'reba_leg_base': 1,
            'reba_leg_knee_30_60': 1,
            'reba_leg_knee_over_60': 0,
        }

        record = CaptureRecord.from_dict(data)

        assert record.reba_neck_base == 2
        assert record.reba_neck_twist_side == 1
        assert record.reba_leg_base == 1
        assert record.reba_leg_knee_30_60 == 1

    def test_backward_compatible_load(self):
        """기존 데이터 로드 시 세부 필드 기본값 처리"""
        # 기존 형식 데이터 (세부 필드 없음)
        old_data = {
            'timestamp': 1.0,
            'frame_number': 30,
            'capture_time': '2026-01-30T10:35:00',
            'rula_upper_arm': 3,  # 기존 total 필드만 있음
            'rula_lower_arm': 2,
        }

        record = CaptureRecord.from_dict(old_data)

        # 세부 필드는 기본값(0)
        assert record.rula_upper_arm_base == 0
        assert record.rula_upper_arm_shoulder_raised == 0
        # 기존 total 필드는 유지
        assert record.rula_upper_arm == 3


class TestDetailFieldsRoundtrip:
    """세부 필드 왕복 변환 테스트"""

    def test_roundtrip_rula_detail_fields(self):
        """RULA 세부 필드 to_dict → from_dict 왕복"""
        original = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )
        original.rula_upper_arm_base = 2
        original.rula_upper_arm_shoulder_raised = 1
        original.rula_upper_arm_abducted = 1
        original.rula_upper_arm_supported = -1
        original.rula_neck_base = 3
        original.rula_neck_twisted = 1
        original.rula_neck_side_bending = 0

        data = original.to_dict()
        restored = CaptureRecord.from_dict(data)

        assert restored.rula_upper_arm_base == original.rula_upper_arm_base
        assert restored.rula_upper_arm_shoulder_raised == original.rula_upper_arm_shoulder_raised
        assert restored.rula_upper_arm_supported == original.rula_upper_arm_supported
        assert restored.rula_neck_base == original.rula_neck_base
        assert restored.rula_neck_twisted == original.rula_neck_twisted

    def test_roundtrip_reba_detail_fields(self):
        """REBA 세부 필드 to_dict → from_dict 왕복"""
        original = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )
        original.reba_neck_base = 2
        original.reba_neck_twist_side = 1
        original.reba_leg_base = 1
        original.reba_leg_knee_30_60 = 1
        original.reba_leg_knee_over_60 = 0
        original.reba_upper_arm_base = 3
        original.reba_upper_arm_supported = -1

        data = original.to_dict()
        restored = CaptureRecord.from_dict(data)

        assert restored.reba_neck_base == original.reba_neck_base
        assert restored.reba_neck_twist_side == original.reba_neck_twist_side
        assert restored.reba_leg_base == original.reba_leg_base
        assert restored.reba_leg_knee_30_60 == original.reba_leg_knee_30_60
        assert restored.reba_upper_arm_supported == original.reba_upper_arm_supported


class TestFieldCount:
    """필드 개수 테스트"""

    def test_capture_record_field_count_increased(self):
        """CaptureRecord 필드 개수 증가 확인 (58 → 85)"""
        # 기존 58개 + RULA 세부 14개 + REBA 세부 13개 = 85개
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )
        from dataclasses import fields
        # RULA 세부: upper_arm(4) + lower_arm(2) + wrist(2) + neck(3) + trunk(3) = 14개
        # REBA 세부: neck(2) + trunk(2) + leg(3) + upper_arm(4) + wrist(2) = 13개
        # 기존 58 + 14 + 13 = 85개
        assert len(fields(record)) == 85
