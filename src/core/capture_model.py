"""
캡처 데이터 모델

스프레드시트 캡처 기능을 위한 데이터 모델 정의.
CaptureRecord: 단일 캡처 레코드 (43개 필드)
CaptureDataModel: 레코드 컬렉션 관리
"""

from dataclasses import dataclass, field, fields, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import bisect

from .score_calculator import (
    get_rula_table_a_score,
    get_rula_table_b_score,
    get_rula_table_c_score,
    get_rula_risk_level,
    get_reba_table_a_score,
    get_reba_table_b_score,
    get_reba_table_c_score,
    get_reba_risk_level,
    get_owas_action_category,
    get_owas_risk_level,
)


@dataclass
class CaptureRecord:
    """
    단일 캡처 레코드 (총 43개 필드)

    - 기본 정보 (3개): timestamp, frame_number, capture_time
    - RULA (15개): 부위 7 + 수동입력 4 + 결과 4
    - REBA (13개): 부위 6 + 수동입력 3 + 결과 4
    - OWAS (7개): 부위 3 + 수동입력 1 + 결과 3
    """

    # === 기본 정보 (3개) ===
    timestamp: float  # 동영상 시간 (초)
    frame_number: int  # 프레임 번호
    capture_time: datetime  # 캡처 시각 (실제 시간)

    # === RULA (15개) ===
    # 이미지 분석 결과 (7개)
    rula_upper_arm: int = 0
    rula_lower_arm: int = 0
    rula_wrist: int = 0
    rula_wrist_twist: int = 0
    rula_neck: int = 0
    rula_trunk: int = 0
    rula_leg: int = 0

    # 수동 입력 (4개)
    rula_muscle_use_a: int = 0  # 0 or 1
    rula_force_load_a: int = 0  # 0, 1, 2, 3
    rula_muscle_use_b: int = 0  # 0 or 1
    rula_force_load_b: int = 0  # 0, 1, 2, 3

    # 계산 결과 (4개)
    rula_score_a: int = 0  # Wrist & Arm Score
    rula_score_b: int = 0  # Neck Trunk Leg Score
    rula_score: int = 0  # Final Score
    rula_risk: str = ""  # Risk Level

    # === REBA (13개) ===
    # 이미지 분석 결과 (6개)
    reba_neck: int = 0
    reba_trunk: int = 0
    reba_leg: int = 0
    reba_upper_arm: int = 0
    reba_lower_arm: int = 0
    reba_wrist: int = 0

    # 수동 입력 (3개)
    reba_load_force: int = 0  # 0, 1, 2, 3
    reba_coupling: int = 0  # 0, 1, 2, 3
    reba_activity: int = 0  # 0, 1, 2, 3

    # 계산 결과 (4개)
    reba_score_a: int = 0  # Score A
    reba_score_b: int = 0  # Score B
    reba_score: int = 0  # Final Score
    reba_risk: str = ""  # Risk Level

    # === OWAS (7개) ===
    # 이미지 분석 결과 (3개)
    owas_back: int = 1
    owas_arms: int = 1
    owas_legs: int = 1

    # 수동 입력 (1개)
    owas_load: int = 1  # 1, 2, 3

    # 계산 결과 (3개)
    owas_code: str = "1111"  # Posture Code
    owas_ac: int = 1  # Action Category
    owas_risk: str = ""  # Risk Level

    def recalculate_rula(self) -> None:
        """RULA 점수 재계산"""
        # Table A 점수 (상지 posture)
        posture_a = get_rula_table_a_score(
            self.rula_upper_arm,
            self.rula_lower_arm,
            self.rula_wrist,
            self.rula_wrist_twist,
        )

        # Table B 점수 (목/몸통/다리 posture)
        posture_b = get_rula_table_b_score(
            self.rula_neck,
            self.rula_trunk,
            self.rula_leg,
        )

        # Score A = Table A + Muscle Use A + Force/Load A
        self.rula_score_a = posture_a + self.rula_muscle_use_a + self.rula_force_load_a

        # Score B = Table B + Muscle Use B + Force/Load B
        self.rula_score_b = posture_b + self.rula_muscle_use_b + self.rula_force_load_b

        # Final Score = Table C[Score A][Score B]
        self.rula_score = get_rula_table_c_score(self.rula_score_a, self.rula_score_b)

        # Risk Level
        self.rula_risk = get_rula_risk_level(self.rula_score)

    def recalculate_reba(self) -> None:
        """REBA 점수 재계산"""
        # Table A 점수 (목/몸통/다리 posture)
        posture_a = get_reba_table_a_score(
            self.reba_neck,
            self.reba_trunk,
            self.reba_leg,
        )

        # Table B 점수 (상지 posture)
        posture_b = get_reba_table_b_score(
            self.reba_upper_arm,
            self.reba_lower_arm,
            self.reba_wrist,
        )

        # Score A = Table A + Load/Force
        self.reba_score_a = posture_a + self.reba_load_force

        # Score B = Table B + Coupling
        self.reba_score_b = posture_b + self.reba_coupling

        # Score C = Table C[Score A][Score B]
        score_c = get_reba_table_c_score(self.reba_score_a, self.reba_score_b)

        # Final Score = Score C + Activity
        self.reba_score = score_c + self.reba_activity

        # Risk Level
        self.reba_risk = get_reba_risk_level(self.reba_score)

    def recalculate_owas(self) -> None:
        """OWAS 점수 재계산"""
        # Posture Code = back + arms + legs + load
        self.owas_code = f"{self.owas_back}{self.owas_arms}{self.owas_legs}{self.owas_load}"

        # Action Category (load와 무관)
        self.owas_ac = get_owas_action_category(
            self.owas_back,
            self.owas_arms,
            self.owas_legs,
        )

        # Risk Level
        self.owas_risk = get_owas_risk_level(self.owas_ac)

    def recalculate_all(self) -> None:
        """모든 평가 재계산"""
        self.recalculate_rula()
        self.recalculate_reba()
        self.recalculate_owas()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        d = asdict(self)
        # datetime을 ISO 문자열로 변환
        if isinstance(d['capture_time'], datetime):
            d['capture_time'] = d['capture_time'].isoformat()
        return d

    @classmethod
    def from_results(
        cls,
        timestamp: float,
        frame_number: int,
        capture_time: datetime,
        rula_result: Dict[str, Any],
        reba_result: Dict[str, Any],
        owas_result: Dict[str, Any],
    ) -> 'CaptureRecord':
        """평가 결과에서 레코드 생성"""
        record = cls(
            timestamp=timestamp,
            frame_number=frame_number,
            capture_time=capture_time,
            # RULA
            rula_upper_arm=rula_result.get('upper_arm', 0),
            rula_lower_arm=rula_result.get('lower_arm', 0),
            rula_wrist=rula_result.get('wrist', 0),
            rula_wrist_twist=rula_result.get('wrist_twist', 0),
            rula_neck=rula_result.get('neck', 0),
            rula_trunk=rula_result.get('trunk', 0),
            rula_leg=rula_result.get('leg', 0),
            rula_score_a=rula_result.get('score_a', 0),
            rula_score_b=rula_result.get('score_b', 0),
            rula_score=rula_result.get('score', 0),
            rula_risk=rula_result.get('risk', ''),
            # REBA
            reba_neck=reba_result.get('neck', 0),
            reba_trunk=reba_result.get('trunk', 0),
            reba_leg=reba_result.get('leg', 0),
            reba_upper_arm=reba_result.get('upper_arm', 0),
            reba_lower_arm=reba_result.get('lower_arm', 0),
            reba_wrist=reba_result.get('wrist', 0),
            reba_score_a=reba_result.get('score_a', 0),
            reba_score_b=reba_result.get('score_b', 0),
            reba_score=reba_result.get('score', 0),
            reba_risk=reba_result.get('risk', ''),
            # OWAS
            owas_back=owas_result.get('back', 1),
            owas_arms=owas_result.get('arms', 1),
            owas_legs=owas_result.get('legs', 1),
            owas_load=owas_result.get('load', 1),
            owas_code=owas_result.get('code', '1111'),
            owas_ac=owas_result.get('ac', 1),
            owas_risk=owas_result.get('risk', ''),
        )
        return record


