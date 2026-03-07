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

    MODELS = {
        'lite': {
            'url': "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
            'filename': "pose_landmarker_lite.task",
        },
        'full': {
            'url': "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task",
            'filename': "pose_landmarker_full.task",
        },
        'heavy': {
            'url': "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task",
            'filename': "pose_landmarker_heavy.task",
        },
    }

    def __init__(
        self,
        model_type: str = 'lite',
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        """
        PoseDetector 초기화

        Args:
            model_type: 모델 타입 ('lite', 'full', 'heavy')
            min_detection_confidence: 최소 감지 신뢰도
            min_tracking_confidence: 최소 추적 신뢰도
        """
        self._model_type = model_type if model_type in self.MODELS else 'lite'
        self._min_detection_confidence = min_detection_confidence
        self._min_tracking_confidence = min_tracking_confidence
        self._landmarker = None
        self._initialize()

    @property
    def model_type(self) -> str:
        return self._model_type

    def _get_model_path(self) -> str:
        info = self.MODELS[self._model_type]
        return os.path.join(os.path.dirname(__file__), info['filename'])

    def _download_model(self):
        """모델 파일 다운로드"""
        model_path = self._get_model_path()
        if not os.path.exists(model_path):
            url = self.MODELS[self._model_type]['url']
            urllib.request.urlretrieve(url, model_path)

    def _initialize(self):
        """MediaPipe PoseLandmarker 초기화"""
        self._download_model()

        base_options = python.BaseOptions(model_asset_path=self._get_model_path())
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=5,
            min_pose_detection_confidence=self._min_detection_confidence,
            min_tracking_confidence=self._min_tracking_confidence
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def change_model(self, model_type: str):
        """모델 변경"""
        if model_type == self._model_type:
            return
        if model_type not in self.MODELS:
            return
        self.release()
        self._model_type = model_type
        self._initialize()

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
            # 다중 인원 감지 시 가장 큰(가까운) 사람 선택
            best_idx = self._select_closest_pose(results.pose_landmarks)
            pose_landmarks = results.pose_landmarks[best_idx]

            # 랜드마크를 리스트로 변환
            landmarks = []
            for lm in pose_landmarks:
                landmarks.append({
                    'x': lm.x,
                    'y': lm.y,
                    'z': lm.z,
                    'visibility': max(lm.visibility if hasattr(lm, 'visibility') else 1.0, 0.5)
                })

            world_landmarks = None
            if results.pose_world_landmarks and len(results.pose_world_landmarks) > best_idx:
                world_landmarks = []
                for lm in results.pose_world_landmarks[best_idx]:
                    world_landmarks.append({
                        'x': lm.x,
                        'y': lm.y,
                        'z': lm.z,
                        'visibility': max(lm.visibility if hasattr(lm, 'visibility') else 1.0, 0.5)
                    })

            return PoseResult(
                pose_detected=True,
                landmarks=landmarks,
                world_landmarks=world_landmarks
            )

        return PoseResult(pose_detected=False, landmarks=None)

    @staticmethod
    def _select_closest_pose(pose_landmarks_list) -> int:
        """여러 감지된 포즈 중 가장 큰(카메라에 가까운) 사람의 인덱스 반환"""
        if len(pose_landmarks_list) == 1:
            return 0

        best_idx = 0
        best_area = 0.0

        for i, pose_lms in enumerate(pose_landmarks_list):
            # 바운딩 박스 면적으로 크기 판단 (가장 큰 사람 = 가장 가까운 사람)
            xs = [lm.x for lm in pose_lms]
            ys = [lm.y for lm in pose_lms]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            if area > best_area:
                best_area = area
                best_idx = i

        return best_idx

    @staticmethod
    def create_default_landmarks() -> List:
        """기본 포즈 랜드마크 생성 (33개, 정규화 좌표)"""
        # (x, y, z) - z: 음수=카메라쪽(앞), 양수=뒤쪽
        positions = {
            # 얼굴 (코 중심으로 밀집, 얼굴은 몸보다 약간 앞)
            0: (0.500, 0.140, -0.06),   # nose
            1: (0.496, 0.128, -0.04),   # left_eye_inner
            2: (0.492, 0.126, -0.05),   # left_eye
            3: (0.488, 0.128, -0.04),   # left_eye_outer
            4: (0.504, 0.128, -0.04),   # right_eye_inner
            5: (0.508, 0.126, -0.05),   # right_eye
            6: (0.512, 0.128, -0.04),   # right_eye_outer
            7: (0.484, 0.134, -0.01),   # left_ear
            8: (0.516, 0.134, -0.01),   # right_ear
            9: (0.497, 0.148, -0.05),   # mouth_left
            10: (0.503, 0.148, -0.05),  # mouth_right
            # 어깨 (몸통 기준면)
            11: (0.380, 0.220, 0.0),    # left_shoulder
            12: (0.620, 0.220, 0.0),    # right_shoulder
            # 팔 (내린 자세, 약간 앞쪽)
            13: (0.360, 0.370, -0.03),  # left_elbow
            14: (0.640, 0.370, -0.03),  # right_elbow
            15: (0.350, 0.500, -0.05),  # left_wrist
            16: (0.650, 0.500, -0.05),  # right_wrist
            # 손 (손목보다 약간 앞)
            17: (0.340, 0.520, -0.06),  # left_pinky
            18: (0.660, 0.520, -0.06),  # right_pinky
            19: (0.345, 0.520, -0.07),  # left_index
            20: (0.655, 0.520, -0.07),  # right_index
            21: (0.355, 0.510, -0.06),  # left_thumb
            22: (0.645, 0.510, -0.06),  # right_thumb
            # 골반 (어깨와 같은 면)
            23: (0.420, 0.520, 0.0),    # left_hip
            24: (0.580, 0.520, 0.0),    # right_hip
            # 다리 (무릎은 약간 앞)
            25: (0.410, 0.700, -0.03),  # left_knee
            26: (0.590, 0.700, -0.03),  # right_knee
            27: (0.400, 0.880, -0.02),  # left_ankle
            28: (0.600, 0.880, -0.02),  # right_ankle
            # 발 (발끝은 앞, 발꿈치는 뒤)
            29: (0.390, 0.920, 0.02),   # left_heel
            30: (0.610, 0.920, 0.02),   # right_heel
            31: (0.385, 0.900, -0.08),  # left_foot_index
            32: (0.615, 0.900, -0.08),  # right_foot_index
        }

        landmarks = []
        for i in range(33):
            x, y, z = positions.get(i, (0.5, 0.5, 0.0))
            landmarks.append({
                'x': x,
                'y': y,
                'z': z,
                'visibility': 1.0
            })
        return landmarks

    def release(self):
        """리소스 해제"""
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None

    def __del__(self):
        """소멸자"""
        # GC 시점에서 mediapipe 라이브러리가 이미 언로드된 경우
        # bus error 방지를 위해 landmarker 참조만 제거
        self._landmarker = None
