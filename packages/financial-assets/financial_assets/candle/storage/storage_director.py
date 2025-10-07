from .prepare import PrepareWorker
from .save import SaveWorker
from .load import LoadWorker
from .prepare.strategy import ParquetPrepareStrategy, MySQLPrepareStrategy
from .save.strategy import ParquetSaveStrategy, MySQLSaveStrategy
from .load.strategy import ParquetLoadStrategy, MySQLLoadStrategy
from simple_logger import init_logging, func_logging


class StorageDirector:
    """전략 선택 및 Worker 관리"""

    @init_logging
    def __init__(self, env_config: dict):
        """
        Args:
            env_config: 환경변수 설정 dict
        """
        strategy = env_config.get('strategy')

        if strategy == 'parquet':
            prepare_strategy = ParquetPrepareStrategy(env_config)
            save_strategy = ParquetSaveStrategy(env_config)
            load_strategy = ParquetLoadStrategy(env_config)
        elif strategy == 'mysql':
            prepare_strategy = MySQLPrepareStrategy(env_config)
            save_strategy = MySQLSaveStrategy(env_config)
            load_strategy = MySQLLoadStrategy(env_config)
        else:
            raise ValueError(f"Unsupported storage strategy: {strategy}")

        # Worker 생성 및 캐싱
        self.prepare_worker = PrepareWorker(prepare_strategy)
        self.save_worker = SaveWorker(save_strategy)
        self.load_worker = LoadWorker(load_strategy)

    @func_logging
    def get_prepare_worker(self) -> PrepareWorker:
        """PrepareWorker 인스턴스 반환"""
        return self.prepare_worker

    @func_logging
    def get_save_worker(self) -> SaveWorker:
        """SaveWorker 인스턴스 반환"""
        return self.save_worker

    @func_logging
    def get_load_worker(self) -> LoadWorker:
        """LoadWorker 인스턴스 반환"""
        return self.load_worker
