"""MovementAnalyzer 및 데이터 클래스 단위 테스트"""
import pytest
import json

# 공통 기본값: AssessmentResult 필수 필드
_BASE_RESULT_DEFAULTS = dict(
    final_score=0,
    risk_level='무시 가능',
    action_required='조치 불필요',
    details={},
)


# ═══════════════════════════════════════════════════════════════
# 1. BodyPartStats 테스트
# ═══════════════════════════════════════════════════════════════

class TestBodyPartStats:

    def test_body_part_stats_initial_values(self):
        """초기값이 모두 0/0.0인지 확인"""
        from src.core.movement_analyzer import BodyPartStats
        stats = BodyPartStats(joint_name='left_shoulder', display_name='좌측 어깨')
        assert stats.total_frames == 0
        assert stats.movement_count == 0
        assert stats.high_risk_frames == 0
        assert stats.high_risk_ratio == 0.0
        assert stats.max_angle == 0.0
        assert stats.min_angle == 0.0
        assert stats.avg_angle == 0.0
        assert stats.cumulative_score == 0.0

    def test_body_part_stats_high_risk_ratio_calculation(self):
        """high_risk_frames / total_frames 계산 정확성"""
        from src.core.movement_analyzer import BodyPartStats
        stats = BodyPartStats(
            joint_name='left_shoulder',
            display_name='좌측 어깨',
            total_frames=10,
            high_risk_frames=3,
            high_risk_ratio=0.3,
        )
        assert stats.high_risk_ratio == pytest.approx(0.3)


# ═══════════════════════════════════════════════════════════════
# 2. MovementAnalyzer 기본 동작
# ═══════════════════════════════════════════════════════════════

