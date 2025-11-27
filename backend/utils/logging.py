"""로깅 관리 모듈"""

import logging
from pathlib import Path

from backend.config.settings import settings


class LogManager:
    """로깅 설정 및 관리를 담당하는 클래스"""

    _initialized = False

    @classmethod
    def setup_logging(
        cls,
        log_level: str | None = None,
        log_file: str | None = None,
        format_string: str | None = None,
    ) -> None:
        """
        로깅 설정 초기화

        Args:
            log_level: 로그 레벨 (INFO, DEBUG, WARNING, ERROR, CRITICAL)
                      기본값은 settings.LOG_LEVEL
            log_file: 로그 파일 경로 (None이면 파일 로깅 안 함)
                     기본값은 settings.LOG_FILE
            format_string: 로그 포맷 문자열
                          기본값은 "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        """
        if cls._initialized:
            return  # 이미 초기화되었으면 다시 설정하지 않음

        # 설정 값 결정
        level = log_level or settings.LOG_LEVEL
        log_file_path = log_file or settings.LOG_FILE
        log_format = (
            format_string or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # 로그 레벨 변환
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        date_format = "%Y-%m-%d %H:%M:%S"

        # 핸들러 설정
        handlers: list[logging.Handler] = []
        handlers.append(logging.StreamHandler())  # 콘솔 출력

        # 파일 로깅 설정 (LOG_FILE이 지정된 경우)
        if log_file_path:
            # 디렉토리가 없으면 생성
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_file_path, encoding="utf-8"))

        # 로깅 설정 적용
        logging.basicConfig(
            level=numeric_level,
            format=log_format,
            datefmt=date_format,
            handlers=handlers,
            force=True,  # 기존 설정 재정의
        )

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        로거 인스턴스 반환

        Args:
            name: 로거 이름 (일반적으로 __name__ 사용)

        Returns:
            logging.Logger: 로거 인스턴스
        """
        if not cls._initialized:
            cls.setup_logging()
        return logging.getLogger(name)

    @classmethod
    def reset(cls) -> None:
        """로깅 설정 초기화 상태 리셋 (테스트용)"""
        cls._initialized = False
