"""
SI (Strain Index) Calculator

Strain Index를 사용한 상지 반복 작업 위험도 평가.
Moore & Garg (1995) 방법론 기반.
"""

from dataclasses import dataclass
from typing import Dict, Any

from ..score_calculator import (
    get_si_multiplier,
    calculate_si_score,
    get_si_risk_level,
    SI_MULTIPLIERS,
)


@dataclass
class SIResult:
    """SI 평가 결과"""
    # Multipliers
    ie_m: float   # Intensity of Exertion Multiplier
    de_m: float   # Duration of Exertion Multiplier
    em_m: float   # Efforts per Minute Multiplier
    hwp_m: float  # Hand/Wrist Posture Multiplier
    sw_m: float   # Speed of Work Multiplier
    dd_m: float   # Duration per Day Multiplier

    # Results
    score: float     # Strain Index Score
    risk_level: str  # Risk level (safe/uncertain/hazardous)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'ie_m': self.ie_m,
            'de_m': self.de_m,
            'em_m': self.em_m,
            'hwp_m': self.hwp_m,
            'sw_m': self.sw_m,
            'dd_m': self.dd_m,
            'score': self.score,
            'risk_level': self.risk_level,
        }


class SICalculator:
    """SI (Strain Index) Calculator"""

    # 위험 수준 정의
    RISK_LEVELS = {
        'safe': '안전',
        'uncertain': '불확실',
        'hazardous': '위험',
    }

    # 조치 사항
    ACTIONS = {
        'safe': '안전',
        'uncertain': '불확실',
        'hazardous': '위험',
    }

    # 파라미터 설명
    PARAM_DESCRIPTIONS = {
        'ie': {
            1: 'Light (가벼움)',
            2: 'Somewhat Hard (약간 힘듦)',
            3: 'Hard (힘듦)',
            4: 'Very Hard (매우 힘듦)',
            5: 'Near Maximal (거의 최대)',
        },
        'de': {
            1: '<10% (10% 미만)',
            2: '10-29%',
            3: '30-49%',
            4: '50-79%',
            5: '≥80% (80% 이상)',
        },
        'em': {
            1: '<4회/분',
            2: '4-8회/분',
            3: '9-14회/분',
            4: '15-19회/분',
            5: '≥20회/분',
        },
        'hwp': {
            1: 'Very Good (매우 좋음)',
            2: 'Good (좋음)',
            3: 'Fair (보통)',
            4: 'Bad (나쁨)',
            5: 'Very Bad (매우 나쁨)',
        },
        'sw': {
            1: 'Very Slow (매우 느림)',
            2: 'Slow (느림)',
            3: 'Fair (보통)',
            4: 'Fast (빠름)',
            5: 'Very Fast (매우 빠름)',
        },
        'dd': {
            1: '≤1시간',
            2: '1-2시간',
            3: '2-4시간',
            4: '4-8시간',
            5: '>8시간',
        },
    }

    def get_multiplier(self, param: str, level: int) -> float:
        """
        SI Multiplier 값 조회

        Args:
            param: 파라미터 이름 ('ie', 'de', 'em', 'hwp', 'sw', 'dd')
            level: 레벨 (1-5)

        Returns:
            Multiplier 값
        """
        return get_si_multiplier(param, level)

    def get_risk_level(self, score: float) -> str:
        """SI Score에 따른 위험 수준 반환"""
        return get_si_risk_level(score)

    def get_action_required(self, risk_level: str) -> str:
        """위험 수준에 따른 조치 사항 반환"""
        return self.ACTIONS.get(risk_level, '평가 필요')

    def get_param_description(self, param: str, level: int) -> str:
        """파라미터 레벨 설명 반환"""
        level = max(1, min(5, level))
        if param in self.PARAM_DESCRIPTIONS:
            return self.PARAM_DESCRIPTIONS[param].get(level, '')
        return ''

    def calculate(
        self,
        ie: int = 1,
        de: int = 1,
        em: int = 1,
        hwp: int = 1,
        sw: int = 1,
        dd: int = 1,
    ) -> SIResult:
        """
        SI 평가 계산

        Args:
            ie: Intensity of Exertion (1-5)
            de: Duration of Exertion (1-5)
            em: Efforts per Minute (1-5)
            hwp: Hand/Wrist Posture (1-5)
            sw: Speed of Work (1-5)
            dd: Duration per Day (1-5)

        Returns:
            SIResult: 평가 결과
        """
        # Multipliers 조회
        ie_m = self.get_multiplier('ie', ie)
        de_m = self.get_multiplier('de', de)
        em_m = self.get_multiplier('em', em)
        hwp_m = self.get_multiplier('hwp', hwp)
        sw_m = self.get_multiplier('sw', sw)
        dd_m = self.get_multiplier('dd', dd)

        # SI Score 계산
        score = calculate_si_score(ie, de, em, hwp, sw, dd)

        # Risk level
        risk_level = self.get_risk_level(score)

        return SIResult(
            ie_m=ie_m,
            de_m=de_m,
            em_m=em_m,
            hwp_m=hwp_m,
            sw_m=sw_m,
            dd_m=dd_m,
            score=round(score, 4),
            risk_level=risk_level,
        )
