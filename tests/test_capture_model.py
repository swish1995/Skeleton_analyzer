"""CaptureRecord 및 CaptureDataModel 테스트"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.capture_model import CaptureRecord, CaptureDataModel


class TestCaptureRecordCreation:
    """CaptureRecord 인스턴스 생성 테스트"""

    def test_capture_record_creation_minimal(self):
        """최소 필수 필드로 생성"""
        record = CaptureRecord(
            timestamp=5.123,
            frame_number=154,
            capture_time=datetime.now(),
        )
        assert record.timestamp == 5.123
        assert record.frame_number == 154

    def test_capture_record_has_40_fields(self):
        """CaptureRecord는 40개 필드를 가짐 (3기본 + 15RULA + 13REBA + 7OWAS + 2이미지)"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )
        # dataclass의 필드 수 확인
        from dataclasses import fields
        assert len(fields(record)) == 40

    def test_capture_record_default_manual_fields(self):
        """수동 입력 필드 기본값은 0"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
        )
        # RULA 수동 입력
        assert record.rula_muscle_use_a == 0
        assert record.rula_force_load_a == 0
        assert record.rula_muscle_use_b == 0
        assert record.rula_force_load_b == 0
        # REBA 수동 입력
        assert record.reba_load_force == 0
        assert record.reba_coupling == 0
        assert record.reba_activity == 0
        # OWAS 수동 입력
        assert record.owas_load == 1  # OWAS load는 1-3 범위, 기본값 1

    def test_capture_record_to_dict(self):
        """CaptureRecord → dict 변환"""
        now = datetime.now()
        record = CaptureRecord(
            timestamp=5.0,
            frame_number=150,
            capture_time=now,
            rula_upper_arm=2,
            rula_score=4,
        )
        d = record.to_dict()
        assert isinstance(d, dict)
        assert d['timestamp'] == 5.0
        assert d['frame_number'] == 150
        assert d['rula_upper_arm'] == 2
        assert d['rula_score'] == 4
        assert len(d) == 40


class TestCaptureRecordRecalculation:
    """CaptureRecord 재계산 테스트"""

    def test_recalculate_rula_with_manual_input(self):
        """RULA 수동 입력 후 재계산"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            # 이미지 분석 결과
            rula_upper_arm=2,
            rula_lower_arm=2,
            rula_wrist=2,
            rula_wrist_twist=1,
            rula_neck=2,
            rula_trunk=2,
            rula_leg=1,
        )
        # 초기 계산
        record.recalculate_rula()
        initial_score_a = record.rula_score_a
        initial_score = record.rula_score

        # 수동 입력 변경
        record.rula_muscle_use_a = 1
        record.rula_force_load_a = 2
        record.recalculate_rula()

        # Score A가 증가해야 함 (muscle + force 추가)
        assert record.rula_score_a == initial_score_a + 3  # +1(muscle) + 2(force)

    def test_recalculate_rula_score_a_formula(self):
        """RULA Score A = Table A + Muscle Use + Force/Load"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            rula_upper_arm=1,
            rula_lower_arm=1,
            rula_wrist=1,
            rula_wrist_twist=1,
        )
        record.rula_muscle_use_a = 1
        record.rula_force_load_a = 3
        record.recalculate_rula()

        # Table A(1,1,1,1) = 1, + muscle(1) + force(3) = 5
        assert record.rula_score_a == 5

    def test_recalculate_rula_score_b_formula(self):
        """RULA Score B = Table B + Muscle Use + Force/Load"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            rula_neck=1,
            rula_trunk=1,
            rula_leg=1,
        )
        record.rula_muscle_use_b = 1
        record.rula_force_load_b = 2
        record.recalculate_rula()

        # Table B(1,1,1) = 1, + muscle(1) + force(2) = 4
        assert record.rula_score_b == 4

    def test_recalculate_reba_with_manual_input(self):
        """REBA 수동 입력 후 재계산"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            reba_neck=1,
            reba_trunk=1,
            reba_leg=1,
            reba_upper_arm=1,
            reba_lower_arm=1,
            reba_wrist=1,
        )
        record.recalculate_reba()
        initial_score = record.reba_score

        # 수동 입력 변경
        record.reba_load_force = 2
        record.reba_coupling = 1
        record.reba_activity = 2
        record.recalculate_reba()

        # 점수가 증가해야 함
        assert record.reba_score > initial_score

    def test_recalculate_reba_activity_adds_to_final(self):
        """REBA Activity는 최종 점수에 더해짐"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            reba_neck=1,
            reba_trunk=1,
            reba_leg=1,
            reba_upper_arm=1,
            reba_lower_arm=1,
            reba_wrist=1,
        )
        record.recalculate_reba()
        score_without_activity = record.reba_score

        record.reba_activity = 2
        record.recalculate_reba()

        # activity가 최종 점수에 추가됨
        assert record.reba_score == score_without_activity + 2

    def test_recalculate_owas_updates_code(self):
        """OWAS 하중 변경 시 코드 업데이트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            owas_back=2,
            owas_arms=1,
            owas_legs=3,
        )
        record.owas_load = 2
        record.recalculate_owas()

        assert record.owas_code == "2132"

    def test_owas_ac_independent_of_load(self):
        """OWAS AC는 하중(load)과 무관"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            owas_back=2,
            owas_arms=1,
            owas_legs=1,
        )
        record.owas_load = 1
        record.recalculate_owas()
        ac_with_load_1 = record.owas_ac

        record.owas_load = 3
        record.recalculate_owas()
        ac_with_load_3 = record.owas_ac

        # AC는 load와 무관하게 동일
        assert ac_with_load_1 == ac_with_load_3

    def test_recalculate_updates_risk_level(self):
        """재계산 시 위험 수준도 업데이트"""
        record = CaptureRecord(
            timestamp=1.0,
            frame_number=30,
            capture_time=datetime.now(),
            rula_upper_arm=1,
            rula_lower_arm=1,
            rula_wrist=1,
            rula_wrist_twist=1,
            rula_neck=1,
            rula_trunk=1,
            rula_leg=1,
        )
        record.recalculate_rula()

        # 낮은 점수일 때 acceptable
        assert record.rula_risk == 'acceptable'


