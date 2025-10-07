import os
from pathlib import Path
from dotenv import load_dotenv, set_key, find_dotenv
from simple_logger import func_logging


class EnvManageWorker:
    """환경변수 관리 전담. Candle 초기화 과정에서 필요한 환경변수 준비, 로드하여 반환한다."""

    @func_logging
    def __call__(self) -> dict:
        """
        환경변수를 준비, 로드하여 dict로 반환

        Returns:
            환경변수 설정 dict
        """
        # .env 파일 로드
        env_path = find_dotenv()
        if not env_path:
            # .env 파일이 없으면 현재 디렉토리에 생성
            env_path = Path.cwd() / '.env'
            env_path.touch()

        load_dotenv(env_path)

        # 저장소 전략 확인 및 설정
        strategy = os.getenv('FA_CANDLE_STORAGE_STRTG')
        if not strategy:
            strategy = 'parquet'
            set_key(env_path, 'FA_CANDLE_STORAGE_STRTG', strategy)

        config = {'strategy': strategy}

        # 전략별 환경변수 로드
        if strategy == 'parquet':
            config.update(self._load_parquet_config(env_path))
        elif strategy == 'mysql':
            config.update(self._load_mysql_config(env_path))
        else:
            raise ValueError(f"Unsupported storage strategy: {strategy}")

        return config

    @func_logging
    def _load_parquet_config(self, env_path: str) -> dict:
        """Parquet 전략 환경변수 로드"""
        basepath = os.getenv('FA_CANDLE_STORAGE_PARQUET_BASEPATH')
        if not basepath:
            basepath = './data/fa_candles/'
            set_key(env_path, 'FA_CANDLE_STORAGE_PARQUET_BASEPATH', basepath)

        return {'basepath': basepath}

    @func_logging
    def _load_mysql_config(self, env_path: str) -> dict:
        """MySQL 전략 환경변수 로드"""
        config = {}

        # 기본값 있는 환경변수
        defaults = {
            'FA_CANDLE_STORAGE_MYSQL_HOST': 'localhost',
            'FA_CANDLE_STORAGE_MYSQL_PORT': '3306',
            'FA_CANDLE_STORAGE_MYSQL_DBNAME': 'fa$candles',
            'FA_CANDLE_STORAGE_MYSQL_USERNAME': 'root',
            'FA_CANDLE_STORAGE_MYSQL_PASSWORD': ''
        }

        for key, default_value in defaults.items():
            value = os.getenv(key)
            if not value:
                value = default_value
                set_key(env_path, key, value)

            # dict 키는 소문자로 (host, port, dbname, username, password)
            config_key = key.replace('FA_CANDLE_STORAGE_MYSQL_', '').lower()
            config[config_key] = value

        # PORT는 int로 변환
        config['port'] = int(config['port'])

        return config
