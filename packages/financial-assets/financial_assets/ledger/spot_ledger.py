"""Spot ledger container.

This module provides the SpotLedger class for managing trade history
for a single spot trading pair.
"""

from __future__ import annotations
from typing import Optional
import pandas as pd
from ..trade import SpotTrade, SpotSide
from .spot_ledger_entry import SpotLedgerEntry


class SpotLedger:
    """
    단일 거래쌍의 현물 거래 내역을 관리하는 장부.

    SpotLedger는 특정 거래쌍(예: BTC-USDT)의 모든 거래를 시간순으로 기록하고,
    각 거래가 포지션에 미치는 영향(누적 자산/가치, 평균 진입가, 실현 손익)을
    자동으로 계산합니다.

    장부는 데이터 테이블 역할에 집중하며, DataFrame 변환을 통해 상위 레이어에서
    자유롭게 분석과 시각화를 수행할 수 있습니다.

    Attributes:
        ticker (str): 거래쌍 티커 (예: "BTC-USDT")

    Examples:
        >>> from financial_assets.ledger import SpotLedger
        >>> from financial_assets.trade import SpotTrade, SpotSide
        >>> from financial_assets.pair import Pair
        >>> from financial_assets.token import Token
        >>> from financial_assets.stock_address import StockAddress
        >>>
        >>> stock_address = StockAddress(
        ...     archetype="crypto",
        ...     exchange="binance",
        ...     tradetype="spot",
        ...     base="btc",
        ...     quote="usdt",
        ...     timeframe="1d"
        ... )
        >>>
        >>> ledger = SpotLedger(ticker="BTC-USDT")
        >>>
        >>> # Add a BUY trade
        >>> buy_trade = SpotTrade(
        ...     stock_address=stock_address,
        ...     trade_id="trade-1",
        ...     fill_id="fill-1",
        ...     side=SpotSide.BUY,
        ...     pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
        ...     timestamp=1234567890
        ... )
        >>> entry = ledger.add_trade(buy_trade)
        >>> entry.cumulative_asset
        1.0
        >>> entry.average_price
        50000.0
        >>>
        >>> # Convert to DataFrame for analysis
        >>> df = ledger.to_dataframe()
        >>> len(df)
        1
    """

    def __init__(self, ticker: str) -> None:
        """
        SpotLedger 초기화.

        Args:
            ticker: 거래쌍 티커 (예: "BTC-USDT", "ETH-BTC")
        """
        self.ticker = ticker
        self._entries: list[SpotLedgerEntry] = []
        self._cumulative_asset: float = 0.0
        self._cumulative_value: float = 0.0
        self._average_price: Optional[float] = None

    def add_trade(self, trade: SpotTrade) -> SpotLedgerEntry:
        """
        거래를 장부에 기록하고 SpotLedgerEntry를 반환합니다.

        BUY 거래 시 평균 진입가를 가중 평균으로 재계산하고,
        SELL 거래 시 실현 손익을 계산합니다.

        Args:
            trade: 기록할 SpotTrade 객체

        Returns:
            SpotLedgerEntry: 생성된 장부 엔트리

        Examples:
            >>> ledger = SpotLedger(ticker="BTC-USDT")
            >>>
            >>> # BUY: 평균가 계산
            >>> buy1 = SpotTrade(
            ...     stock_address=stock_address,
            ...     trade_id="t1",
            ...     fill_id="f1",
            ...     side=SpotSide.BUY,
            ...     pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
            ...     timestamp=1234567890
            ... )
            >>> entry1 = ledger.add_trade(buy1)
            >>> entry1.average_price
            50000.0
            >>>
            >>> # SELL: 실현 손익 계산
            >>> sell = SpotTrade(
            ...     stock_address=stock_address,
            ...     trade_id="t2",
            ...     fill_id="f2",
            ...     side=SpotSide.SELL,
            ...     pair=Pair(Token("BTC", 0.5), Token("USDT", 27500.0)),
            ...     timestamp=1234567900
            ... )
            >>> entry2 = ledger.add_trade(sell)
            >>> entry2.realized_pnl
            2500.0
        """
        asset_amount = trade.pair.get_asset()
        value_amount = trade.pair.get_value()
        trade_price = trade.pair.mean_value()

        if trade.side == SpotSide.BUY:
            # BUY: 자산 증가, 가치 감소 (투자금 증가)
            asset_change = asset_amount
            value_change = -value_amount

            # 평균 진입가 재계산 (가중 평균)
            if self._cumulative_asset > 0:
                total_value = (
                    self._average_price * self._cumulative_asset + value_amount
                )
                new_asset = self._cumulative_asset + asset_amount
                new_average_price = total_value / new_asset
            else:
                # 첫 매수
                new_average_price = trade_price

            self._cumulative_asset += asset_change
            self._cumulative_value += value_change
            self._average_price = new_average_price

            realized_pnl = None

        else:  # SpotSide.SELL
            # SELL: 자산 감소, 가치 증가
            asset_change = -asset_amount
            value_change = value_amount

            # 실현 손익 계산
            if self._average_price is not None:
                realized_pnl = (trade_price - self._average_price) * asset_amount
            else:
                # 평균가가 없는 상태에서 매도 (비정상 상황)
                realized_pnl = 0.0

            self._cumulative_asset += asset_change
            self._cumulative_value += value_change

            # 포지션 완전 청산 시 평균가 리셋
            if abs(self._cumulative_asset) < 1e-8:  # Floating point tolerance
                self._average_price = None
                self._cumulative_asset = 0.0  # 정확히 0으로

        # Entry 생성
        entry = SpotLedgerEntry(
            timestamp=trade.timestamp,
            trade=trade,
            asset_change=asset_change,
            value_change=value_change,
            cumulative_asset=self._cumulative_asset,
            cumulative_value=self._cumulative_value,
            average_price=self._average_price if self._average_price is not None else 0.0,
            realized_pnl=realized_pnl,
        )

        self._entries.append(entry)
        return entry

    def to_dataframe(self) -> pd.DataFrame:
        """
        모든 거래 내역을 pandas DataFrame으로 반환합니다.

        DataFrame 컬럼:
        - timestamp: 거래 시각
        - side: 거래 방향 (BUY/SELL)
        - asset_change: 자산 변화량
        - value_change: 가치 변화량
        - cumulative_asset: 누적 자산
        - cumulative_value: 누적 가치
        - average_price: 평균 진입가
        - realized_pnl: 실현 손익

        Returns:
            pd.DataFrame: 거래 내역 DataFrame

        Examples:
            >>> ledger = SpotLedger(ticker="BTC-USDT")
            >>> # ... add trades ...
            >>> df = ledger.to_dataframe()
            >>> df.columns
            Index(['timestamp', 'side', 'asset_change', 'value_change',
                   'cumulative_asset', 'cumulative_value', 'average_price',
                   'realized_pnl'], dtype='object')
        """
        if not self._entries:
            # 빈 DataFrame 반환
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "side",
                    "asset_change",
                    "value_change",
                    "cumulative_asset",
                    "cumulative_value",
                    "average_price",
                    "realized_pnl",
                ]
            )

        data = []
        for entry in self._entries:
            data.append(
                {
                    "timestamp": entry.timestamp,
                    "side": entry.trade.side.value,
                    "asset_change": entry.asset_change,
                    "value_change": entry.value_change,
                    "cumulative_asset": entry.cumulative_asset,
                    "cumulative_value": entry.cumulative_value,
                    "average_price": entry.average_price,
                    "realized_pnl": entry.realized_pnl,
                }
            )

        return pd.DataFrame(data)

    def __str__(self) -> str:
        """
        SpotLedger의 읽기 쉬운 문자열 표현을 반환합니다.

        Returns:
            str: 티커와 엔트리 수 정보를 포함한 문자열
        """
        return f"SpotLedger(ticker={self.ticker}, entries={len(self._entries)})"

    def __repr__(self) -> str:
        """
        SpotLedger의 상세한 문자열 표현을 반환합니다.

        Returns:
            str: 티커, 엔트리 수, 현재 포지션 정보를 포함한 문자열
        """
        return (
            f"SpotLedger(ticker={self.ticker!r}, entries={len(self._entries)}, "
            f"position=({self._cumulative_asset}, {self._cumulative_value}), "
            f"avg_price={self._average_price})"
        )