class TestCaptureDataModel:
    """CaptureDataModel 테스트"""

    def test_add_record(self):
        """레코드 추가"""
        model = CaptureDataModel()
        record = CaptureRecord(
            timestamp=5.0,
            frame_number=150,
            capture_time=datetime.now(),
        )
        model.add_record(record)
        assert len(model.get_all_records()) == 1

    def test_add_record_maintains_sort(self):
        """레코드 추가 시 타임스탬프 정렬 유지"""
        model = CaptureDataModel()
        now = datetime.now()

        model.add_record(CaptureRecord(timestamp=10.0, frame_number=300, capture_time=now))
        model.add_record(CaptureRecord(timestamp=5.0, frame_number=150, capture_time=now))
        model.add_record(CaptureRecord(timestamp=15.0, frame_number=450, capture_time=now))

        records = model.get_all_records()
        assert records[0].timestamp == 5.0
        assert records[1].timestamp == 10.0
        assert records[2].timestamp == 15.0

    def test_get_record_by_index(self):
        """인덱스로 레코드 조회"""
        model = CaptureDataModel()
        now = datetime.now()
        model.add_record(CaptureRecord(timestamp=5.0, frame_number=150, capture_time=now))
        model.add_record(CaptureRecord(timestamp=10.0, frame_number=300, capture_time=now))

        record = model.get_record(1)
        assert record.timestamp == 10.0

    def test_update_record(self):
        """레코드 업데이트"""
        model = CaptureDataModel()
        now = datetime.now()
        model.add_record(CaptureRecord(timestamp=5.0, frame_number=150, capture_time=now))

        record = model.get_record(0)
        record.rula_muscle_use_a = 1
        model.update_record(0, record)

        updated = model.get_record(0)
        assert updated.rula_muscle_use_a == 1

    def test_delete_record(self):
        """레코드 삭제"""
        model = CaptureDataModel()
        now = datetime.now()
        model.add_record(CaptureRecord(timestamp=5.0, frame_number=150, capture_time=now))
        model.add_record(CaptureRecord(timestamp=10.0, frame_number=300, capture_time=now))

        model.delete_record(0)
        assert len(model.get_all_records()) == 1
        assert model.get_record(0).timestamp == 10.0

    def test_clear_removes_all(self):
        """초기화 시 모든 레코드 삭제"""
        model = CaptureDataModel()
        now = datetime.now()
        model.add_record(CaptureRecord(timestamp=5.0, frame_number=150, capture_time=now))
        model.add_record(CaptureRecord(timestamp=10.0, frame_number=300, capture_time=now))

        model.clear()
        assert len(model.get_all_records()) == 0

    def test_to_json(self):
        """JSON 직렬화"""
        model = CaptureDataModel()
        now = datetime.now()
        model.add_record(CaptureRecord(
            timestamp=5.0,
            frame_number=150,
            capture_time=now,
            rula_score=3,
        ))

        json_str = model.to_json()
        data = json.loads(json_str)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['timestamp'] == 5.0
        assert data[0]['rula_score'] == 3

    def test_to_json_includes_manual_fields(self):
        """JSON에 수동 입력 필드 포함"""
        model = CaptureDataModel()
        now = datetime.now()
        record = CaptureRecord(
            timestamp=5.0,
            frame_number=150,
            capture_time=now,
        )
        record.rula_muscle_use_a = 1
        record.reba_coupling = 2
        model.add_record(record)

        json_str = model.to_json()
        data = json.loads(json_str)

        assert data[0]['rula_muscle_use_a'] == 1
        assert data[0]['reba_coupling'] == 2

    def test_to_dict_list(self):
        """딕셔너리 리스트 반환 (Excel용)"""
        model = CaptureDataModel()
        now = datetime.now()
        model.add_record(CaptureRecord(timestamp=5.0, frame_number=150, capture_time=now))

        dict_list = model.to_dict_list()
        assert isinstance(dict_list, list)
        assert isinstance(dict_list[0], dict)
        assert len(dict_list[0]) == 40


