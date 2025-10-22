"""미실현 손익 계산 Worker."""

from __future__ import annotations
from typing import TYPE_CHECKING
from simple_logger import func_logging

from .wallet_worker import WalletWorker

if TYPE_CHECKING:
    from ..spot_wallet import SpotWallet
    from ...price import Price


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
