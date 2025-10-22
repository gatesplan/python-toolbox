"""WalletInspector for wallet statistics and analysis."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd
from simple_logger import init_logging

from .workers import (
    TotalValueWorker,
    RealizedPnLWorker,
    UnrealizedPnLWorker,
    PositionSummaryWorker,
    CurrencySummaryWorker,
)

if TYPE_CHECKING:
    from .spot_wallet import SpotWallet
    from ..price import Price


class WalletInspector:
    """지갑 상태 분석 도구.
    총 자산 가치, 실현/미실현 손익, 포지션 요약을 제공합니다.
    """

    @init_logging(level="DEBUG")
    def __init__(self, wallet: SpotWallet) -> None:
        """WalletInspector 초기화."""
        self.wallet = wallet
        self._total_value_worker = TotalValueWorker()
        self._realized_pnl_worker = RealizedPnLWorker()
        self._unrealized_pnl_worker = UnrealizedPnLWorker()
        self._position_summary_worker = PositionSummaryWorker()
        self._currency_summary_worker = CurrencySummaryWorker()

    def get_total_value(
        self, quote_symbol: str, current_prices: dict[str, Price]
    ) -> float:
        """총 자산 가치 계산."""
        return self._total_value_worker.analyze(
            self.wallet, quote_symbol=quote_symbol, current_prices=current_prices
        )

    def get_total_realized_pnl(self) -> float:
        """실현 손익 계산."""
        return self._realized_pnl_worker.analyze(self.wallet)

    def get_unrealized_pnl(
        self, quote_symbol: str, current_prices: dict[str, Price]
    ) -> float:
        """미실현 손익 계산."""
        return self._unrealized_pnl_worker.analyze(
            self.wallet, quote_symbol=quote_symbol, current_prices=current_prices
        )

    def get_position_summary(
        self, quote_symbol: str, current_prices: dict[str, Price]
    ) -> pd.DataFrame:
        """포지션 요약."""
        return self._position_summary_worker.analyze(
            self.wallet, quote_symbol=quote_symbol, current_prices=current_prices
        )

    def get_currency_summary(self) -> pd.DataFrame:
        """화폐 계정 요약."""
        return self._currency_summary_worker.analyze(self.wallet)

    def __str__(self) -> str:
        """읽기 쉬운 문자열 표현 반환."""
        currency_count = len(self.wallet.list_currencies())
        ticker_count = len(self.wallet.list_tickers())
        return f"WalletInspector(currencies={currency_count}, tickers={ticker_count})"

    def __repr__(self) -> str:
        """상세한 문자열 표현 반환."""
        return f"WalletInspector(wallet={self.wallet!r})"
