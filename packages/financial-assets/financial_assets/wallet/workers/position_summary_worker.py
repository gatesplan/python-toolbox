"""포지션 요약 DataFrame 생성 Worker."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd
from simple_logger import func_logging

from .wallet_worker import WalletWorker

if TYPE_CHECKING:
    from ..spot_wallet import SpotWallet
    from ...price import Price


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
