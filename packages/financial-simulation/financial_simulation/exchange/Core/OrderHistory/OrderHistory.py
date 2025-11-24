# 주문 이력 관리

from typing import Optional
from dataclasses import dataclass
from financial_assets.order import SpotOrder
from financial_assets.constants import OrderStatus
from simple_logger import init_logging, func_logging, logger


@dataclass(frozen=True)
class OrderRecord:
    # 주문 이력 레코드 (Particles)
    order: SpotOrder
    status: OrderStatus
    timestamp: int  # 상태 변경 시각


class OrderHistory:
    # 모든 주문의 생성/체결/취소 상태 이력 추적

    @init_logging(level="INFO")
    def __init__(self) -> None:
        self._records: dict[str, OrderRecord] = {}
        logger.info("OrderHistory 초기화 완료")

    @func_logging(level="INFO")
    def add_record(
        self,
        order: SpotOrder,
        status: OrderStatus,
        timestamp: int
    ) -> None:
        # 주문 이력 추가
        record = OrderRecord(order=order, status=status, timestamp=timestamp)
        self._records[order.order_id] = record
        logger.info(f"이력 추가: order_id={order.order_id}, status={status.value}")

    def get_record(self, order_id: str) -> Optional[OrderRecord]:
        # 특정 주문 이력 조회
        return self._records.get(order_id)

    def get_all_records(self) -> list[OrderRecord]:
        # 모든 주문 이력 조회
        return list(self._records.values())

    def get_records_by_status(self, status: OrderStatus) -> list[OrderRecord]:
        # 상태별 주문 이력 조회
        return [r for r in self._records.values() if r.status == status]
