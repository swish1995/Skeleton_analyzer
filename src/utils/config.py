"""설정 관리 모듈"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """애플리케이션 설정 관리 클래스"""

    def __init__(self, app_name: str = "SkeletonAnalyzer"):
        self._app_name = app_name
        self._config_dir = self._get_config_dir()
        self._config_file = self._config_dir / "config.json"
        self._config: Dict[str, Any] = {}
        self._load()

    def _get_config_dir(self) -> Path:
        """설정 디렉토리 경로 반환"""
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('APPDATA', '~'))
        else:  # macOS, Linux
            base = Path.home() / "Library" / "Application Support"

        config_dir = base / self._app_name
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _load(self):
        """설정 파일 로드"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = {}
        else:
            self._config = {}

    def save(self):
        """설정 파일 저장"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """설정 값 저장"""
        self._config[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._config.get(key)

    def __setitem__(self, key: str, value: Any):
        self._config[key] = value
