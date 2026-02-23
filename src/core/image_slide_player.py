"""이미지 슬라이드 플레이어 모듈

폴더 또는 압축 파일에서 이미지를 로드하여 슬라이드쇼 형태로 제공합니다.
"""

import re
import shutil
from collections import OrderedDict
from pathlib import Path
from typing import Optional, List

import cv2
import numpy as np


# 지원하는 이미지 확장자
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}


def _natural_sort_key(path: Path):
    """파일명을 자연순 정렬하기 위한 키 함수"""
    name = path.stem.lower()
    parts = re.split(r'(\d+)', name)
    result = []
    for part in parts:
        if part.isdigit():
            result.append(int(part))
        else:
            result.append(part)
    return result


class ImageSlidePlayer:
    """이미지 슬라이드 플레이어

    폴더 또는 압축 파일에서 이미지를 로드하여
    인덱스 기반 네비게이션을 제공합니다.
    """

    CACHE_SIZE = 5
    TEMP_BASE_DIR = "temp_images"

    def __init__(self):
        self._image_paths: List[Path] = []
        self._current_index: int = 0
        self._source_type: Optional[str] = None  # 'folder' | 'archive'
        self._source_path: Optional[str] = None   # 원본 경로
        self._temp_dir: Optional[Path] = None      # 압축 해제 임시 디렉토리
        self._cache: OrderedDict[int, np.ndarray] = OrderedDict()

    # === 속성 ===

    @property
    def is_loaded(self) -> bool:
        """이미지가 로드되었는지 확인"""
        return len(self._image_paths) > 0

    @property
    def image_count(self) -> int:
        """총 이미지 수"""
        return len(self._image_paths)

    @property
    def current_index(self) -> int:
        """현재 이미지 인덱스"""
        return self._current_index

    @property
    def current_image_path(self) -> Optional[str]:
        """현재 이미지 파일 경로"""
        if self.is_loaded and 0 <= self._current_index < self.image_count:
            return str(self._image_paths[self._current_index])
        return None

    @property
    def source_type(self) -> Optional[str]:
        """소스 타입 ('folder' | 'archive')"""
        return self._source_type

    @property
    def source_path(self) -> Optional[str]:
        """원본 소스 경로"""
        return self._source_path

    @property
    def temp_dir(self) -> Optional[Path]:
        """압축 해제 임시 디렉토리"""
        return self._temp_dir

    # === 로드 ===

    def set_loaded_folder(self, folder_path: str, image_paths: List[Path]):
        """외부에서 스캔 완료된 이미지 경로 목록으로 폴더 모드 설정

        LoadWorker에서 미리 스캔한 결과를 받아 세팅합니다.

        Args:
            folder_path: 원본 폴더 경로
            image_paths: 스캔된 이미지 경로 목록 (정렬 완료)
        """
        self.release()
        self._image_paths = list(image_paths)
        self._current_index = 0
        self._source_type = 'folder'
        self._source_path = folder_path

    def set_loaded_archive(self, archive_path: str, image_paths: List[Path],
                           temp_dir: Path):
        """외부에서 압축 해제 완료된 결과로 아카이브 모드 설정

        LoadWorker에서 미리 압축 해제 + 스캔한 결과를 받아 세팅합니다.

        Args:
            archive_path: 원본 압축 파일 경로
            image_paths: 스캔된 이미지 경로 목록 (정렬 완료)
            temp_dir: 압축 해제 임시 디렉토리
        """
        self.release()
        self._image_paths = list(image_paths)
        self._current_index = 0
        self._source_type = 'archive'
        self._source_path = archive_path
        self._temp_dir = temp_dir

    # === 네비게이션 ===

    def get_frame(self, index: int) -> Optional[np.ndarray]:
        """특정 인덱스의 이미지를 numpy 배열로 반환

        Args:
            index: 이미지 인덱스

        Returns:
            BGR 형식의 numpy 배열 또는 None
        """
        if not self.is_loaded or index < 0 or index >= self.image_count:
            return None

        # 캐시 확인
        if index in self._cache:
            self._cache.move_to_end(index)
            return self._cache[index]

        # 이미지 로드
        img = cv2.imread(str(self._image_paths[index]))
        if img is None:
            return None

        # 캐시에 추가
        self._cache[index] = img
        if len(self._cache) > self.CACHE_SIZE:
            self._cache.popitem(last=False)

        return img

    def read_frame(self) -> Optional[np.ndarray]:
        """현재 인덱스의 프레임 반환 (VideoPlayer 인터페이스 호환)"""
        return self.get_frame(self._current_index)

    def next(self) -> Optional[np.ndarray]:
        """다음 이미지로 이동

        Returns:
            다음 이미지 또는 None (마지막인 경우 마지막 이미지 유지)
        """
        if not self.is_loaded:
            return None

        if self._current_index < self.image_count - 1:
            self._current_index += 1

        return self.get_frame(self._current_index)

    def prev(self) -> Optional[np.ndarray]:
        """이전 이미지로 이동

        Returns:
            이전 이미지 또는 None (첫 번째인 경우 첫 이미지 유지)
        """
        if not self.is_loaded:
            return None

        if self._current_index > 0:
            self._current_index -= 1

        return self.get_frame(self._current_index)

    def seek(self, index: int) -> Optional[np.ndarray]:
        """특정 인덱스로 이동

        Args:
            index: 이동할 인덱스 (범위 내로 클램핑됨)

        Returns:
            해당 인덱스의 이미지 또는 None
        """
        if not self.is_loaded:
            return None

        self._current_index = max(0, min(index, self.image_count - 1))
        return self.get_frame(self._current_index)

    # === 정리 ===

    def cleanup_temp(self):
        """압축 해제 임시 디렉토리 삭제"""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

    def release(self):
        """리소스 해제"""
        self.cleanup_temp()
        self._image_paths.clear()
        self._current_index = 0
        self._source_type = None
        self._source_path = None
        self._cache.clear()

    @staticmethod
    def cleanup_all_temp():
        """모든 임시 이미지 디렉토리 삭제"""
        temp_base = Path(ImageSlidePlayer.TEMP_BASE_DIR)
        if temp_base.exists():
            shutil.rmtree(temp_base, ignore_errors=True)

    def __del__(self):
        """소멸자"""
        self.release()
