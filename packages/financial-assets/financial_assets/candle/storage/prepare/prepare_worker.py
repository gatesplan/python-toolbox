from ....stock_address import StockAddress
from .strategy.base import BasePrepareStrategy
from simple_logger import init_logging, func_logging


class PrepareWorker:
    """저장소 준비 작업 흐름 관장"""

    @init_logging
    def __init__(self, strategy: BasePrepareStrategy):
        """
        Args:
            strategy: BasePrepareStrategy 인스턴스
        """
        self.strategy = strategy

    @func_logging
    def __call__(self, address: StockAddress) -> None:
        """
        저장소 준비 실행

        Args:
            address: StockAddress 객체
        """
        self.strategy.prepare(address)
