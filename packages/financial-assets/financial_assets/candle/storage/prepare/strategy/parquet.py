from pathlib import Path
from .....stock_address import StockAddress
from .base import BasePrepareStrategy
from simple_logger import init_logging, func_logging


class ParquetPrepareStrategy(BasePrepareStrategy):
    """Parquet 저장소 준비 전략"""

    @init_logging
    def __init__(self, config: dict):
        """
        Args:
            config: 환경변수 설정 dict (basepath 포함)
        """
        self.basepath = Path(config['basepath'])

    @func_logging
    def prepare(self, address: StockAddress) -> None:
        """
        디렉토리 생성

        Args:
            address: StockAddress 객체
        """
        # basepath가 없으면 생성
        self.basepath.mkdir(parents=True, exist_ok=True)
