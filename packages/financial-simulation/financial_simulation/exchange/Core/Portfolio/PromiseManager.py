"""자산 예약 관리자"""

from typing import Optional
from simple_logger import init_logging, logger


class PromiseManager:
    """자산 예약 관리자.

    미체결 주문에 대한 자금 예약을 추적합니다.
    """

    @init_logging(level="INFO")
    def __init__(self) -> None:
        """PromiseManager 초기화."""
        self._promises: dict[str, dict] = {}
        logger.info("PromiseManager 초기화 완료")

    def lock(self, promise_id: str, symbol: str, amount: float) -> None:
        """자산 예약 생성.

        Args:
            promise_id: 고유 식별자
            symbol: 화폐 심볼
            amount: 예약 수량

        Raises:
            ValueError: promise_id 중복 시
        """
        logger.info(f"자산 예약 생성 시도: promise_id={promise_id}, symbol={symbol}, amount={amount}")

        if promise_id in self._promises:
            logger.error(f"중복된 promise_id: {promise_id}")
            raise ValueError(f"Promise {promise_id} already exists")

        self._promises[promise_id] = {
            "symbol": symbol,
            "amount": amount
        }
        logger.info(f"자산 예약 완료: promise_id={promise_id}")

    def unlock(self, promise_id: str) -> None:
        """자산 예약 삭제.

        Args:
            promise_id: 예약 식별자

        Raises:
            KeyError: 존재하지 않는 promise_id
        """
        logger.info(f"자산 예약 해제 시도: promise_id={promise_id}")

        if promise_id not in self._promises:
            logger.error(f"존재하지 않는 promise_id: {promise_id}")
            raise KeyError(f"Promise {promise_id} not found")

        del self._promises[promise_id]
        logger.info(f"자산 예약 해제 완료: promise_id={promise_id}")

    def get_locked_amount(self, symbol: str) -> float:
        """특정 화폐의 총 예약 수량 계산.

        Args:
            symbol: 화폐 심볼

        Returns:
            float: 예약된 총 수량
        """
        total = 0.0
        for promise in self._promises.values():
            if promise["symbol"] == symbol:
                total += promise["amount"]
        return total

    def get_promise(self, promise_id: str) -> Optional[dict]:
        """특정 promise 조회.

        Args:
            promise_id: 예약 식별자

        Returns:
            dict | None: {symbol: str, amount: float} 또는 None
        """
        return self._promises.get(promise_id)

    def get_all_promises(self) -> dict[str, dict]:
        """모든 promise 조회.

        Returns:
            dict[str, dict]: {promise_id: {symbol: str, amount: float}}
        """
        return self._promises.copy()

    def __repr__(self) -> str:
        """상세한 문자열 표현 반환."""
        return f"PromiseManager(promises={len(self._promises)})"
