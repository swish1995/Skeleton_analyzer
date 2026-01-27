"""PoseDetector 클래스 테스트"""
import pytest
import numpy as np


class TestPoseDetector:
    """PoseDetector 클래스 테스트"""

    @pytest.fixture
    def detector(self):
        from src.core.pose_detector import PoseDetector
        return PoseDetector()

    @pytest.fixture
    def sample_image(self):
        """테스트용 샘플 이미지 (빈 이미지)"""
        return np.zeros((480, 640, 3), dtype=np.uint8)

    # --- 인체 감지 ---

    def test_detect_pose_returns_result(self, detector, sample_image):
        """포즈 감지가 결과를 반환하는지 테스트"""
        result = detector.detect(sample_image)
        assert result is not None
        assert hasattr(result, 'pose_detected')

    def test_detect_pose_no_person(self, detector, sample_image):
        """인체 없는 이미지에서 감지 테스트"""
        result = detector.detect(sample_image)
        assert result.pose_detected == False

    def test_result_has_landmarks_attribute(self, detector, sample_image):
        """결과에 landmarks 속성이 있는지 테스트"""
        result = detector.detect(sample_image)
        assert hasattr(result, 'landmarks')

    def test_landmarks_is_none_when_no_person(self, detector, sample_image):
        """인체가 없을 때 landmarks가 None인지 테스트"""
        result = detector.detect(sample_image)
        if not result.pose_detected:
            assert result.landmarks is None

    # --- 리소스 관리 ---

    def test_detector_release(self, detector):
        """디텍터 리소스 해제 테스트"""
        detector.release()
        # 해제 후에도 에러 없이 동작해야 함

    def test_detector_can_process_after_release(self, detector, sample_image):
        """해제 후 재사용 가능 테스트"""
        detector.release()
        # 다시 detect 호출 시 재초기화되어야 함
        result = detector.detect(sample_image)
        assert result is not None

    # --- 이미지 형식 ---

    def test_detect_with_rgb_image(self, detector):
        """RGB 이미지 처리 테스트"""
        rgb_image = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect(rgb_image)
        assert result is not None

    def test_detect_with_different_size(self, detector):
        """다른 크기 이미지 처리 테스트"""
        small_image = np.zeros((240, 320, 3), dtype=np.uint8)
        result = detector.detect(small_image)
        assert result is not None

        large_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        result = detector.detect(large_image)
        assert result is not None
