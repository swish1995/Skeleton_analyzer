"""인체 포즈 감지 모듈"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, List
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os


@dataclass
class PoseResult:
    """포즈 감지 결과"""
    pose_detected: bool
    landmarks: Optional[List] = None
    world_landmarks: Optional[List] = None


class PoseDetector:
    """MediaPipe 기반 인체 포즈 감지 클래스"""

    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker.task")

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        """
        PoseDetector 초기화

        Args:
            min_detection_confidence: 최소 감지 신뢰도
            min_tracking_confidence: 최소 추적 신뢰도
        """
        self._min_detection_confidence = min_detection_confidence
        self._min_tracking_confidence = min_tracking_confidence
        self._landmarker = None
        self._initialize()

    def _download_model(self):
        """모델 파일 다운로드"""
        if not os.path.exists(self.MODEL_PATH):
            urllib.request.urlretrieve(self.MODEL_URL, self.MODEL_PATH)

    def _initialize(self):
        """MediaPipe PoseLandmarker 초기화"""
        self._download_model()

        base_options = python.BaseOptions(model_asset_path=self.MODEL_PATH)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=self._min_detection_confidence,
            min_tracking_confidence=self._min_tracking_confidence
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def detect(self, image: np.ndarray) -> PoseResult:
        """
        이미지에서 인체 포즈 감지

        Args:
            image: BGR 형식의 이미지 (OpenCV)

        Returns:
            PoseResult: 감지 결과
        """
        if self._landmarker is None:
            self._initialize()

        # BGR → RGB 변환
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # MediaPipe Image 생성
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # 포즈 감지
        results = self._landmarker.detect(mp_image)

        if results.pose_landmarks and len(results.pose_landmarks) > 0:
            # 첫 번째 감지된 포즈의 랜드마크
            pose_landmarks = results.pose_landmarks[0]

            # 랜드마크를 리스트로 변환
            landmarks = []
            for lm in pose_landmarks:
                landmarks.append({
                    'x': lm.x,
                    'y': lm.y,
                    'z': lm.z,
                    'visibility': lm.visibility if hasattr(lm, 'visibility') else 1.0
                })

            world_landmarks = None
            if results.pose_world_landmarks and len(results.pose_world_landmarks) > 0:
                world_landmarks = []
                for lm in results.pose_world_landmarks[0]:
                    world_landmarks.append({
                        'x': lm.x,
                        'y': lm.y,
                        'z': lm.z,
                        'visibility': lm.visibility if hasattr(lm, 'visibility') else 1.0
                    })

            return PoseResult(
                pose_detected=True,
                landmarks=landmarks,
                world_landmarks=world_landmarks
            )

        return PoseResult(pose_detected=False, landmarks=None)

    def release(self):
        """리소스 해제"""
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None

    def __del__(self):
        """소멸자"""
        try:
            self.release()
        except:
            pass
