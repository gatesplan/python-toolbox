from abc import ABC, abstractmethod
import pandas as pd
from .....stock_address import StockAddress


class BaseLoadStrategy(ABC):
    """데이터 로드 전략의 추상 클래스"""

    @abstractmethod
    def load(self, address: StockAddress, start_ts: int = None, end_ts: int = None) -> pd.DataFrame:
        """
        데이터 로드

        Args:
            address: StockAddress 객체
            start_ts: 시작 타임스탬프 (이상)
            end_ts: 종료 타임스탬프 (미만)

        Returns:
            로드된 DataFrame
        """
        pass
