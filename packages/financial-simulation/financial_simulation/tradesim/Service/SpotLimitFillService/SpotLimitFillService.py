# 지정가 주문 체결 서비스

from __future__ import annotations
import random
from typing import List

from simple_logger import func_logging
from financial_assets.order import SpotOrder
from financial_assets.price import Price
from financial_assets.constants import TimeInForce

from ...InternalStruct import TradeParams
from ...Constants import FillProbability, SplitConfig
from ...Core import CandleAnalyzer, AmountSplitter


class SpotLimitFillService:

    @func_logging(level="INFO")
    def execute(
        self,
        order: SpotOrder,
        price: Price,
    ) -> List[TradeParams]:
        # 지정가 주문 체결 파라미터 생성

        # 1. GTD 만료 체크
        if order.time_in_force == TimeInForce.GTD:
            if self._is_expired(order, price.t):
                return []

        # 2. 영역 판단
        zone = CandleAnalyzer.classify_zone(price, order.price)

        if zone == "body":
            return self._fill_body_zone(order)
        elif zone in ("head", "tail"):
            # FOK는 부분 체결 불가
            if order.time_in_force == TimeInForce.FOK:
                return self._fill_wick_zone_fok(order)
            else:  # GTC, GTD, IOC, None
                return self._fill_wick_zone(order)
        else:
            return []

    def _is_expired(self, order: SpotOrder, current_timestamp: int) -> bool:
        # GTD 주문 만료 여부 확인
        if order.expire_timestamp is None:
            return False
        return current_timestamp > order.expire_timestamp

    def _fill_body_zone(self, order: SpotOrder) -> List[TradeParams]:
        # body 영역: 전량 체결
        return [self._create_full_fill(order)]

    def _fill_wick_zone(self, order: SpotOrder) -> List[TradeParams]:
        # wick 영역: 확률적 체결 (GTC, GTD, IOC)
        rand = random.random()

        if rand < FillProbability.WICK_FAIL:
            return []
        elif rand < FillProbability.WICK_FAIL + FillProbability.WICK_FULL:
            return [self._create_full_fill(order)]
        else:
            return self._create_partial_fills(order)

    def _fill_wick_zone_fok(self, order: SpotOrder) -> List[TradeParams]:
        # wick 영역: FOK 체결 (전량 체결 or 전체 실패만)
        rand = random.random()

        if rand < FillProbability.WICK_FOK_FAIL:
            return []
        else:
            return [self._create_full_fill(order)]

    def _create_full_fill(self, order: SpotOrder) -> TradeParams:
        # 전량 체결 파라미터 생성
        return TradeParams(
            fill_amount=order.remaining_asset(),
            fill_price=order.price,
            fill_index=1,
        )

    def _create_partial_fills(self, order: SpotOrder) -> List[TradeParams]:
        # 부분 체결 파라미터 리스트 생성
        if not order.min_trade_amount or order.min_trade_amount <= 0:
            raise ValueError(
                f"Order must have valid min_trade_amount for partial fills: {order.min_trade_amount}"
            )

        total_amount = order.remaining_asset()
        split_count = random.randint(
            SplitConfig.MIN_SPLIT_COUNT,
            SplitConfig.MAX_SPLIT_COUNT
        )

        amounts = AmountSplitter.split_with_dirichlet(
            total_amount, order.min_trade_amount, split_count
        )

        return [
            TradeParams(
                fill_amount=amount,
                fill_price=order.price,
                fill_index=idx,
            )
            for idx, amount in enumerate(amounts, 1)
        ]
