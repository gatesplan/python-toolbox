# 시장가 매수 체결 서비스

from __future__ import annotations
import random
from typing import List

from simple_logger import func_logging, logger
from financial_assets.order import SpotOrder
from financial_assets.price import Price
from financial_assets.constants import OrderSide, TimeInForce

from ...InternalStruct import TradeParams
from ...Constants import SplitConfig
from ...Core import PriceSampler, AmountSplitter, SlippageCalculator


class SpotMarketBuyFillService:

    @func_logging(level="INFO")
    def execute(
        self,
        order: SpotOrder,
        price: Price,
    ) -> List[TradeParams]:
        # 시장가 매수 체결 파라미터 생성
        if not order.min_trade_amount or order.min_trade_amount <= 0:
            raise ValueError(
                f"Order must have valid min_trade_amount: {order.min_trade_amount}"
            )

        # 유동성 비율 계산 (매도 측 유동성 근사)
        available_liquidity = price.v / 2
        order_ratio = order.remaining_asset() / available_liquidity

        # 체결 비율 결정
        fill_ratio = self._calculate_fill_ratio(order, order_ratio)

        if fill_ratio == 0:
            return []

        # 실제 체결 수량
        total_amount = order.remaining_asset() * fill_ratio

        return self._create_fills(order, price, total_amount)

    def _calculate_fill_ratio(self, order: SpotOrder, order_ratio: float) -> float:
        # 유동성 비율에 따른 체결 비율 계산

        # 거래량의 20% 초과 (order_ratio > 0.4)
        if order_ratio > 0.4:
            logger.warning(
                f"주문량이 가용 유동성의 20%를 초과합니다. "
                f"order_id={order.order_id}, order_ratio={order_ratio:.2%}"
            )

            if order.time_in_force == TimeInForce.FOK:
                # FOK: 무조건 실패
                logger.warning(f"FOK 주문 실패: order_id={order.order_id}")
                return 0
            else:
                # IOC: 5-15% 극소량 체결
                return random.uniform(0.05, 0.15)

        # 0.1% 이하: 전량 체결
        elif order_ratio <= 0.001:
            return 1.0

        # 0.1% ~ 1%: 거의 전량 체결
        elif order_ratio <= 0.01:
            if order.time_in_force == TimeInForce.FOK:
                # FOK: 10% 확률로 실패
                if random.random() < 0.1:
                    logger.info(f"FOK 주문 실패 (확률): order_id={order.order_id}")
                    return 0
            return random.uniform(0.95, 1.0)

        # 1% ~ 5%: 부분 체결
        elif order_ratio <= 0.05:
            if order.time_in_force == TimeInForce.FOK:
                # FOK: 50% 확률로 실패
                if random.random() < 0.5:
                    logger.info(f"FOK 주문 실패 (확률): order_id={order.order_id}")
                    return 0
            return random.uniform(0.6, 0.9)

        # 5% ~ 20%: 낮은 체결률
        else:
            if order.time_in_force == TimeInForce.FOK:
                # FOK: 90% 확률로 실패
                if random.random() < 0.9:
                    logger.info(f"FOK 주문 실패 (확률): order_id={order.order_id}")
                    return 0
            return random.uniform(0.2, 0.5)

    def _create_fills(
        self,
        order: SpotOrder,
        price: Price,
        total_amount: float,
    ) -> List[TradeParams]:
        # 체결 파라미터 생성
        slippage_min, slippage_max = SlippageCalculator.calculate_range(
            price, OrderSide.BUY
        )

        mean, std = PriceSampler.calculate_normal_params(
            slippage_min, slippage_max, SplitConfig.STD_CALCULATION_FACTOR
        )

        split_count = random.randint(
            SplitConfig.MIN_SPLIT_COUNT,
            SplitConfig.MAX_SPLIT_COUNT
        )

        amounts = AmountSplitter.split_with_dirichlet(
            total_amount, order.min_trade_amount, split_count
        )

        params_list = []
        for idx, amount in enumerate(amounts, 1):
            sampled_price = PriceSampler.sample_from_normal(
                slippage_min, slippage_max, mean, std
            )
            params_list.append(
                TradeParams(
                    fill_amount=amount,
                    fill_price=sampled_price,
                    fill_index=idx,
                )
            )

        return params_list
