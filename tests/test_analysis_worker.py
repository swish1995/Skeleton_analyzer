"""AnalysisWorker (QThread) 단위 테스트"""
import sys
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

# cv2, mediapipe를 미리 모킹하여 import 에러 방지
cv2_mock = MagicMock()
cv2_mock.CAP_PROP_FRAME_COUNT = 7
cv2_mock.CAP_PROP_FPS = 5
mediapipe_mock = MagicMock()
sys.modules.setdefault('cv2', cv2_mock)
sys.modules.setdefault('mediapipe', mediapipe_mock)
sys.modules.setdefault('mediapipe.tasks', mediapipe_mock.tasks)
sys.modules.setdefault('mediapipe.tasks.python', mediapipe_mock.tasks.python)
sys.modules.setdefault('mediapipe.tasks.python.vision', mediapipe_mock.tasks.python.vision)


class TestAnalysisWorker:

    @pytest.fixture(autouse=True)
    def reset_cv2_mock(self):
        """각 테스트 전에 cv2 모킹 초기화"""
        cv2_mock.reset_mock()
        cv2_mock.CAP_PROP_FRAME_COUNT = 7
        cv2_mock.CAP_PROP_FPS = 5
        yield

    def _make_capture(self, num_frames=10, fps=30.0):
        """cv2.VideoCapture 모킹 생성"""
        cap = MagicMock()
        cap.isOpened.return_value = True
        cap.get.side_effect = lambda prop: {
            cv2_mock.CAP_PROP_FRAME_COUNT: float(num_frames),
            cv2_mock.CAP_PROP_FPS: fps,
        }.get(prop, 0.0)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        call_count = [0]

        def read_side_effect():
            call_count[0] += 1
            if call_count[0] <= num_frames:
                return True, frame.copy()
            return False, None

        cap.read.side_effect = read_side_effect
        cap._call_count = call_count
        return cap

    def _make_pose_result(self, success=True):
        """포즈 감지 결과 모킹"""
        result = MagicMock()
        result.pose_detected = success
        if success:
            landmarks = [{'x': 0.5, 'y': 0.5, 'z': 0.0, 'visibility': 0.9} for _ in range(33)]
            result.landmarks = landmarks
        else:
            result.landmarks = None
        return result

    def _make_assessment_result(self):
        """RULA/REBA 평가 결과 모킹 (점수 속성을 정수로 설정)"""
        result = MagicMock()
        result.upper_arm_score = 2
        result.lower_arm_score = 2
        result.wrist_score = 1
        result.neck_score = 2
        result.trunk_score = 2
        result.leg_score = 1
        return result

    def test_worker_emits_progress(self):
        """프레임 처리마다 progress_updated 시그널 emit"""
        from src.core.analysis_worker import AnalysisWorker

        cap = self._make_capture(num_frames=10)
        cv2_mock.VideoCapture.return_value = cap
        pose_success = self._make_pose_result(success=True)

        with patch('src.core.analysis_worker.PoseDetector') as MockDetector, \
             patch('src.core.analysis_worker.RULACalculator') as MockRula, \
             patch('src.core.analysis_worker.REBACalculator') as MockReba:

            MockDetector.return_value.detect.return_value = pose_success
            MockRula.return_value.calculate.return_value = self._make_assessment_result()
            MockReba.return_value.calculate.return_value = self._make_assessment_result()

            worker = AnalysisWorker(video_path='/tmp/test.mp4')
            progress_calls = []
            worker.progress_updated.connect(lambda cur, total: progress_calls.append((cur, total)))
            worker.run()

            assert len(progress_calls) > 0
            assert progress_calls[-1][0] == progress_calls[-1][1]

    def test_worker_emits_completed(self):
        """전체 스캔 완료 시 analysis_completed 시그널 emit"""
        from src.core.analysis_worker import AnalysisWorker
        from src.core.movement_analyzer import MovementAnalysisResult

        cap = self._make_capture(num_frames=10)
        cv2_mock.VideoCapture.return_value = cap
        pose_success = self._make_pose_result(success=True)

        with patch('src.core.analysis_worker.PoseDetector') as MockDetector, \
             patch('src.core.analysis_worker.RULACalculator') as MockRula, \
             patch('src.core.analysis_worker.REBACalculator') as MockReba:

            MockDetector.return_value.detect.return_value = pose_success
            MockRula.return_value.calculate.return_value = self._make_assessment_result()
            MockReba.return_value.calculate.return_value = self._make_assessment_result()

            worker = AnalysisWorker(video_path='/tmp/test.mp4')
            completed_results = []
            worker.analysis_completed.connect(lambda r: completed_results.append(r))
            worker.run()

            assert len(completed_results) == 1
            assert isinstance(completed_results[0], MovementAnalysisResult)

    def test_worker_stop(self):
        """stop() 호출 시 안전하게 중단"""
        from src.core.analysis_worker import AnalysisWorker

        cap = self._make_capture(num_frames=1000)
        cv2_mock.VideoCapture.return_value = cap
        pose_success = self._make_pose_result(success=True)

        with patch('src.core.analysis_worker.PoseDetector') as MockDetector, \
             patch('src.core.analysis_worker.RULACalculator') as MockRula, \
             patch('src.core.analysis_worker.REBACalculator') as MockReba:

            MockDetector.return_value.detect.return_value = pose_success
            MockRula.return_value.calculate.return_value = self._make_assessment_result()
            MockReba.return_value.calculate.return_value = self._make_assessment_result()

            worker = AnalysisWorker(video_path='/tmp/test.mp4')

            original_read = cap.read.side_effect
            read_count = [0]

            def read_and_stop():
                read_count[0] += 1
                if read_count[0] == 3:
                    worker.stop()
                return original_read()

            cap.read.side_effect = read_and_stop
            worker.run()

            # 1000프레임이 아닌, 3~4프레임에서 중단됨
            assert read_count[0] <= 5

    def test_worker_stop_cleans_resources(self):
        """중단 시 cv2.VideoCapture, PoseDetector 해제"""
        from src.core.analysis_worker import AnalysisWorker

        cap = self._make_capture(num_frames=10)
        cv2_mock.VideoCapture.return_value = cap
        pose_success = self._make_pose_result(success=True)

        with patch('src.core.analysis_worker.PoseDetector') as MockDetector, \
             patch('src.core.analysis_worker.RULACalculator') as MockRula, \
             patch('src.core.analysis_worker.REBACalculator') as MockReba:

            mock_detector_inst = MockDetector.return_value
            mock_detector_inst.detect.return_value = pose_success
            MockRula.return_value.calculate.return_value = self._make_assessment_result()
            MockReba.return_value.calculate.return_value = self._make_assessment_result()

            worker = AnalysisWorker(video_path='/tmp/test.mp4')
            worker.run()

            cap.release.assert_called_once()
            mock_detector_inst.release.assert_called_once()

    def test_worker_skip_failed_frames(self):
        """포즈 감지 실패 프레임 스킵 후 계속 진행"""
        from src.core.analysis_worker import AnalysisWorker

        cap = self._make_capture(num_frames=5)
        cv2_mock.VideoCapture.return_value = cap

        pose_success = self._make_pose_result(success=True)
        pose_fail = self._make_pose_result(success=False)

        with patch('src.core.analysis_worker.PoseDetector') as MockDetector, \
             patch('src.core.analysis_worker.RULACalculator') as MockRula, \
             patch('src.core.analysis_worker.REBACalculator') as MockReba:

            # 프레임 1,3 성공, 프레임 2,4,5 실패
            MockDetector.return_value.detect.side_effect = [
                pose_success, pose_fail, pose_success, pose_fail, pose_fail,
            ]
            MockRula.return_value.calculate.return_value = self._make_assessment_result()
            MockReba.return_value.calculate.return_value = self._make_assessment_result()

            worker = AnalysisWorker(video_path='/tmp/test.mp4')
            completed_results = []
            worker.analysis_completed.connect(lambda r: completed_results.append(r))
            worker.run()

            assert len(completed_results) == 1
            result = completed_results[0]
            assert result.total_frames == 5
            assert result.analyzed_frames == 2
            assert result.skipped_frames == 3

    def test_worker_result_analyzed_frames(self):
        """analyzed_frames가 실제 성공 프레임 수와 일치"""
        from src.core.analysis_worker import AnalysisWorker

        cap = self._make_capture(num_frames=10)
        cv2_mock.VideoCapture.return_value = cap
        pose_success = self._make_pose_result(success=True)

        with patch('src.core.analysis_worker.PoseDetector') as MockDetector, \
             patch('src.core.analysis_worker.RULACalculator') as MockRula, \
             patch('src.core.analysis_worker.REBACalculator') as MockReba:

            MockDetector.return_value.detect.return_value = pose_success
            MockRula.return_value.calculate.return_value = self._make_assessment_result()
            MockReba.return_value.calculate.return_value = self._make_assessment_result()

            worker = AnalysisWorker(video_path='/tmp/test.mp4')
            completed_results = []
            worker.analysis_completed.connect(lambda r: completed_results.append(r))
            worker.run()

            result = completed_results[0]
            assert result.analyzed_frames == 10
            assert result.skipped_frames == 0

    def test_worker_sample_interval(self):
        """샘플링 간격에 따라 분석 프레임 수 정확"""
        from src.core.analysis_worker import AnalysisWorker

        cap = self._make_capture(num_frames=10)
        cv2_mock.VideoCapture.return_value = cap
        pose_success = self._make_pose_result(success=True)

        with patch('src.core.analysis_worker.PoseDetector') as MockDetector, \
             patch('src.core.analysis_worker.RULACalculator') as MockRula, \
             patch('src.core.analysis_worker.REBACalculator') as MockReba:

            MockDetector.return_value.detect.return_value = pose_success
            MockRula.return_value.calculate.return_value = self._make_assessment_result()
            MockReba.return_value.calculate.return_value = self._make_assessment_result()

            worker = AnalysisWorker(video_path='/tmp/test.mp4', sample_interval=2)
            completed_results = []
            worker.analysis_completed.connect(lambda r: completed_results.append(r))
            worker.run()

            result = completed_results[0]
            # 10프레임 중 매 2프레임: 0,2,4,6,8 = 5프레임
            assert result.analyzed_frames == 5
            assert result.sample_interval == 2
