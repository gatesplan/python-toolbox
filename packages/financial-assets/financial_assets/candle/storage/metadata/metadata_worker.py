from ....stock_address import StockAddress
from .strategy.base import BaseMetadataStrategy
from simple_logger import init_logging, func_logging


class MetadataWorker:
    # 메타데이터 관리 작업 흐름 관장

    @init_logging
    def __init__(self, strategy: BaseMetadataStrategy):
        self.strategy = strategy

    @func_logging
    def get_last_update_ts(self, address: StockAddress) -> int | None:
        # 마지막 업데이트 타임스탬프 조회
        return self.strategy.get_last_update_ts(address)

    @func_logging
    def set_last_update_ts(self, address: StockAddress, timestamp: int) -> None:
        # 마지막 업데이트 타임스탬프 저장
        self.strategy.set_last_update_ts(address, timestamp)
