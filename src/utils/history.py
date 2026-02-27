"""파일 이력 관리 모듈"""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class FileHistory:
    """최근 파일 이력 관리 클래스"""

    def __init__(self, app_name: str = "IMAS", max_items: int = 10):
        self._app_name = app_name
        self._max_items = max_items
        self._history_dir = self._get_history_dir()
        self._history_file = self._history_dir / "recent_files.json"
        self._history: List[Dict] = []
        self._load()

    def _get_history_dir(self) -> Path:
        """이력 디렉토리 경로 반환"""
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('APPDATA', '~'))
        else:  # macOS, Linux
            base = Path.home() / "Library" / "Application Support"

        history_dir = base / self._app_name
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir

    def _load(self):
        """이력 파일 로드"""
        if self._history_file.exists():
            try:
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._history = data.get('recent_files', [])
            except (json.JSONDecodeError, IOError):
                self._history = []
        else:
            self._history = []

    def save(self):
        """이력 파일 저장"""
        try:
            data = {
                'recent_files': self._history,
                'max_items': self._max_items
            }
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def add(self, file_path: str, position: int = 0):
        """파일 이력 추가"""
        # 기존 항목 제거
        self._history = [h for h in self._history if h.get('path') != file_path]

        # 새 항목 추가
        entry = {
            'path': file_path,
            'last_opened': datetime.now().isoformat(),
            'last_position': position
        }
        self._history.insert(0, entry)

        # 최대 개수 제한
        self._history = self._history[:self._max_items]

        self.save()

    def get_recent_files(self) -> List[str]:
        """최근 파일 경로 목록 반환"""
        return [h.get('path', '') for h in self._history if h.get('path')]

    def get_last_position(self, file_path: str) -> int:
        """파일의 마지막 재생 위치 반환"""
        for h in self._history:
            if h.get('path') == file_path:
                return h.get('last_position', 0)
        return 0

    def update_position(self, file_path: str, position: int):
        """파일의 재생 위치 업데이트"""
        for h in self._history:
            if h.get('path') == file_path:
                h['last_position'] = position
                self.save()
                return

    def clear(self):
        """이력 초기화"""
        self._history = []
        self.save()

    @property
    def items(self) -> List[Dict]:
        """전체 이력 반환"""
        return self._history.copy()
