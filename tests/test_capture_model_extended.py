"""CaptureRecord NLE/SI 확장 테스트"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# 테스트 모듈 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.capture_model import CaptureRecord


class TestCaptureRecordNLEFields:
    """CaptureRecord NLE 필드 테스트"""

    def test_capture_record_nle_input_fields(self):
        """NLE 입력 필드 기본값 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )

        # NLE 입력 필드 기본값 확인
        assert record.nle_h == 25.0  # Horizontal distance (cm)
        assert record.nle_v == 75.0  # Vertical location (cm)
        assert record.nle_d == 25.0  # Vertical travel distance (cm)
        assert record.nle_a == 0.0   # Asymmetry angle (°)
        assert record.nle_f == 1.0   # Frequency (lifts/min)
        assert record.nle_c == 1     # Coupling (1=Good, 2=Fair, 3=Poor)
        assert record.nle_load == 0.0  # Actual load weight (kg)

    def test_capture_record_nle_result_fields(self):
        """NLE 결과 필드 기본값 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )

        # NLE 결과 필드 기본값 확인
        assert record.nle_rwl == 0.0  # Recommended Weight Limit
        assert record.nle_li == 0.0   # Lifting Index
        assert record.nle_risk == ''  # Risk level

    def test_capture_record_nle_custom_values(self):
        """NLE 필드에 커스텀 값 설정 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            nle_h=30.0,
            nle_v=80.0,
            nle_d=40.0,
            nle_a=15.0,
            nle_f=2.0,
            nle_c=2,
            nle_load=15.0,
        )

        assert record.nle_h == 30.0
        assert record.nle_v == 80.0
        assert record.nle_d == 40.0
        assert record.nle_a == 15.0
        assert record.nle_f == 2.0
        assert record.nle_c == 2
        assert record.nle_load == 15.0


class TestCaptureRecordSIFields:
    """CaptureRecord SI 필드 테스트"""

    def test_capture_record_si_input_fields(self):
        """SI 입력 필드 기본값 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )

        # SI 입력 필드 기본값 확인 (모두 레벨 1)
        assert record.si_ie == 1  # Intensity of Exertion
        assert record.si_de == 1  # Duration of Exertion
        assert record.si_em == 1  # Efforts per Minute
        assert record.si_hwp == 1  # Hand/Wrist Posture
        assert record.si_sw == 1  # Speed of Work
        assert record.si_dd == 1  # Duration per Day

    def test_capture_record_si_result_fields(self):
        """SI 결과 필드 기본값 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )

        # SI 결과 필드 기본값 확인
        assert record.si_score == 0.0  # Strain Index score
        assert record.si_risk == ''    # Risk level

    def test_capture_record_si_custom_values(self):
        """SI 필드에 커스텀 값 설정 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            si_ie=3,
            si_de=2,
            si_em=3,
            si_hwp=2,
            si_sw=2,
            si_dd=3,
        )

        assert record.si_ie == 3
        assert record.si_de == 2
        assert record.si_em == 3
        assert record.si_hwp == 2
        assert record.si_sw == 2
        assert record.si_dd == 3


class TestCaptureRecordFieldCount:
    """CaptureRecord 필드 수 테스트"""

    def test_capture_record_has_58_fields(self):
        """CaptureRecord는 58개 필드를 가짐 (기존 40개 + NLE 10개 + SI 8개)"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )
        from dataclasses import fields
        assert len(fields(record)) == 58


class TestCaptureRecordToDictWithNLESI:
    """CaptureRecord to_dict NLE/SI 포함 테스트"""

    def test_to_dict_includes_nle_fields(self):
        """to_dict에 NLE 필드 포함 확인"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            nle_h=30.0,
            nle_load=15.0,
        )

        d = record.to_dict()
        assert 'nle_h' in d
        assert 'nle_v' in d
        assert 'nle_d' in d
        assert 'nle_a' in d
        assert 'nle_f' in d
        assert 'nle_c' in d
        assert 'nle_load' in d
        assert 'nle_rwl' in d
        assert 'nle_li' in d
        assert 'nle_risk' in d
        assert d['nle_h'] == 30.0
        assert d['nle_load'] == 15.0

    def test_to_dict_includes_si_fields(self):
        """to_dict에 SI 필드 포함 확인"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            si_ie=3,
            si_de=2,
        )

        d = record.to_dict()
        assert 'si_ie' in d
        assert 'si_de' in d
        assert 'si_em' in d
        assert 'si_hwp' in d
        assert 'si_sw' in d
        assert 'si_dd' in d
        assert 'si_score' in d
        assert 'si_risk' in d
        assert d['si_ie'] == 3
        assert d['si_de'] == 2


