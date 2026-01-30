"""
로깅 시스템

로테이팅 파일 로그와 콘솔 로그를 제공합니다.

설정:
    - 파일 크기: 2MB
    - 백업 개수: 10개
    - 개발 환경: DEBUG 레벨
    - 상용 환경: INFO 레벨

환경 변수:
    - SKELETON_ANALYZER_LOG_LEVEL: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
    - SKELETON_ANALYZER_ENV: 환경 (development, production)
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# 로그 설정 상수
LOG_DIR = Path.home() / '.skeleton-analyzer' / 'logs'
LOG_FILE = 'app.log'
MAX_BYTES = 2 * 1024 * 1024  # 2MB
BACKUP_COUNT = 10

# 로그 포맷
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def _get_log_level() -> int:
    """환경에 따른 로그 레벨 결정"""
    # 명시적 레벨 설정 확인
    level_str = os.environ.get('SKELETON_ANALYZER_LOG_LEVEL', '').upper()
    if level_str:
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
        }
        if level_str in level_map:
            return level_map[level_str]

    # 환경에 따른 기본 레벨
    env = os.environ.get('SKELETON_ANALYZER_ENV', 'development').lower()
    if env == 'production':
        return logging.INFO
    return logging.DEBUG


def _ensure_log_dir() -> Path:
    """로그 디렉토리 생성"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def setup_logging() -> logging.Logger:
    """
    로깅 시스템 초기화

    Returns:
        루트 로거
    """
    log_dir = _ensure_log_dir()
    log_file = log_dir / LOG_FILE
    log_level = _get_log_level()

    # 루트 로거 설정
    root_logger = logging.getLogger('skeleton_analyzer')
    root_logger.setLevel(log_level)

    # 기존 핸들러 제거 (중복 방지)
    root_logger.handlers.clear()

    # 포맷터
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # 로테이팅 파일 핸들러
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding='utf-8',
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 콘솔 핸들러 (개발 환경에서만)
    env = os.environ.get('SKELETON_ANALYZER_ENV', 'development').lower()
    if env != 'production':
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    root_logger.info(f"로깅 시스템 초기화 완료 (레벨: {logging.getLevelName(log_level)}, 파일: {log_file})")

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    로거 인스턴스 반환

    Args:
        name: 로거 이름 (모듈명). None이면 루트 로거 반환.

    Returns:
        로거 인스턴스
    """
    if name:
        return logging.getLogger(f'skeleton_analyzer.{name}')
    return logging.getLogger('skeleton_analyzer')
