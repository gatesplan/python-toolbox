import pandas as pd
from ....stock_address import StockAddress
from .strategy.base import BaseLoadStrategy
from simple_logger import init_logging, func_logging


class LoadWorker:
    """데이터 로드 작업 흐름 관장"""

    @init_logging
    def __init__(self, strategy: BaseLoadStrategy):
        """
        Args:
            strategy: BaseLoadStrategy 인스턴스
        """
        self.strategy = strategy

    @func_logging
    def __call__(self, address: StockAddress, start_ts: int = None, end_ts: int = None) -> pd.DataFrame:
        """
        데이터 로드 및 반환

        Args:
            address: StockAddress 객체
            start_ts: 시작 타임스탬프 (이상)
            end_ts: 종료 타임스탬프 (미만)

        Returns:
            로드된 DataFrame
        """
        return self.strategy.load(address, start_ts, end_ts)
