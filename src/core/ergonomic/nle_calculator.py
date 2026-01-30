"""
NLE (NIOSH Lifting Equation) Calculator

NIOSH Lifting Equation을 사용한 들기 작업 위험도 평가.
RWL (Recommended Weight Limit)과 LI (Lifting Index) 계산.
"""

from dataclasses import dataclass
from typing import Dict, Any

from ..score_calculator import (
    calculate_nle_hm,
    calculate_nle_vm,
    calculate_nle_dm,
    calculate_nle_am,
    calculate_nle_fm,
    calculate_nle_cm,
    calculate_nle_rwl,
    calculate_nle_li,
    get_nle_risk_level,
    NLE_LC,
)


@dataclass
class NLEResult:
    """NLE 평가 결과"""
    # Multipliers
    hm: float  # Horizontal Multiplier
    vm: float  # Vertical Multiplier
    dm: float  # Distance Multiplier
    am: float  # Asymmetry Multiplier
    fm: float  # Frequency Multiplier
    cm: float  # Coupling Multiplier

    # Results
    rwl: float       # Recommended Weight Limit (kg)
    li: float        # Lifting Index
    risk_level: str  # Risk level (safe/increased/high)

    @property
    def lc(self) -> float:
        """Load Constant (항상 23 kg)"""
        return NLE_LC

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'hm': self.hm,
            'vm': self.vm,
            'dm': self.dm,
            'am': self.am,
            'fm': self.fm,
            'cm': self.cm,
            'rwl': self.rwl,
            'li': self.li,
            'risk_level': self.risk_level,
        }


class NLECalculator:
    """NLE (NIOSH Lifting Equation) Calculator"""

    # 위험 수준 정의
    RISK_LEVELS = {
        'safe': 'LI ≤ 1.0: 안전',
        'increased': '1.0 < LI ≤ 3.0: 주의 필요',
        'high': 'LI > 3.0: 즉시 개선 필요',
    }

    # 조치 사항
    ACTIONS = {
        'safe': '현재 작업 조건 유지',
        'increased': '작업 조건 검토 및 개선 권고',
        'high': '즉각적인 작업 조건 개선 필요',
    }

    def calculate_hm(self, h: float) -> float:
        """HM (Horizontal Multiplier) 계산"""
        return calculate_nle_hm(h)

    def calculate_vm(self, v: float) -> float:
        """VM (Vertical Multiplier) 계산"""
        return calculate_nle_vm(v)

    def calculate_dm(self, d: float) -> float:
        """DM (Distance Multiplier) 계산"""
        return calculate_nle_dm(d)

    def calculate_am(self, a: float) -> float:
        """AM (Asymmetry Multiplier) 계산"""
        return calculate_nle_am(a)

    def calculate_fm(self, frequency: float, duration_hours: float = 1.0, v: float = 75.0) -> float:
        """FM (Frequency Multiplier) 계산"""
        return calculate_nle_fm(frequency, duration_hours, v)

    def calculate_cm(self, coupling: int, v: float = 75.0) -> float:
        """CM (Coupling Multiplier) 계산"""
        return calculate_nle_cm(coupling, v)

    def get_risk_level(self, li: float) -> str:
        """LI에 따른 위험 수준 반환"""
        return get_nle_risk_level(li)

    def get_action_required(self, risk_level: str) -> str:
        """위험 수준에 따른 조치 사항 반환"""
        return self.ACTIONS.get(risk_level, '평가 필요')

    def calculate(
        self,
        h: float = 25.0,
        v: float = 75.0,
        d: float = 25.0,
        a: float = 0.0,
        frequency: float = 1.0,
        duration_hours: float = 1.0,
        coupling: int = 1,
        load: float = 0.0,
    ) -> NLEResult:
        """
        NLE 평가 계산

        Args:
            h: 수평 거리 (cm), 손과 척추 중심선 사이 거리
            v: 수직 높이 (cm), 손 위치의 바닥으로부터 높이
            d: 이동 거리 (cm), 들기 시작과 끝의 수직 거리
            a: 비틀림 각도 (°), 몸통 비틀림 각도
            frequency: 빈도 (회/분), 분당 들기 횟수
            duration_hours: 작업 지속 시간 (시간)
            coupling: 손잡이 품질 (1=Good, 2=Fair, 3=Poor)
            load: 실제 중량 (kg)

        Returns:
            NLEResult: 평가 결과
        """
        # Multipliers 계산
        hm = self.calculate_hm(h)
        vm = self.calculate_vm(v)
        dm = self.calculate_dm(d)
        am = self.calculate_am(a)
        fm = self.calculate_fm(frequency, duration_hours, v)
        cm = self.calculate_cm(coupling, v)

        # RWL 계산
        rwl = calculate_nle_rwl(h, v, d, a, frequency, duration_hours, coupling)

        # LI 계산
        li = calculate_nle_li(load, rwl)

        # Risk level
        risk_level = self.get_risk_level(li)

        return NLEResult(
            hm=round(hm, 3),
            vm=round(vm, 3),
            dm=round(dm, 3),
            am=round(am, 3),
            fm=round(fm, 3),
            cm=round(cm, 3),
            rwl=round(rwl, 2),
            li=round(li, 2),
            risk_level=risk_level,
        )
