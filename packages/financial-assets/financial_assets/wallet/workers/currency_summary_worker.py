"""화폐 잔액 요약 DataFrame 생성 Worker."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd
from simple_logger import func_logging

from .wallet_worker import WalletWorker

if TYPE_CHECKING:
    from ..spot_wallet import SpotWallet


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
