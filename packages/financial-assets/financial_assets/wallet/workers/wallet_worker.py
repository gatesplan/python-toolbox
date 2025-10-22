"""Worker interface for wallet analysis."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..spot_wallet import SpotWallet


class WalletWorker(ABC):
    """
    Wallet 분석 작업을 수행하는 Worker 추상 클래스.

    Director-Worker 패턴에서 Worker 역할을 담당하며,
    각 구현체는 특정 분석 작업을 수행합니다.

    Examples:
        >>> from financial_assets.wallet import SpotWallet
        >>> from financial_assets.wallet.workers import WalletWorker
        >>>
        >>> class CustomWorker(WalletWorker):
        ...     def analyze(self, wallet: SpotWallet) -> dict:
        ...         return {"currency_count": len(wallet.list_currencies())}
        >>>
        >>> wallet = SpotWallet()
        >>> worker = CustomWorker()
        >>> result = worker.analyze(wallet)
    """

    @abstractmethod
    def analyze(self, wallet: SpotWallet, **kwargs) -> Any:
        """
        Wallet 분석 수행.

        Args:
            wallet: 분석할 SpotWallet
            **kwargs: 추가 파라미터

        Returns:
            Any: 분석 결과
        """
        pass
