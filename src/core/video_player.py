"""비디오 플레이어 모듈"""
import cv2
import numpy as np
from typing import Optional, Tuple

from src.utils.cv_unicode import VideoCapture as CvVideoCapture


class VideoPlayer:
    """OpenCV 기반 비디오 플레이어 클래스"""

    def __init__(self):
        """VideoPlayer 초기화"""
        self._cap: Optional[CvVideoCapture] = None
        self._is_playing: bool = False
        self._current_frame: int = 0
        self._file_path: Optional[str] = None

    @property
    def is_loaded(self) -> bool:
        """비디오가 로드되었는지 확인"""
        return self._cap is not None and self._cap.isOpened()

    @property
    def is_playing(self) -> bool:
        """재생 중인지 확인"""
        return self._is_playing

    @property
    def fps(self) -> float:
        """초당 프레임 수 반환"""
        if not self.is_loaded:
            return 0.0
        return self._cap.get(cv2.CAP_PROP_FPS)

    @property
    def frame_count(self) -> int:
        """총 프레임 수 반환"""
        if not self.is_loaded:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

    @property
    def duration(self) -> float:
        """총 재생 시간(초) 반환"""
        if not self.is_loaded or self.fps == 0:
            return 0.0
        return self.frame_count / self.fps

    @property
    def size(self) -> Tuple[int, int]:
        """비디오 크기 (width, height) 반환"""
        if not self.is_loaded:
            return (0, 0)
        width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)

    @property
    def current_frame(self) -> int:
        """현재 프레임 위치 반환"""
        return self._current_frame

    @property
    def current_time(self) -> float:
        """현재 재생 시간(초) 반환"""
        if self.fps == 0:
            return 0.0
        return self._current_frame / self.fps

    @property
    def video_path(self) -> Optional[str]:
        """로드된 비디오 파일 경로 반환"""
        return self._file_path

    def load(self, file_path: str) -> bool:
        """
        비디오 파일 로드

        Args:
            file_path: 비디오 파일 경로

        Returns:
            성공 여부
        """
        self.release()

        try:
            self._cap = CvVideoCapture(file_path)
            if not self._cap.isOpened():
                self._cap = None
                return False

            # 실제 비디오 파일인지 확인 (프레임 읽기 시도)
            ret, _ = self._cap.read()
            if not ret:
                self._cap.release()
                self._cap = None
                return False

            # 처음으로 되감기
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._current_frame = 0
            self._file_path = file_path
            return True

        except Exception:
            self._cap = None
            return False

    def read_frame(self) -> Optional[np.ndarray]:
        """
        현재 위치에서 프레임 읽기

        Returns:
            프레임 (BGR 형식) 또는 None
        """
        if not self.is_loaded:
            return None

        ret, frame = self._cap.read()
        if ret:
            self._current_frame += 1
            return frame
        return None

    def seek(self, frame_number: int) -> bool:
        """
        특정 프레임으로 이동

        Args:
            frame_number: 이동할 프레임 번호

        Returns:
            성공 여부
        """
        if not self.is_loaded:
            return False

        # 범위 제한
        frame_number = max(0, min(frame_number, self.frame_count - 1))

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self._current_frame = frame_number
        return True

    def seek_time(self, seconds: float) -> bool:
        """
        특정 시간으로 이동

        Args:
            seconds: 이동할 시간 (초)

        Returns:
            성공 여부
        """
        if self.fps == 0:
            return False
        frame_number = int(seconds * self.fps)
        return self.seek(frame_number)

    def play(self):
        """재생 시작"""
        if self.is_loaded:
            self._is_playing = True

    def pause(self):
        """일시정지"""
        self._is_playing = False

    def toggle_play(self):
        """재생/일시정지 토글"""
        if self._is_playing:
            self.pause()
        else:
            self.play()

    def stop(self):
        """정지 및 처음으로 이동"""
        self._is_playing = False
        self.seek(0)

    def release(self):
        """리소스 해제"""
        if self._cap:
            self._cap.release()
            self._cap = None
        self._is_playing = False
        self._current_frame = 0
        self._file_path = None

    def __del__(self):
        """소멸자"""
        self.release()
