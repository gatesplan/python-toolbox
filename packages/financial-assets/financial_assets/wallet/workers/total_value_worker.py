"""총 자산 가치 계산 Worker."""

from __future__ import annotations
from typing import TYPE_CHECKING
from simple_logger import func_logging

from .wallet_worker import WalletWorker

if TYPE_CHECKING:
    from ..spot_wallet import SpotWallet
    from ...price import Price


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
