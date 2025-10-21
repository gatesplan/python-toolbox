"""Worker interface and implementations for wallet analysis."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING
import pandas as pd
from simple_logger import func_logging

if TYPE_CHECKING:
    from .spot_wallet import SpotWallet
    from ..price import Price


class WalletWorker(ABC):
    """
    Wallet 분석 작업을 수행하는 Worker 추상 클래스.

    Director-Worker 패턴에서 Worker 역할을 담당하며,
    각 구현체는 특정 분석 작업을 수행합니다.

    Examples:
        >>> from financial_assets.wallet import SpotWallet
        >>> from financial_assets.wallet.worker import WalletWorker
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


class TotalValueWorker(WalletWorker):
    """
    총 자산 가치 계산 Worker.

    화폐 잔액과 보유 자산의 현재 가치를 합산하여
    특정 quote 화폐 기준 총 자산 가치를 계산합니다.
    """

    @func_logging(level="DEBUG")
    def analyze(
        self,
        wallet: SpotWallet,
        quote_symbol: str,
        current_prices: dict[str, Price],
    ) -> float:
        """
        총 자산 가치 계산.

        Args:
            wallet: SpotWallet
            quote_symbol: 기준 화폐 (예: "USD")
            current_prices: ticker -> Price 매핑 (Price.c를 현재가로 사용)

        Returns:
            float: 총 자산 가치

        Examples:
            >>> from financial_assets.wallet import SpotWallet
            >>> from financial_assets.price import Price
            >>>
            >>> wallet = SpotWallet()
            >>> wallet.deposit_currency("USD", 10000.0)
            >>>
            >>> worker = TotalValueWorker()
            >>> total = worker.analyze(wallet, "USD", {})
            >>> total
            10000.0
        """
        total = 0.0

        # 화폐 잔액 (quote 화폐만)
        total += wallet.get_currency_balance(quote_symbol)

        # 보유 자산 가치
        for ticker in wallet.list_tickers():
            if ticker not in current_prices:
                continue

            stack = wallet.get_pair_stack(ticker)
            if stack is None:
                continue

            current_price = current_prices[ticker].c  # close 가격 사용
            asset_amount = stack.total_asset_amount()
            total += current_price * asset_amount

        return total


class RealizedPnLWorker(WalletWorker):
    """
    실현 손익 계산 Worker.

    모든 ledger의 realized_pnl을 합산합니다.
    """

    @func_logging(level="DEBUG")
    def analyze(self, wallet: SpotWallet) -> float:
        """
        총 실현 손익 계산.

        Args:
            wallet: SpotWallet

        Returns:
            float: 총 실현 손익

        Examples:
            >>> wallet = SpotWallet()
            >>> worker = RealizedPnLWorker()
            >>> total_pnl = worker.analyze(wallet)
            >>> total_pnl
            0.0
        """
        total_pnl = 0.0

        for ticker in wallet.list_tickers():
            ledger = wallet.get_ledger(ticker)
            if ledger is None:
                continue

            df = ledger.to_dataframe()
            if df.empty:
                continue

            # realized_pnl 합계 (None은 0으로 처리)
            pnl_values = df["realized_pnl"].fillna(0.0)
            total_pnl += pnl_values.sum()

        return total_pnl


class UnrealizedPnLWorker(WalletWorker):
    """
    미실현 손익 계산 Worker.

    보유 자산의 (현재가 - 평균가) × 보유량을 계산합니다.
    """

    @func_logging(level="DEBUG")
    def analyze(
        self,
        wallet: SpotWallet,
        quote_symbol: str,
        current_prices: dict[str, Price],
    ) -> float:
        """
        미실현 손익 계산.

        Args:
            wallet: SpotWallet
            quote_symbol: 기준 화폐
            current_prices: ticker -> Price 매핑

        Returns:
            float: 미실현 손익

        Examples:
            >>> from financial_assets.price import Price
            >>>
            >>> wallet = SpotWallet()
            >>> worker = UnrealizedPnLWorker()
            >>> unrealized = worker.analyze(wallet, "USD", {})
            >>> unrealized
            0.0
        """
        total_unrealized = 0.0

        for ticker in wallet.list_tickers():
            if ticker not in current_prices:
                continue

            stack = wallet.get_pair_stack(ticker)
            if stack is None:
                continue

            current_price = current_prices[ticker].c
            avg_price = stack.mean_value()
            asset_amount = stack.total_asset_amount()

            unrealized_pnl = (current_price - avg_price) * asset_amount
            total_unrealized += unrealized_pnl

        return total_unrealized


class PositionSummaryWorker(WalletWorker):
    """
    포지션 요약 DataFrame 생성 Worker.

    각 ticker별 보유량, 평균가, 투자금, 현재 가치, 미실현 손익을 정리합니다.
    """

    @func_logging(level="DEBUG")
    def analyze(
        self,
        wallet: SpotWallet,
        quote_symbol: str,
        current_prices: dict[str, Price],
    ) -> pd.DataFrame:
        """
        포지션 요약 DataFrame 생성.

        Args:
            wallet: SpotWallet
            quote_symbol: 기준 화폐
            current_prices: ticker -> Price 매핑

        Returns:
            pd.DataFrame: 포지션 요약 (columns: ticker, asset_amount, avg_price,
                          cost_basis, current_value, unrealized_pnl)

        Examples:
            >>> wallet = SpotWallet()
            >>> worker = PositionSummaryWorker()
            >>> df = worker.analyze(wallet, "USD", {})
            >>> df.empty
            True
        """
        data = []

        for ticker in wallet.list_tickers():
            stack = wallet.get_pair_stack(ticker)
            if stack is None:
                continue

            asset_amount = stack.total_asset_amount()
            avg_price = stack.mean_value()
            cost_basis = stack.total_value_amount()

            # 현재 가격이 있으면 현재 가치 및 미실현 손익 계산
            if ticker in current_prices:
                current_price = current_prices[ticker].c
                current_value = current_price * asset_amount
                unrealized_pnl = (current_price - avg_price) * asset_amount
            else:
                current_value = 0.0
                unrealized_pnl = 0.0

            data.append(
                {
                    "ticker": ticker,
                    "asset_amount": asset_amount,
                    "avg_price": avg_price,
                    "cost_basis": cost_basis,
                    "current_value": current_value,
                    "unrealized_pnl": unrealized_pnl,
                }
            )

        if not data:
            return pd.DataFrame(
                columns=[
                    "ticker",
                    "asset_amount",
                    "avg_price",
                    "cost_basis",
                    "current_value",
                    "unrealized_pnl",
                ]
            )

        return pd.DataFrame(data)


class CurrencySummaryWorker(WalletWorker):
    """
    화폐 잔액 요약 DataFrame 생성 Worker.
    """

    @func_logging(level="DEBUG")
    def analyze(self, wallet: SpotWallet) -> pd.DataFrame:
        """
        화폐 잔액 요약 DataFrame 생성.

        Args:
            wallet: SpotWallet

        Returns:
            pd.DataFrame: 화폐 요약 (columns: symbol, amount)

        Examples:
            >>> wallet = SpotWallet()
            >>> wallet.deposit_currency("USD", 1000.0)
            >>> worker = CurrencySummaryWorker()
            >>> df = worker.analyze(wallet)
            >>> len(df)
            1
        """
        data = []

        for symbol in wallet.list_currencies():
            amount = wallet.get_currency_balance(symbol)
            data.append({"symbol": symbol, "amount": amount})

        if not data:
            return pd.DataFrame(columns=["symbol", "amount"])

        return pd.DataFrame(data)
