from __future__ import annotations
from .order_info import OrderInfo
from ..pair import PairStack


class Order:
    """
    실제 자산을 보유한 주문 객체.

    OrderInfo(메타데이터)와 PairStack(실제 자산)을 결합하여
    거래소의 limit 주문 동작을 시뮬레이션합니다.

    Note:
        market 주문은 즉시 체결되므로 Order 객체가 필요 없습니다.
        Order는 거래소에서 대기 중인 limit 주문을 위한 것입니다.

    Attributes:
        info (OrderInfo): 주문 메타데이터
        assets (PairStack): 주문과 연결된 실제 자산
    """

    def __init__(self, info: OrderInfo, assets: PairStack):
        """
        Order 초기화.

        Args:
            info: 주문 메타데이터
            assets: 주문과 연결된 실제 자산 (PairStack)
        """
        self.info = info
        self.assets = assets

    # OrderInfo 속성 위임 (delegation pattern)
    @property
    def order_id(self) -> str:
        """주문 ID"""
        return self.info.order_id

    @property
    def price(self) -> float | None:
        """주문 가격"""
        return self.info.price

    @property
    def quantity(self) -> float:
        """주문 수량"""
        return self.info.quantity

    @property
    def filled_quantity(self) -> float:
        """체결된 수량"""
        return self.info.filled_quantity

    @property
    def status(self):
        """주문 상태"""
        return self.info.status

    def fill_by_value_amount(self, amount: float) -> PairStack:
        """
        value 수량 기준으로 체결 처리.

        내부 PairStack에서 해당 value 수량만큼 분리하여 반환합니다.
        원본 Order의 assets는 수정됩니다 (FIFO).

        Args:
            amount: 체결할 value 수량

        Returns:
            PairStack: 체결된 자산 (분리된 PairStack)

        Raises:
            ValueError: amount가 음수이거나 총 value 수량을 초과할 때
            RuntimeError: 총 value 수량이 0일 때
        """
        return self.assets.split_by_value_amount(amount)

    def fill_by_asset_amount(self, amount: float) -> PairStack:
        """
        asset 수량 기준으로 체결 처리.

        내부 PairStack에서 해당 asset 수량만큼 분리하여 반환합니다.
        원본 Order의 assets는 수정됩니다 (FIFO).

        Args:
            amount: 체결할 asset 수량

        Returns:
            PairStack: 체결된 자산 (분리된 PairStack)

        Raises:
            ValueError: amount가 음수이거나 총 asset 수량을 초과할 때
            RuntimeError: 총 asset 수량이 0일 때
        """
        return self.assets.split_by_asset_amount(amount)

    def __eq__(self, other: object) -> bool:
        """
        Order 동등성 비교.

        PairStack의 동등성 비교를 위임합니다.
        (asset_symbol과 value_symbol이 같으면 같은 종류로 판단)

        Args:
            other: 비교 대상 객체

        Returns:
            bool: 같은 종류의 Order이면 True
        """
        if not isinstance(other, Order):
            return False

        return self.assets == other.assets

    def __repr__(self) -> str:
        """Order의 문자열 표현 반환."""
        return f"Order(info={self.info!r}, assets={self.assets!r})"

    def __str__(self) -> str:
        """Order의 읽기 쉬운 문자열 표현 반환."""
        return (
            f"Order(id={self.order_id}, "
            f"price={self.price}, "
            f"quantity={self.quantity}, "
            f"filled={self.filled_quantity}, "
            f"status={self.status.value})"
        )
