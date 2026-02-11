"""분석 워커 스레드 - 동영상 전체 프레임 순차 스캔"""
import time

import cv2
from PyQt6.QtCore import QThread, pyqtSignal

from src.core.pose_detector import PoseDetector
from src.core.angle_calculator import AngleCalculator
from src.core.ergonomic.rula_calculator import RULACalculator
from src.core.ergonomic.reba_calculator import REBACalculator
from src.core.movement_analyzer import MovementAnalyzer, MovementAnalysisResult
from src.core.logger import get_logger


class AnalysisWorker(QThread):
    """동영상 전체 프레임을 순차 스캔하여 움직임 빈도를 분석하는 워커 스레드"""

    progress_updated = pyqtSignal(int, int)       # (current_frame, total_frames)
    analysis_completed = pyqtSignal(object)        # MovementAnalysisResult
    analysis_cancelled = pyqtSignal(object, dict, int, int)  # (partial_result, analyzer_state, frame_index, skipped_frames)
    skipped_updated = pyqtSignal(int)              # skipped_frames_count
    error_occurred = pyqtSignal(str)               # error message

    def __init__(self, video_path: str, sample_interval: int = 1,
                 resume_state: dict = None, resume_frame: int = 0,
                 resume_skipped: int = 0, resume_elapsed: float = 0.0,
                 parent=None):
        super().__init__(parent)
        self._video_path = video_path
        self._sample_interval = sample_interval
        self._resume_state = resume_state
        self._resume_frame = resume_frame
        self._resume_skipped = resume_skipped
        self._resume_elapsed = resume_elapsed
        self._stopped = False
        self._logger = get_logger('analysis_worker')

    def stop(self):
        self._stopped = True

    def run(self):
        start_time = time.time()

        cap = cv2.VideoCapture(self._video_path)
        detector = PoseDetector()
        angle_calc = AngleCalculator()
        rula_calc = RULACalculator()
        reba_calc = REBACalculator()
        analyzer = MovementAnalyzer(sample_interval=self._sample_interval)

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            skipped_frames = self._resume_skipped
            frame_index = self._resume_frame

            # 재개 상태 복원
            if self._resume_state:
                analyzer.load_state(self._resume_state)
                self._logger.info(f"분석 재개: 프레임 {frame_index}/{total_frames}부터")

            # 프레임 위치 이동 (재개 시)
            if frame_index > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

            while not self._stopped:
                ret, frame = cap.read()
                if not ret:
                    break

                # 샘플링: sample_interval에 따라 스킵
                if frame_index % self._sample_interval != 0:
                    frame_index += 1
                    continue

                # 포즈 감지
                pose_result = detector.detect(frame)
                if not pose_result.pose_detected:
                    skipped_frames += 1
                    frame_index += 1
                    self.progress_updated.emit(frame_index, total_frames)
                    self.skipped_updated.emit(skipped_frames)
                    continue

                # 각도 계산
                angles = angle_calc.calculate_all_angles(pose_result.landmarks)

                # RULA/REBA 평가
                landmarks_for_calc = pose_result.landmarks
                rula_result = rula_calc.calculate(angles, landmarks_for_calc)
                reba_result = reba_calc.calculate(angles, landmarks_for_calc)

                # 분석 엔진에 누적
                analyzer.update(angles, rula_result, reba_result)

                frame_index += 1
                self.progress_updated.emit(frame_index, total_frames)

            # 결과 생성 (이전 실행 시간 누적)
            elapsed = time.time() - start_time + self._resume_elapsed
            result = analyzer.get_result()
            result.total_frames = frame_index
            result.skipped_frames = skipped_frames
            result.duration_seconds = elapsed
            result.sample_interval = self._sample_interval

            if self._stopped:
                # 취소 시 부분 결과 + 분석기 상태 전달
                analyzer_state = analyzer.get_state()
                self.analysis_cancelled.emit(result, analyzer_state, frame_index, skipped_frames)
                self._logger.info(f"분석 취소: {frame_index}/{total_frames} 프레임 처리")
            else:
                self.analysis_completed.emit(result)
                self._logger.info(f"분석 완료: {frame_index} 프레임, {elapsed:.1f}초")

        except Exception as e:
            self._logger.error(f"분석 중 오류 발생: {e}", exc_info=True)
            self.error_occurred.emit(str(e))

        finally:
            cap.release()
            detector.release()
