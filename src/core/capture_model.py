"""
캡처 데이터 모델

스프레드시트 캡처 기능을 위한 데이터 모델 정의.
CaptureRecord: 단일 캡처 레코드 (40개 필드)
CaptureDataModel: 레코드 컬렉션 관리
"""

from dataclasses import dataclass, field, fields, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
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
    # NLE functions
    calculate_nle_rwl,
    calculate_nle_li,
    get_nle_risk_level,
    # SI functions
    calculate_si_score,
    get_si_risk_level,
)
from .logger import get_logger

_logger = get_logger('capture_model')


@dataclass
class CaptureRecord:
    """
    단일 캡처 레코드 (총 58개 필드)

    - 기본 정보 (3개): timestamp, frame_number, capture_time
    - RULA (15개): 부위 7 + 수동입력 4 + 결과 4
    - REBA (13개): 부위 6 + 수동입력 3 + 결과 4
    - OWAS (7개): 부위 3 + 수동입력 1 + 결과 3
    - NLE (10개): 입력 7 + 결과 3
    - SI (8개): 입력 6 + 결과 2
    - 이미지 경로 (2개): video_frame_path, skeleton_image_path
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

    # === NLE (10개) ===
    # 입력 파라미터 (7개)
    nle_h: float = 25.0           # Horizontal distance (cm), 기본값 25
    nle_v: float = 75.0           # Vertical location (cm), 기본값 75
    nle_d: float = 25.0           # Vertical travel distance (cm)
    nle_a: float = 0.0            # Asymmetry angle (°)
    nle_f: float = 1.0            # Frequency (lifts/min)
    nle_c: int = 1                # Coupling (1=Good, 2=Fair, 3=Poor)
    nle_load: float = 0.0         # Actual load weight (kg)

    # 계산 결과 (3개)
    nle_rwl: float = 0.0          # Recommended Weight Limit (kg)
    nle_li: float = 0.0           # Lifting Index
    nle_risk: str = ""            # Risk level (safe/increased/high)

    # === SI (8개) ===
    # 입력 파라미터 (6개)
    si_ie: int = 1                # Intensity of Exertion (1-5)
    si_de: int = 1                # Duration of Exertion (1-5)
    si_em: int = 1                # Efforts per Minute (1-5)
    si_hwp: int = 1               # Hand/Wrist Posture (1-5)
    si_sw: int = 1                # Speed of Work (1-5)
    si_dd: int = 1                # Duration per Day (1-5)

    # 계산 결과 (2개)
    si_score: float = 0.0         # Strain Index score
    si_risk: str = ""             # Risk level (safe/uncertain/hazardous)

    # === 이미지 경로 (2개) ===
    video_frame_path: Optional[str] = None  # 동영상 프레임 이미지 경로
    skeleton_image_path: Optional[str] = None  # 스켈레톤 이미지 경로

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

    def recalculate_nle(self) -> None:
        """NLE 점수 재계산"""
        # RWL 계산
        self.nle_rwl = calculate_nle_rwl(
            h=self.nle_h,
            v=self.nle_v,
            d=self.nle_d,
            a=self.nle_a,
            frequency=self.nle_f,
            duration_hours=1.0,  # 기본 1시간
            coupling=self.nle_c,
        )

        # LI 계산
        self.nle_li = calculate_nle_li(self.nle_load, self.nle_rwl)

        # Risk Level
        self.nle_risk = get_nle_risk_level(self.nle_li)

    def recalculate_si(self) -> None:
        """SI 점수 재계산"""
        # SI Score 계산
        self.si_score = calculate_si_score(
            ie=self.si_ie,
            de=self.si_de,
            em=self.si_em,
            hwp=self.si_hwp,
            sw=self.si_sw,
            dd=self.si_dd,
        )

        # Risk Level
        self.si_risk = get_si_risk_level(self.si_score)

    def recalculate_all(self) -> None:
        """모든 평가 재계산"""
        self.recalculate_rula()
        self.recalculate_reba()
        self.recalculate_owas()
        self.recalculate_nle()
        self.recalculate_si()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        d = asdict(self)
        # datetime을 ISO 문자열로 변환
        if isinstance(d['capture_time'], datetime):
            d['capture_time'] = d['capture_time'].isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CaptureRecord':
        """딕셔너리에서 CaptureRecord 생성 (역직렬화)"""
        # capture_time 처리: ISO 문자열 → datetime
        capture_time = data.get('capture_time')
        if isinstance(capture_time, str):
            capture_time = datetime.fromisoformat(capture_time)

        return cls(
            timestamp=data.get('timestamp', 0.0),
            frame_number=data.get('frame_number', 0),
            capture_time=capture_time,
            # RULA 필드
            rula_upper_arm=data.get('rula_upper_arm', 0),
            rula_lower_arm=data.get('rula_lower_arm', 0),
            rula_wrist=data.get('rula_wrist', 0),
            rula_wrist_twist=data.get('rula_wrist_twist', 0),
            rula_neck=data.get('rula_neck', 0),
            rula_trunk=data.get('rula_trunk', 0),
            rula_leg=data.get('rula_leg', 0),
            rula_muscle_use_a=data.get('rula_muscle_use_a', 0),
            rula_force_load_a=data.get('rula_force_load_a', 0),
            rula_muscle_use_b=data.get('rula_muscle_use_b', 0),
            rula_force_load_b=data.get('rula_force_load_b', 0),
            rula_score_a=data.get('rula_score_a', 0),
            rula_score_b=data.get('rula_score_b', 0),
            rula_score=data.get('rula_score', 0),
            rula_risk=data.get('rula_risk', ''),
            # REBA 필드
            reba_neck=data.get('reba_neck', 0),
            reba_trunk=data.get('reba_trunk', 0),
            reba_leg=data.get('reba_leg', 0),
            reba_upper_arm=data.get('reba_upper_arm', 0),
            reba_lower_arm=data.get('reba_lower_arm', 0),
            reba_wrist=data.get('reba_wrist', 0),
            reba_load_force=data.get('reba_load_force', 0),
            reba_coupling=data.get('reba_coupling', 0),
            reba_activity=data.get('reba_activity', 0),
            reba_score_a=data.get('reba_score_a', 0),
            reba_score_b=data.get('reba_score_b', 0),
            reba_score=data.get('reba_score', 0),
            reba_risk=data.get('reba_risk', ''),
            # OWAS 필드
            owas_back=data.get('owas_back', 1),
            owas_arms=data.get('owas_arms', 1),
            owas_legs=data.get('owas_legs', 1),
            owas_load=data.get('owas_load', 1),
            owas_code=data.get('owas_code', '1111'),
            owas_ac=data.get('owas_ac', 1),
            owas_risk=data.get('owas_risk', ''),
            # NLE 필드
            nle_h=data.get('nle_h', 25.0),
            nle_v=data.get('nle_v', 75.0),
            nle_d=data.get('nle_d', 25.0),
            nle_a=data.get('nle_a', 0.0),
            nle_f=data.get('nle_f', 1.0),
            nle_c=data.get('nle_c', 1),
            nle_load=data.get('nle_load', 0.0),
            nle_rwl=data.get('nle_rwl', 0.0),
            nle_li=data.get('nle_li', 0.0),
            nle_risk=data.get('nle_risk', ''),
            # SI 필드
            si_ie=data.get('si_ie', 1),
            si_de=data.get('si_de', 1),
            si_em=data.get('si_em', 1),
            si_hwp=data.get('si_hwp', 1),
            si_sw=data.get('si_sw', 1),
            si_dd=data.get('si_dd', 1),
            si_score=data.get('si_score', 0.0),
            si_risk=data.get('si_risk', ''),
            # 이미지 경로
            video_frame_path=data.get('video_frame_path'),
            skeleton_image_path=data.get('skeleton_image_path'),
        )

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

    def to_project_dict(self, base_path: Path) -> Dict[str, Any]:
        """
        프로젝트 저장용 딕셔너리 생성

        이미지 경로를 base_path 기준 상대 경로로 변환합니다.

        Args:
            base_path: 이미지 경로의 기준 디렉토리

        Returns:
            {'records': [...]} 형태의 딕셔너리
        """
        records = []
        base_path_str = str(base_path)

        for record in self._records:
            data = record.to_dict()

            # 이미지 경로를 상대 경로로 변환
            for key in ('video_frame_path', 'skeleton_image_path'):
                path = data.get(key)
                if path:
                    try:
                        path_obj = Path(path)
                        if path_obj.is_absolute():
                            # 절대 경로인 경우 base_path 기준 상대 경로로 변환
                            data[key] = str(path_obj.relative_to(base_path))
                        else:
                            # 상대 경로인 경우 base_path로 시작하면 제거
                            path_str = str(path_obj)
                            if path_str.startswith(base_path_str + '/') or path_str.startswith(base_path_str + '\\'):
                                data[key] = path_str[len(base_path_str) + 1:]
                    except ValueError:
                        # base_path 밖의 경로인 경우 원본 유지
                        pass

            records.append(data)

        return {'records': records}

    @classmethod
    def from_project_dict(
        cls,
        data: Dict[str, Any],
        base_path: Path
    ) -> 'CaptureDataModel':
        """
        프로젝트 딕셔너리에서 모델 복원

        상대 경로를 base_path 기준 절대 경로로 변환합니다.

        Args:
            data: {'records': [...]} 형태의 딕셔너리
            base_path: 이미지 경로의 기준 디렉토리

        Returns:
            CaptureDataModel 인스턴스
        """
        _logger.info(f"[썸네일] from_project_dict 호출: base_path={base_path}")
        model = cls()

        records_data = data.get('records', [])
        _logger.debug(f"[썸네일] 레코드 수: {len(records_data)}")

        for idx, record_data in enumerate(records_data):
            # 이미지 경로를 절대 경로로 변환
            for key in ('video_frame_path', 'skeleton_image_path'):
                path = record_data.get(key)
                if path:
                    rel_path = Path(path)
                    _logger.debug(f"[썸네일] 레코드 {idx} - {key}: 원본 경로={path}, is_absolute={rel_path.is_absolute()}")
                    if not rel_path.is_absolute():
                        abs_path = str(base_path / rel_path)
                        record_data[key] = abs_path
                        _logger.debug(f"[썸네일] 레코드 {idx} - {key}: 변환된 절대 경로={abs_path}")
                else:
                    _logger.debug(f"[썸네일] 레코드 {idx} - {key}: 경로 없음")

            record = CaptureRecord.from_dict(record_data)
            model.add_record(record)

        _logger.info(f"[썸네일] from_project_dict 완료: 총 {len(model)}개 레코드 복원")
        return model
