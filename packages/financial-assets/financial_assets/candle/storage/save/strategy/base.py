from abc import ABC, abstractmethod
import pandas as pd
from .....stock_address import StockAddress


class BaseSaveStrategy(ABC):
    """데이터 저장 전략의 추상 클래스"""

    @abstractmethod
    def save(self, address: StockAddress, df: pd.DataFrame, storage_last_ts: int = None) -> None:
        """
        데이터 저장

        Args:
            address: StockAddress 객체
            df: 저장할 DataFrame
            storage_last_ts: 저장소에 기록된 마지막 타임스탬프
        """
        pass
