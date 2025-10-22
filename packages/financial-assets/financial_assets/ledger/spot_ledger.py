"""Spot ledger container.

This module provides the SpotLedger class for managing trade history
for a single spot trading pair.
"""

from __future__ import annotations
from typing import Optional
import pandas as pd
from ..trade import SpotTrade, SpotSide
from .spot_ledger_entry import SpotLedgerEntry
from simple_logger import init_logging, logger


class SpotLedger:
    """단일 거래쌍의 현물 거래 내역 장부.
    거래를 시간순으로 기록하고 누적 자산, 평균 진입가, 실현 손익을 계산합니다.
    """

    @init_logging(level="DEBUG")
    def __init__(self, ticker: str) -> None:
        """SpotLedger 초기화."""
        self.ticker = ticker
        self._entries: list[SpotLedgerEntry] = []
        self._cumulative_asset: float = 0.0
        self._cumulative_value: float = 0.0
        self._average_price: Optional[float] = None

    def add_trade(self, trade: SpotTrade) -> SpotLedgerEntry:
        """거래 추가 및 장부 업데이트."""
        asset_amount = trade.pair.get_asset()
        value_amount = trade.pair.get_value()
        trade_price = trade.pair.mean_value()

        logger.debug(f"SpotLedger.add_trade: ticker={self.ticker}, side={trade.side.value}, asset={asset_amount}, price={trade_price}")

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
                logger.debug(f"평균가 재계산: 기존={self._average_price:.2f}, 신규={new_average_price:.2f}")
            else:
                # 첫 매수
                new_average_price = trade_price
                logger.debug(f"첫 매수: 평균가={new_average_price:.2f}")

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
                logger.debug(f"실현 손익 계산: avg_price={self._average_price:.2f}, sell_price={trade_price:.2f}, pnl={realized_pnl:.2f}")
            else:
                # 평균가가 없는 상태에서 매도 (비정상 상황)
                realized_pnl = 0.0
                logger.warning("평균가 없이 매도 발생 (비정상)")

            self._cumulative_asset += asset_change
            self._cumulative_value += value_change

            # 포지션 완전 청산 시 평균가 리셋
            if abs(self._cumulative_asset) < 1e-8:  # Floating point tolerance
                self._average_price = None
                self._cumulative_asset = 0.0  # 정확히 0으로
                logger.debug("포지션 완전 청산: 평균가 리셋")

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
        """장부를 DataFrame으로 변환."""
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
        """읽기 쉬운 문자열 표현 반환."""
        return f"SpotLedger(ticker={self.ticker}, entries={len(self._entries)})"

    def __repr__(self) -> str:
        """상세한 문자열 표현 반환."""
        return (
            f"SpotLedger(ticker={self.ticker!r}, entries={len(self._entries)}, "
            f"position=({self._cumulative_asset}, {self._cumulative_value}), "
            f"avg_price={self._average_price})"
        )