class TestCaptureRecordFromDictWithNLESI:
    """CaptureRecord from_dict NLE/SI 포함 테스트"""

    def test_from_dict_with_nle_fields(self):
        """from_dict에서 NLE 필드 복원 확인"""
        data = {
            'timestamp': 1.0,
            'frame_number': 30,
            'capture_time': datetime.now().isoformat(),
            'nle_h': 30.0,
            'nle_v': 80.0,
            'nle_load': 15.0,
            'nle_rwl': 18.5,
            'nle_li': 0.81,
            'nle_risk': 'safe',
        }

        record = CaptureRecord.from_dict(data)
        assert record.nle_h == 30.0
        assert record.nle_v == 80.0
        assert record.nle_load == 15.0
        assert record.nle_rwl == 18.5
        assert record.nle_li == 0.81
        assert record.nle_risk == 'safe'

    def test_from_dict_with_si_fields(self):
        """from_dict에서 SI 필드 복원 확인"""
        data = {
            'timestamp': 1.0,
            'frame_number': 30,
            'capture_time': datetime.now().isoformat(),
            'si_ie': 3,
            'si_de': 2,
            'si_em': 3,
            'si_score': 6.75,
            'si_risk': 'uncertain',
        }

        record = CaptureRecord.from_dict(data)
        assert record.si_ie == 3
        assert record.si_de == 2
        assert record.si_em == 3
        assert record.si_score == 6.75
        assert record.si_risk == 'uncertain'

    def test_from_dict_without_nle_si_fields(self):
        """기존 데이터(NLE/SI 없음)에서 from_dict 호환성 테스트"""
        data = {
            'timestamp': 1.0,
            'frame_number': 30,
            'capture_time': datetime.now().isoformat(),
            'rula_upper_arm': 2,
            'rula_score': 4,
        }

        record = CaptureRecord.from_dict(data)
        # NLE 기본값 확인
        assert record.nle_h == 25.0
        assert record.nle_v == 75.0
        assert record.nle_load == 0.0
        # SI 기본값 확인
        assert record.si_ie == 1
        assert record.si_de == 1
        assert record.si_score == 0.0


class TestCaptureRecordRecalculateNLE:
    """CaptureRecord NLE 재계산 테스트"""

    def test_recalculate_nle(self):
        """NLE 재계산 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            nle_h=30.0,
            nle_v=75.0,
            nle_d=30.0,
            nle_a=0.0,
            nle_f=1.0,
            nle_c=1,
            nle_load=15.0,
        )

        # 재계산 수행
        record.recalculate_nle()

        # 결과 확인
        assert record.nle_rwl > 0
        assert record.nle_li > 0
        assert record.nle_risk in ['safe', 'increased', 'high']

    def test_recalculate_nle_safe_level(self):
        """NLE 재계산 - 안전 수준 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            nle_h=25.0,  # 이상적 수평 거리
            nle_v=75.0,  # 이상적 수직 높이
            nle_d=25.0,  # 이상적 이동 거리
            nle_a=0.0,   # 비틀림 없음
            nle_f=1.0,   # 낮은 빈도
            nle_c=1,     # Good coupling
            nle_load=5.0,  # 낮은 중량
        )

        record.recalculate_nle()

        # 이상적 조건에서는 RWL이 높고 LI가 낮아야 함
        assert record.nle_li <= 1.0
        assert record.nle_risk == 'safe'


class TestCaptureRecordRecalculateSI:
    """CaptureRecord SI 재계산 테스트"""

    def test_recalculate_si(self):
        """SI 재계산 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            si_ie=3,
            si_de=2,
            si_em=3,
            si_hwp=2,
            si_sw=2,
            si_dd=3,
        )

        # 재계산 수행
        record.recalculate_si()

        # 결과 확인
        assert record.si_score > 0
        assert record.si_risk in ['safe', 'uncertain', 'hazardous']

    def test_recalculate_si_safe_level(self):
        """SI 재계산 - 안전 수준 테스트 (모든 레벨 1)"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            si_ie=1,
            si_de=1,
            si_em=1,
            si_hwp=1,
            si_sw=1,
            si_dd=1,
        )

        record.recalculate_si()

        # SI = 1.0 × 0.5 × 0.5 × 1.0 × 1.0 × 0.25 = 0.0625
        assert record.si_score == pytest.approx(0.0625, rel=0.01)
        assert record.si_risk == 'safe'

    def test_recalculate_si_hazardous_level(self):
        """SI 재계산 - 위험 수준 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            si_ie=4,
            si_de=3,
            si_em=3,
            si_hwp=3,
            si_sw=2,
            si_dd=4,
        )

        record.recalculate_si()

        # 높은 입력값에서는 SI >= 7 (hazardous)
        assert record.si_score >= 7
        assert record.si_risk == 'hazardous'


class TestCaptureRecordRecalculateAll:
    """CaptureRecord recalculate_all 테스트"""

    def test_recalculate_all_includes_nle_si(self):
        """recalculate_all()이 NLE/SI 포함하는지 테스트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            nle_load=10.0,
            si_ie=2,
        )

        # 재계산 수행
        record.recalculate_all()

        # NLE/SI도 계산됨
        assert record.nle_rwl >= 0
        assert record.nle_li >= 0
        assert record.si_score >= 0
