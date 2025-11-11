"""거래소 맥락의 자산 관리"""

from financial_assets.wallet import SpotWallet
from financial_assets.trade import SpotTrade
from simple_logger import init_logging, logger
from .PromiseManager import PromiseManager


class Portfolio:
    """거래소 맥락의 자산 관리.

    SpotWallet을 래핑하고 자산 예약(promise) 시스템을 제공하여
    미체결 주문에 대한 자금 잠금을 관리합니다.
    """

    @init_logging(level="INFO")
    def __init__(self) -> None:
        """Portfolio 초기화."""
        self._wallet = SpotWallet()
        self._promise_manager = PromiseManager()
        logger.info("Portfolio 초기화 완료")

    # ===== 잔고 관리 =====

    def deposit_currency(self, symbol: str, amount: float) -> None:
        """화폐 입금.

        Args:
            symbol: 화폐 심볼 (예: "USDT", "BTC")
            amount: 입금 수량
        """
        self._wallet.deposit_currency(symbol, amount)

    def withdraw_currency(self, symbol: str, amount: float) -> None:
        """화폐 출금.

        Args:
            symbol: 화폐 심볼
            amount: 출금 수량

        Raises:
            ValueError: 사용 가능 잔고 부족 시
        """
        available = self.get_available_balance(symbol)
        if available < amount:
            raise ValueError(
                f"Insufficient available balance for {symbol}: "
                f"requested {amount}, available {available}"
            )

        self._wallet.withdraw_currency(symbol, amount)

    def get_balance(self, symbol: str) -> float:
        """총 잔고 조회 (예약 자산 포함).

        Args:
            symbol: 화폐 심볼

        Returns:
            float: 총 보유 수량
        """
        return self._wallet.get_currency_balance(symbol)

    def get_available_balance(self, symbol: str) -> float:
        """사용 가능 잔고 조회 (총 잔고 - 예약 자산).

        Args:
            symbol: 화폐 심볼

        Returns:
            float: 사용 가능 수량
        """
        total = self.get_balance(symbol)
        locked = self.get_locked_balance(symbol)
        return total - locked

    def get_locked_balance(self, symbol: str) -> float:
        """예약된 자산 수량 조회.

        Args:
            symbol: 화폐 심볼

        Returns:
            float: 예약된 수량
        """
        return self._promise_manager.get_locked_amount(symbol)

    # ===== 자산 예약 (Promise) =====

    def lock_currency(self, promise_id: str, symbol: str, amount: float) -> None:
        """자산 예약 (미체결 주문용).

        Args:
            promise_id: 예약 식별자 (주문 ID 등)
            symbol: 화폐 심볼
            amount: 예약 수량

        Raises:
            ValueError: 사용 가능 잔고 부족 시
        """
        logger.info(f"자산 잠금 요청: promise_id={promise_id}, symbol={symbol}, amount={amount}")

        available = self.get_available_balance(symbol)
        if available < amount:
            logger.error(f"사용 가능 잔고 부족: symbol={symbol}, requested={amount}, available={available}")
            raise ValueError(
                f"Insufficient available balance for {symbol}: "
                f"requested {amount}, available {available}"
            )

        self._promise_manager.lock(promise_id, symbol, amount)
        logger.info(f"자산 잠금 완료: promise_id={promise_id}")

    def unlock_currency(self, promise_id: str) -> None:
        """자산 예약 해제.

        Args:
            promise_id: 예약 식별자
        """
        logger.info(f"자산 잠금 해제 요청: promise_id={promise_id}")
        self._promise_manager.unlock(promise_id)
        logger.info(f"자산 잠금 해제 완료: promise_id={promise_id}")

    # ===== 거래 처리 =====

    def process_trade(self, trade: SpotTrade) -> None:
        """거래 처리 (SpotWallet에 위임).

        BUY: quote 화폐 차감 + 자산 추가
        SELL: 자산 차감 + quote 화폐 증가

        Args:
            trade: 체결된 거래 객체

        Raises:
            ValueError: 잔고 부족 시
        """
        logger.info(f"거래 처리 시작: trade_id={trade.trade_id}, side={trade.side.value}")
        self._wallet.process_trade(trade)
        logger.info(f"거래 처리 완료: trade_id={trade.trade_id}")

    # ===== 조회 =====

    def get_positions(self) -> dict[str, float]:
        """보유 포지션 조회 (ticker -> 자산 수량).

        Returns:
            dict[str, float]: {ticker: asset_amount}
        """
        positions = {}
        tickers = self._wallet.list_tickers()

        for ticker in tickers:
            pair_stack = self._wallet.get_pair_stack(ticker)
            if pair_stack is not None:
                positions[ticker] = pair_stack.total_asset_amount()

        return positions

    def get_currencies(self) -> list[str]:
        """보유 화폐 목록.

        Returns:
            list[str]: 화폐 심볼 리스트
        """
        return self._wallet.list_currencies()

    def get_wallet(self) -> SpotWallet:
        """내부 SpotWallet 접근 (고급 기능용).

        Returns:
            SpotWallet: 내부 지갑 객체
        """
        return self._wallet

    def __repr__(self) -> str:
        """상세한 문자열 표현 반환."""
        currencies = len(self.get_currencies())
        positions = len(self.get_positions())
        promises = len(self._promise_manager.get_all_promises())
        return (
            f"Portfolio(currencies={currencies}, "
            f"positions={positions}, promises={promises})"
        )
