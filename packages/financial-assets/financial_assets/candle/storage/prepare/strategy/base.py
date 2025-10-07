from abc import ABC, abstractmethod
from .....stock_address import StockAddress


class BasePrepareStrategy(ABC):
    """저장소 준비 전략의 추상 클래스"""

    @abstractmethod
    def prepare(self, address: StockAddress) -> None:
        """
        저장소 준비

        Args:
            address: StockAddress 객체
        """
        pass