class CaptureDataModel:
    """캡처 데이터 모델 (레코드 컬렉션 관리)"""

    def __init__(self):
        self._records: List[CaptureRecord] = []

    def add_record(self, record: CaptureRecord) -> int:
        """
        레코드 추가 (타임스탬프 기준 정렬 유지)

        Returns:
            삽입된 인덱스
        """
        # bisect를 사용하여 정렬된 위치에 삽입
        timestamps = [r.timestamp for r in self._records]
        index = bisect.bisect_left(timestamps, record.timestamp)
        self._records.insert(index, record)
        return index

    def get_record(self, index: int) -> Optional[CaptureRecord]:
        """인덱스로 레코드 조회"""
        if 0 <= index < len(self._records):
            return self._records[index]
        return None

    def update_record(self, index: int, record: CaptureRecord) -> bool:
        """레코드 업데이트"""
        if 0 <= index < len(self._records):
            self._records[index] = record
            return True
        return False

    def delete_record(self, index: int) -> bool:
        """레코드 삭제"""
        if 0 <= index < len(self._records):
            del self._records[index]
            return True
        return False

    def get_all_records(self) -> List[CaptureRecord]:
        """모든 레코드 반환"""
        return self._records.copy()

    def clear(self) -> None:
        """모든 레코드 삭제"""
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)

    def to_json(self, indent: int = 2) -> str:
        """JSON 문자열로 직렬화"""
        return json.dumps(
            [record.to_dict() for record in self._records],
            ensure_ascii=False,
            indent=indent,
        )

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """딕셔너리 리스트 반환 (Excel용)"""
        return [record.to_dict() for record in self._records]
