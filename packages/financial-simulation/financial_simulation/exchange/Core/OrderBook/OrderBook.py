# 미체결 주문 관리

from typing import Optional
from financial_assets.order import SpotOrder
from financial_assets.symbol import Symbol
from simple_logger import init_logging, func_logging, logger


class OrderBook:
    # 미체결 주문 관리 (주문 저장, 조회, 취소 및 TimeInForce 기반 자동 만료 처리)

    @init_logging(level="INFO")
    def __init__(self) -> None:
        # OrderBook 초기화
        self._orders: dict[str, SpotOrder] = {}
        self._symbol_index: dict[str, set[str]] = {}
        logger.info("OrderBook 초기화 완료")

    @func_logging(level="INFO")
    def add_order(self, order: SpotOrder) -> None:
        # 미체결 주문 추가 (raise ValueError)
        symbol = self._get_symbol(order)
        logger.info(f"주문 추가 시도: order_id={order.order_id}, symbol={symbol}, side={order.side.value}")

        if order.order_id in self._orders:
            logger.error(f"중복된 order_id: {order.order_id}")
            raise ValueError(f"Order {order.order_id} already exists")

        self._orders[order.order_id] = order

        # symbol_index 업데이트
        if symbol not in self._symbol_index:
            self._symbol_index[symbol] = set()
        self._symbol_index[symbol].add(order.order_id)

        logger.info(f"주문 추가 완료: order_id={order.order_id}, total_orders={len(self._orders)}")

    @func_logging(level="INFO")
    def remove_order(self, order_id: str) -> None:
        # 주문 제거 취소 (raise KeyError)
        logger.info(f"주문 제거 시도: order_id={order_id}")

        if order_id not in self._orders:
            logger.error(f"존재하지 않는 order_id: {order_id}")
            raise KeyError(f"Order {order_id} not found")

        order = self._orders[order_id]
        symbol = self._get_symbol(order)

        # symbol_index에서 제거
        if symbol in self._symbol_index:
            self._symbol_index[symbol].discard(order_id)
            if not self._symbol_index[symbol]:
                del self._symbol_index[symbol]

        # 주문 제거
        del self._orders[order_id]

        logger.info(f"주문 제거 완료: order_id={order_id}, remaining_orders={len(self._orders)}")

    def get_order(self, order_id: str) -> Optional[SpotOrder]:
        # 특정 주문 조회
        return self._orders.get(order_id)

    def get_orders_by_symbol(self, symbol: str | Symbol) -> list[SpotOrder]:
        # 특정 심볼의 모든 미체결 주문 조회
        symbol_str = str(symbol)
        order_ids = self._symbol_index.get(symbol_str, set())
        return [self._orders[oid] for oid in order_ids]

    def get_all_orders(self) -> list[SpotOrder]:
        # 모든 미체결 주문 조회
        return list(self._orders.values())

    def get_order_count(self) -> int:
        # 미체결 주문 총 개수
        return len(self._orders)

    @func_logging(level="DEBUG")
    def expire_orders(self, current_timestamp: int) -> list[str]:
        # TimeInForce 기반 만료 주문 제거
        logger.debug(f"주문 만료 체크 시작: current_timestamp={current_timestamp}")
        expired_ids = []

        for order_id, order in list(self._orders.items()):
            # GTD (Good Till Date) 만료 체크
            if order.expire_timestamp is not None:
                if current_timestamp > order.expire_timestamp:
                    expired_ids.append(order_id)
                    self.remove_order(order_id)

        if expired_ids:
            logger.info(f"만료 주문 처리 완료: expired_count={len(expired_ids)}, expired_ids={expired_ids}")
        else:
            logger.debug("만료된 주문 없음")

        return expired_ids

    def _get_symbol(self, order: SpotOrder) -> str:
        # 주문에서 심볼 추출 ("BASE/QUOTE" 형식)
        return order.stock_address.to_symbol().to_slash()

    def __repr__(self) -> str:
        return f"OrderBook(orders={len(self._orders)}, symbols={len(self._symbol_index)})"
