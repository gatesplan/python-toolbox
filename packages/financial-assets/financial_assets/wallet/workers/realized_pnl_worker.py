"""실현 손익 계산 Worker."""

from __future__ import annotations
from typing import TYPE_CHECKING
from simple_logger import func_logging

from .wallet_worker import WalletWorker

if TYPE_CHECKING:
    from ..spot_wallet import SpotWallet


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