class TestCaptureRecordImagePaths:
    """CaptureRecord 이미지 경로 필드 테스트"""

    def test_has_video_frame_path_field(self):
        """video_frame_path 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        assert hasattr(record, 'video_frame_path')
        assert record.video_frame_path is None

    def test_has_skeleton_image_path_field(self):
        """skeleton_image_path 필드 존재 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
        )
        assert hasattr(record, 'skeleton_image_path')
        assert record.skeleton_image_path is None

    def test_image_paths_can_be_set(self):
        """이미지 경로 설정 가능 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
            video_frame_path="/path/to/frame.png",
            skeleton_image_path="/path/to/skeleton.png",
        )
        assert record.video_frame_path == "/path/to/frame.png"
        assert record.skeleton_image_path == "/path/to/skeleton.png"

    def test_to_dict_includes_image_paths(self):
        """to_dict()에 이미지 경로 포함 확인"""
        record = CaptureRecord(
            timestamp=0.0,
            frame_number=0,
            capture_time=datetime.now(),
            video_frame_path="/path/to/frame.png",
            skeleton_image_path="/path/to/skeleton.png",
        )
        d = record.to_dict()
        assert 'video_frame_path' in d
        assert 'skeleton_image_path' in d
        assert d['video_frame_path'] == "/path/to/frame.png"
        assert d['skeleton_image_path'] == "/path/to/skeleton.png"


class TestCaptureRecordFromErgonomicResult:
    """평가 결과에서 CaptureRecord 생성 테스트"""

    def test_from_results(self):
        """RULA/REBA/OWAS 결과에서 레코드 생성"""
        now = datetime.now()
        record = CaptureRecord.from_results(
            timestamp=5.0,
            frame_number=150,
            capture_time=now,
            rula_result={
                'upper_arm': 2, 'lower_arm': 2, 'wrist': 2, 'wrist_twist': 1,
                'neck': 2, 'trunk': 2, 'leg': 1,
                'score_a': 3, 'score_b': 2, 'score': 3, 'risk': 'investigate',
            },
            reba_result={
                'neck': 1, 'trunk': 2, 'leg': 1,
                'upper_arm': 2, 'lower_arm': 1, 'wrist': 1,
                'score_a': 2, 'score_b': 1, 'score': 2, 'risk': 'low',
            },
            owas_result={
                'back': 1, 'arms': 1, 'legs': 2,
                'load': 1, 'code': '1121', 'ac': 1, 'risk': 'normal',
            },
        )

        assert record.timestamp == 5.0
        assert record.rula_upper_arm == 2
        assert record.rula_score == 3
        assert record.reba_neck == 1
        assert record.owas_back == 1
