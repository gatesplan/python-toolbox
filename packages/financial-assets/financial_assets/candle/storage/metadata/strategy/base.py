from abc import ABC, abstractmethod
from .....stock_address import StockAddress


class BaseMetadataStrategy(ABC):
    # 메타데이터 관리 전략의 추상 클래스

    @abstractmethod
    def get_last_update_ts(self, address: StockAddress) -> int | None:
        # 마지막 업데이트 타임스탬프 조회
        pass

    @abstractmethod
    def set_last_update_ts(self, address: StockAddress, timestamp: int) -> None:
        # 마지막 업데이트 타임스탬프 저장
        pass