class TestMovementAnalyzerBasic:

    @pytest.fixture
    def analyzer(self):
        from src.core.movement_analyzer import MovementAnalyzer
        return MovementAnalyzer()

    @pytest.fixture
    def make_angles(self):
        """13개 관절 각도 딕셔너리를 생성하는 헬퍼"""
        from src.core.angle_calculator import ANGLE_DEFINITIONS

        def _make(default_angle=90.0, overrides=None):
            angles = {name: default_angle for name in ANGLE_DEFINITIONS}
            if overrides:
                angles.update(overrides)
            return angles
        return _make

    @pytest.fixture
    def make_rula_result(self):
        """더미 RULAResult를 생성하는 헬퍼"""
        def _make(**kwargs):
            from src.core.ergonomic.rula_calculator import RULAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return RULAResult(**merged)
        return _make

    @pytest.fixture
    def make_reba_result(self):
        """더미 REBAResult를 생성하는 헬퍼"""
        def _make(**kwargs):
            from src.core.ergonomic.reba_calculator import REBAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return REBAResult(**merged)
        return _make

    def test_analyzer_initialization(self, analyzer):
        """생성 시 13개 관절 모두 초기화 확인"""
        from src.core.angle_calculator import ANGLE_DEFINITIONS
        result = analyzer.get_result()
        assert len(result.body_parts) == len(ANGLE_DEFINITIONS)
        for name in ANGLE_DEFINITIONS:
            assert name in result.body_parts

    def test_analyzer_reset(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """reset() 후 모든 통계가 0으로 초기화"""
        angles = make_angles()
        analyzer.update(angles, make_rula_result(), make_reba_result())
        analyzer.reset()
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.movement_count == 0
            assert stats.total_frames == 0
            assert stats.high_risk_frames == 0

    def test_analyzer_first_frame(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """첫 프레임에서는 움직임 카운트 0 (비교 대상 없음)"""
        angles = make_angles(default_angle=90.0)
        analyzer.update(angles, make_rula_result(), make_reba_result())
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.movement_count == 0

    def test_analyzer_total_frames_increment(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """update() 호출마다 total_frames 증가"""
        angles = make_angles()
        for _ in range(5):
            analyzer.update(angles, make_rula_result(), make_reba_result())
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.total_frames == 5


# ═══════════════════════════════════════════════════════════════
# 3. 움직임 카운팅
# ═══════════════════════════════════════════════════════════════

class TestMovementCounting:

    @pytest.fixture
    def analyzer(self):
        from src.core.movement_analyzer import MovementAnalyzer
        return MovementAnalyzer()

    @pytest.fixture
    def make_angles(self):
        from src.core.angle_calculator import ANGLE_DEFINITIONS

        def _make(default_angle=90.0, overrides=None):
            angles = {name: default_angle for name in ANGLE_DEFINITIONS}
            if overrides:
                angles.update(overrides)
            return angles
        return _make

    @pytest.fixture
    def make_rula_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.rula_calculator import RULAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return RULAResult(**merged)
        return _make

    @pytest.fixture
    def make_reba_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.reba_calculator import REBAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return REBAResult(**merged)
        return _make

    def test_no_movement_below_threshold(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """각도 변화 < 15도면 카운트 증가 안 함"""
        angles1 = make_angles(default_angle=90.0)
        angles2 = make_angles(default_angle=100.0)  # 10도 변화 (< 15)
        analyzer.update(angles1, make_rula_result(), make_reba_result())
        analyzer.update(angles2, make_rula_result(), make_reba_result())
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.movement_count == 0

    def test_movement_above_threshold(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """각도 변화 > 15도면 카운트 1 증가"""
        angles1 = make_angles(default_angle=90.0)
        angles2 = make_angles(default_angle=110.0)  # 20도 변화 (> 15)
        analyzer.update(angles1, make_rula_result(), make_reba_result())
        analyzer.update(angles2, make_rula_result(), make_reba_result())
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.movement_count == 1

    def test_movement_exact_threshold(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """각도 변화 = 15도면 카운트 증가 안 함 (초과만)"""
        angles1 = make_angles(default_angle=90.0)
        angles2 = make_angles(default_angle=105.0)  # 정확히 15도
        analyzer.update(angles1, make_rula_result(), make_reba_result())
        analyzer.update(angles2, make_rula_result(), make_reba_result())
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.movement_count == 0

    def test_multiple_joints_movement(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """여러 관절이 동시에 움직여도 각각 독립 카운팅"""
        angles1 = make_angles(default_angle=90.0)
        # left_shoulder만 20도 변화, right_shoulder는 10도 변화
        angles2 = make_angles(
            default_angle=90.0,
            overrides={'left_shoulder': 110.0, 'right_shoulder': 100.0}
        )
        analyzer.update(angles1, make_rula_result(), make_reba_result())
        analyzer.update(angles2, make_rula_result(), make_reba_result())
        result = analyzer.get_result()
        assert result.body_parts['left_shoulder'].movement_count == 1
        assert result.body_parts['right_shoulder'].movement_count == 0

    def test_continuous_movement(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """연속 3프레임 동안 같은 관절이 계속 움직이면 각 프레임마다 카운트"""
        rula = make_rula_result()
        reba = make_reba_result()
        analyzer.update(make_angles(default_angle=90.0), rula, reba)
        analyzer.update(make_angles(default_angle=110.0), rula, reba)  # +20도
        analyzer.update(make_angles(default_angle=130.0), rula, reba)  # +20도
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.movement_count == 2  # 2번째, 3번째 프레임에서 카운트

    def test_custom_threshold(self, make_angles, make_rula_result, make_reba_result):
        """임계값을 변경했을 때 정상 동작"""
        from src.core.movement_analyzer import MovementAnalyzer
        analyzer = MovementAnalyzer(threshold=10.0)
        rula = make_rula_result()
        reba = make_reba_result()
        angles1 = make_angles(default_angle=90.0)
        angles2 = make_angles(default_angle=102.0)  # 12도 변화 (> 10)
        analyzer.update(angles1, rula, reba)
        analyzer.update(angles2, rula, reba)
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.movement_count == 1


# ═══════════════════════════════════════════════════════════════
# 4. 고위험 자세 집계
# ═══════════════════════════════════════════════════════════════

class TestHighRiskTracking:

    @pytest.fixture
    def analyzer(self):
        from src.core.movement_analyzer import MovementAnalyzer
        return MovementAnalyzer()

    @pytest.fixture
    def make_angles(self):
        from src.core.angle_calculator import ANGLE_DEFINITIONS

        def _make(default_angle=90.0, overrides=None):
            angles = {name: default_angle for name in ANGLE_DEFINITIONS}
            if overrides:
                angles.update(overrides)
            return angles
        return _make

    @pytest.fixture
    def make_rula_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.rula_calculator import RULAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return RULAResult(**merged)
        return _make

    @pytest.fixture
    def make_reba_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.reba_calculator import REBAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return REBAResult(**merged)
        return _make

    def test_rula_high_risk_upper_arm(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """upper_arm 점수 >= 4일 때 고위험 카운트 증가"""
        angles = make_angles()
        rula = make_rula_result(upper_arm_score=4)
        reba = make_reba_result()
        analyzer.update(angles, rula, reba)
        result = analyzer.get_result()
        # left_shoulder, right_shoulder 중 어느 쪽이든 upper_arm 매핑
        assert result.body_parts['left_shoulder'].high_risk_frames >= 1 or \
               result.body_parts['right_shoulder'].high_risk_frames >= 1

    def test_rula_high_risk_neck(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """neck 점수 >= 4일 때 고위험 카운트 증가"""
        angles = make_angles()
        rula = make_rula_result(neck_score=4)
        reba = make_reba_result()
        analyzer.update(angles, rula, reba)
        result = analyzer.get_result()
        assert result.body_parts['neck'].high_risk_frames == 1

    def test_rula_low_risk_not_counted(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """저위험 점수는 고위험 카운트 증가 안 함"""
        angles = make_angles()
        rula = make_rula_result(upper_arm_score=2, neck_score=1)
        reba = make_reba_result()
        analyzer.update(angles, rula, reba)
        result = analyzer.get_result()
        assert result.body_parts['neck'].high_risk_frames == 0
        assert result.body_parts['left_shoulder'].high_risk_frames == 0
        assert result.body_parts['right_shoulder'].high_risk_frames == 0

    def test_high_risk_ratio(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """10프레임 중 3프레임 고위험이면 비율 = 0.3"""
        angles = make_angles()
        reba = make_reba_result()
        for i in range(10):
            if i < 3:
                rula = make_rula_result(neck_score=4)  # 고위험
            else:
                rula = make_rula_result(neck_score=1)  # 저위험
            analyzer.update(angles, rula, reba)
        result = analyzer.get_result()
        assert result.body_parts['neck'].high_risk_ratio == pytest.approx(0.3)


# ═══════════════════════════════════════════════════════════════
# 5. 통계 계산
# ═══════════════════════════════════════════════════════════════

class TestStatisticsCalculation:

    @pytest.fixture
    def analyzer(self):
        from src.core.movement_analyzer import MovementAnalyzer
        return MovementAnalyzer()

    @pytest.fixture
    def make_angles(self):
        from src.core.angle_calculator import ANGLE_DEFINITIONS

        def _make(default_angle=90.0, overrides=None):
            angles = {name: default_angle for name in ANGLE_DEFINITIONS}
            if overrides:
                angles.update(overrides)
            return angles
        return _make

    @pytest.fixture
    def make_rula_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.rula_calculator import RULAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return RULAResult(**merged)
        return _make

    @pytest.fixture
    def make_reba_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.reba_calculator import REBAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return REBAResult(**merged)
        return _make

    def test_max_min_angle_tracking(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """프레임별 최대/최소 각도 추적"""
        rula = make_rula_result()
        reba = make_reba_result()
        analyzer.update(make_angles(default_angle=80.0), rula, reba)
        analyzer.update(make_angles(default_angle=120.0), rula, reba)
        analyzer.update(make_angles(default_angle=100.0), rula, reba)
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.max_angle == pytest.approx(120.0)
            assert stats.min_angle == pytest.approx(80.0)

    def test_average_angle_calculation(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """평균 각도 계산 정확성"""
        rula = make_rula_result()
        reba = make_reba_result()
        analyzer.update(make_angles(default_angle=80.0), rula, reba)
        analyzer.update(make_angles(default_angle=100.0), rula, reba)
        analyzer.update(make_angles(default_angle=120.0), rula, reba)
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.avg_angle == pytest.approx(100.0)

    def test_cumulative_score(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """누적 위험 점수 = 빈도 x 평균 위험도"""
        rula = make_rula_result(neck_score=4)
        reba = make_reba_result()
        # 5프레임, 모두 고위험
        for i in range(5):
            angles = make_angles(default_angle=90.0 + i * 20)  # 매 프레임 20도 변화
            analyzer.update(angles, rula, reba)
        result = analyzer.get_result()
        neck_stats = result.body_parts['neck']
        # movement_count(4) * 평균 위험 점수 = 누적 위험 점수 > 0
        assert neck_stats.cumulative_score > 0


# ═══════════════════════════════════════════════════════════════
# 6. 프레임 샘플링
# ═══════════════════════════════════════════════════════════════

class TestFrameSampling:

    @pytest.fixture
    def make_angles(self):
        from src.core.angle_calculator import ANGLE_DEFINITIONS

        def _make(default_angle=90.0, overrides=None):
            angles = {name: default_angle for name in ANGLE_DEFINITIONS}
            if overrides:
                angles.update(overrides)
            return angles
        return _make

    @pytest.fixture
    def make_rula_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.rula_calculator import RULAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return RULAResult(**merged)
        return _make

    @pytest.fixture
    def make_reba_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.reba_calculator import REBAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return REBAResult(**merged)
        return _make

    def test_sample_interval_1(self, make_angles, make_rula_result, make_reba_result):
        """interval=1이면 모든 프레임 분석"""
        from src.core.movement_analyzer import MovementAnalyzer
        analyzer = MovementAnalyzer(sample_interval=1)
        rula = make_rula_result()
        reba = make_reba_result()
        for i in range(10):
            analyzer.update(make_angles(), rula, reba, frame_index=i)
        result = analyzer.get_result()
        assert result.analyzed_frames == 10

    def test_sample_interval_2(self, make_angles, make_rula_result, make_reba_result):
        """interval=2이면 매 2프레임만 분석"""
        from src.core.movement_analyzer import MovementAnalyzer
        analyzer = MovementAnalyzer(sample_interval=2)
        rula = make_rula_result()
        reba = make_reba_result()
        for i in range(10):
            analyzer.update(make_angles(), rula, reba, frame_index=i)
        result = analyzer.get_result()
        assert result.analyzed_frames == 5  # 0, 2, 4, 6, 8

    def test_sample_interval_3(self, make_angles, make_rula_result, make_reba_result):
        """interval=3이면 매 3프레임만 분석"""
        from src.core.movement_analyzer import MovementAnalyzer
        analyzer = MovementAnalyzer(sample_interval=3)
        rula = make_rula_result()
        reba = make_reba_result()
        for i in range(9):
            analyzer.update(make_angles(), rula, reba, frame_index=i)
        result = analyzer.get_result()
        assert result.analyzed_frames == 3  # 0, 3, 6

    def test_sampling_movement_continuity(self, make_angles, make_rula_result, make_reba_result):
        """샘플링 시에도 이전 분석 프레임 대비 각도 변화 비교"""
        from src.core.movement_analyzer import MovementAnalyzer
        analyzer = MovementAnalyzer(sample_interval=2)
        rula = make_rula_result()
        reba = make_reba_result()
        # frame 0: 90도, frame 1: 건너뜀, frame 2: 130도 (이전 분석 프레임 대비 40도 변화)
        analyzer.update(make_angles(default_angle=90.0), rula, reba, frame_index=0)
        analyzer.update(make_angles(default_angle=110.0), rula, reba, frame_index=1)  # 스킵
        analyzer.update(make_angles(default_angle=130.0), rula, reba, frame_index=2)  # 90 → 130 = 40도
        result = analyzer.get_result()
        for stats in result.body_parts.values():
            assert stats.movement_count == 1  # 90 → 130 비교


# ═══════════════════════════════════════════════════════════════
# 7. 결과 조회
# ═══════════════════════════════════════════════════════════════

class TestResultRetrieval:

    @pytest.fixture
    def analyzer(self):
        from src.core.movement_analyzer import MovementAnalyzer
        return MovementAnalyzer()

    @pytest.fixture
    def make_angles(self):
        from src.core.angle_calculator import ANGLE_DEFINITIONS

        def _make(default_angle=90.0, overrides=None):
            angles = {name: default_angle for name in ANGLE_DEFINITIONS}
            if overrides:
                angles.update(overrides)
            return angles
        return _make

    @pytest.fixture
    def make_rula_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.rula_calculator import RULAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return RULAResult(**merged)
        return _make

    @pytest.fixture
    def make_reba_result(self):
        def _make(**kwargs):
            from src.core.ergonomic.reba_calculator import REBAResult
            merged = {**_BASE_RESULT_DEFAULTS, **kwargs}
            return REBAResult(**merged)
        return _make

    def test_get_result(self, analyzer):
        """MovementAnalysisResult 반환 구조 확인"""
        from src.core.movement_analyzer import MovementAnalysisResult
        result = analyzer.get_result()
        assert isinstance(result, MovementAnalysisResult)
        assert hasattr(result, 'body_parts')
        assert hasattr(result, 'total_frames')
        assert hasattr(result, 'analyzed_frames')
        assert hasattr(result, 'skipped_frames')
        assert hasattr(result, 'sample_interval')
        assert hasattr(result, 'duration_seconds')

    def test_get_sorted_by_movement(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """움직임 횟수 내림차순 정렬"""
        rula = make_rula_result()
        reba = make_reba_result()
        # left_shoulder에 큰 변화 부여
        analyzer.update(make_angles(default_angle=90.0), rula, reba)
        analyzer.update(
            make_angles(default_angle=90.0, overrides={'left_shoulder': 120.0}),
            rula, reba
        )
        result = analyzer.get_result()
        sorted_parts = result.get_sorted_by_movement()
        # 첫 번째 항목이 가장 많이 움직인 관절
        assert sorted_parts[0].movement_count >= sorted_parts[-1].movement_count

    def test_get_sorted_by_risk(self, analyzer, make_angles, make_rula_result, make_reba_result):
        """고위험 비율 내림차순 정렬"""
        angles = make_angles()
        # neck만 고위험
        rula = make_rula_result(neck_score=4)
        reba = make_reba_result()
        analyzer.update(angles, rula, reba)
        result = analyzer.get_result()
        sorted_parts = result.get_sorted_by_risk()
        assert sorted_parts[0].high_risk_ratio >= sorted_parts[-1].high_risk_ratio

    def test_empty_result(self, analyzer):
        """update() 없이 get_result() 호출 시 빈 결과"""
        result = analyzer.get_result()
        assert result.total_frames == 0
        assert result.analyzed_frames == 0
        for stats in result.body_parts.values():
            assert stats.movement_count == 0
            assert stats.total_frames == 0


# ═══════════════════════════════════════════════════════════════
# 8. 직렬화
# ═══════════════════════════════════════════════════════════════

class TestSerialization:

    @pytest.fixture
    def analyzer_with_data(self):
        from src.core.movement_analyzer import MovementAnalyzer
        from src.core.angle_calculator import ANGLE_DEFINITIONS
        from src.core.ergonomic.rula_calculator import RULAResult
        from src.core.ergonomic.reba_calculator import REBAResult

        analyzer = MovementAnalyzer()
        angles_base = {name: 90.0 for name in ANGLE_DEFINITIONS}
        angles_moved = {name: 120.0 for name in ANGLE_DEFINITIONS}

        rula = RULAResult(**_BASE_RESULT_DEFAULTS, neck_score=4, upper_arm_score=3)
        reba = REBAResult(**_BASE_RESULT_DEFAULTS, neck_score=3)

        analyzer.update(angles_base, rula, reba)
        analyzer.update(angles_moved, rula, reba)
        analyzer.update(angles_base, rula, reba)
        return analyzer

    def test_result_to_dict(self, analyzer_with_data):
        """결과를 딕셔너리로 변환"""
        result = analyzer_with_data.get_result()
        d = result.to_dict()
        assert isinstance(d, dict)
        assert 'body_parts' in d
        assert 'total_frames' in d
        assert 'analyzed_frames' in d
        assert 'skipped_frames' in d
        assert 'sample_interval' in d

    def test_result_from_dict(self, analyzer_with_data):
        """딕셔너리에서 결과 복원"""
        from src.core.movement_analyzer import MovementAnalysisResult
        result = analyzer_with_data.get_result()
        d = result.to_dict()
        restored = MovementAnalysisResult.from_dict(d)
        assert isinstance(restored, MovementAnalysisResult)
        assert len(restored.body_parts) == len(result.body_parts)

    def test_round_trip_serialization(self, analyzer_with_data):
        """저장 후 로드 시 데이터 동일"""
        from src.core.movement_analyzer import MovementAnalysisResult
        result = analyzer_with_data.get_result()
        d = result.to_dict()
        json_str = json.dumps(d, ensure_ascii=False)
        d2 = json.loads(json_str)
        restored = MovementAnalysisResult.from_dict(d2)

        assert restored.total_frames == result.total_frames
        assert restored.analyzed_frames == result.analyzed_frames
        assert restored.skipped_frames == result.skipped_frames

        for name, stats in result.body_parts.items():
            restored_stats = restored.body_parts[name]
            assert restored_stats.movement_count == stats.movement_count
            assert restored_stats.high_risk_frames == stats.high_risk_frames
            assert restored_stats.total_frames == stats.total_frames
            assert restored_stats.high_risk_ratio == pytest.approx(stats.high_risk_ratio)
            assert restored_stats.max_angle == pytest.approx(stats.max_angle)
            assert restored_stats.min_angle == pytest.approx(stats.min_angle)
            assert restored_stats.avg_angle == pytest.approx(stats.avg_angle)
