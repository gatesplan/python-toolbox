"""WalletInspector for wallet statistics and analysis."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd

from .worker import (
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
    """
    SpotWallet 통계 및 분석 기능을 제공하는 Director 클래스.

    Director-Worker 패턴을 사용하여 각 분석 작업을 Worker에 위임합니다.
    - TotalValueWorker: 총 자산 가치
    - RealizedPnLWorker: 실현 손익
    - UnrealizedPnLWorker: 미실현 손익
    - PositionSummaryWorker: 포지션 요약
    - CurrencySummaryWorker: 화폐 잔액 요약

    Attributes:
        wallet (SpotWallet): 분석 대상 지갑

    Examples:
        >>> from financial_assets.wallet import SpotWallet, WalletInspector
        >>> from financial_assets.price import Price
        >>>
        >>> wallet = SpotWallet()
        >>> wallet.deposit_currency("USD", 100000.0)
        >>>
        >>> inspector = WalletInspector(wallet)
        >>> total = inspector.get_total_value("USD", {})
        >>> total
        100000.0
    """

    def __init__(self, wallet: SpotWallet) -> None:
        """
        WalletInspector 초기화.

        Args:
            wallet: 분석할 SpotWallet

        Examples:
            >>> wallet = SpotWallet()
            >>> inspector = WalletInspector(wallet)
            >>> inspector.wallet is wallet
            True
        """
        self.wallet = wallet
        self._total_value_worker = TotalValueWorker()
        self._realized_pnl_worker = RealizedPnLWorker()
        self._unrealized_pnl_worker = UnrealizedPnLWorker()
        self._position_summary_worker = PositionSummaryWorker()
        self._currency_summary_worker = CurrencySummaryWorker()

    def get_total_value(
        self, quote_symbol: str, current_prices: dict[str, Price]
    ) -> float:
        """
        총 자산 가치 조회.

        화폐 잔액 + 보유 자산의 현재 가치를 합산합니다.

        Args:
            quote_symbol: 기준 화폐 (예: "USD")
            current_prices: ticker -> Price 매핑 (Price.c를 현재가로 사용)

        Returns:
            float: 총 자산 가치

        Examples:
            >>> from financial_assets.price import Price
            >>>
            >>> wallet = SpotWallet()
            >>> wallet.deposit_currency("USD", 50000.0)
            >>> inspector = WalletInspector(wallet)
            >>>
            >>> total = inspector.get_total_value("USD", {})
            >>> total
            50000.0
        """
        return self._total_value_worker.analyze(
            self.wallet, quote_symbol=quote_symbol, current_prices=current_prices
        )

    def get_total_realized_pnl(self) -> float:
        """
        총 실현 손익 조회.

        모든 ledger의 realized_pnl을 합산합니다.

        Returns:
            float: 총 실현 손익

        Examples:
            >>> wallet = SpotWallet()
            >>> inspector = WalletInspector(wallet)
            >>> total_pnl = inspector.get_total_realized_pnl()
            >>> total_pnl
            0.0
        """
        return self._realized_pnl_worker.analyze(self.wallet)

    def get_unrealized_pnl(
        self, quote_symbol: str, current_prices: dict[str, Price]
    ) -> float:
        """
        미실현 손익 조회.

        보유 자산의 (현재가 - 평균가) × 보유량을 계산합니다.

        Args:
            quote_symbol: 기준 화폐
            current_prices: ticker -> Price 매핑

        Returns:
            float: 미실현 손익

        Examples:
            >>> from financial_assets.price import Price
            >>>
            >>> wallet = SpotWallet()
            >>> inspector = WalletInspector(wallet)
            >>> unrealized = inspector.get_unrealized_pnl("USD", {})
            >>> unrealized
            0.0
        """
        return self._unrealized_pnl_worker.analyze(
            self.wallet, quote_symbol=quote_symbol, current_prices=current_prices
        )

    def get_position_summary(
        self, quote_symbol: str, current_prices: dict[str, Price]
    ) -> pd.DataFrame:
        """
        포지션 요약 DataFrame 조회.

        각 ticker별 보유량, 평균가, 투자금, 현재 가치, 미실현 손익을 정리합니다.

        Args:
            quote_symbol: 기준 화폐
            current_prices: ticker -> Price 매핑

        Returns:
            pd.DataFrame: 포지션 요약 (columns: ticker, asset_amount, avg_price,
                          cost_basis, current_value, unrealized_pnl)

        Examples:
            >>> wallet = SpotWallet()
            >>> inspector = WalletInspector(wallet)
            >>> df = inspector.get_position_summary("USD", {})
            >>> df.empty
            True
        """
        return self._position_summary_worker.analyze(
            self.wallet, quote_symbol=quote_symbol, current_prices=current_prices
        )

    def get_currency_summary(self) -> pd.DataFrame:
        """
        화폐 잔액 요약 DataFrame 조회.

        Args:
            None

        Returns:
            pd.DataFrame: 화폐 요약 (columns: symbol, amount)

        Examples:
            >>> wallet = SpotWallet()
            >>> wallet.deposit_currency("USD", 1000.0)
            >>> inspector = WalletInspector(wallet)
            >>> df = inspector.get_currency_summary()
            >>> len(df)
            1
            >>> df.iloc[0]["symbol"]
            'USD'
        """
        return self._currency_summary_worker.analyze(self.wallet)

    def __str__(self) -> str:
        """
        WalletInspector의 읽기 쉬운 문자열 표현.

        Returns:
            str: Inspector 정보
        """
        currency_count = len(self.wallet.list_currencies())
        ticker_count = len(self.wallet.list_tickers())
        return f"WalletInspector(currencies={currency_count}, tickers={ticker_count})"

    def __repr__(self) -> str:
        """
        WalletInspector의 상세한 문자열 표현.

        Returns:
            str: 상세 정보
        """
        return f"WalletInspector(wallet={self.wallet!r})"
