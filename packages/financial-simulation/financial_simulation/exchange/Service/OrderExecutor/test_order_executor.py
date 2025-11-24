"""OrderExecutor 테스트."""

import pytest
from unittest.mock import Mock, MagicMock
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.constants import OrderSide, OrderType, TimeInForce
from financial_assets.price import Price
from financial_assets.stock_address import StockAddress
from financial_simulation.exchange.Core.Portfolio import Portfolio
from financial_simulation.exchange.Core.OrderBook import OrderBook
from financial_simulation.exchange.Core.MarketData import MarketData
from .OrderExecutor import OrderExecutor


@pytest.fixture
def portfolio():
    """테스트용 Portfolio 생성."""
    from financial_assets.trade import SpotTrade
    from financial_assets.pair import Pair
    from financial_assets.token import Token
    from financial_assets.order import SpotOrder
    from financial_assets.stock_address import StockAddress
    from financial_assets.constants import OrderSide, OrderType

    portfolio = Portfolio()
    portfolio.deposit_currency("USDT", 100000.0)

    # SELL 테스트를 위해 BTC 포지션 생성 (Currency가 아닌 PairStack)
    # 더미 주문 생성
    dummy_stock_address = StockAddress(
        archetype="spot",
        exchange="test",
        tradetype="spot",
        base="BTC",
        quote="USDT",
        timeframe="1m"
    )
    dummy_order = SpotOrder(
        order_id="dummy_init",
        stock_address=dummy_stock_address,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=50000.0,
        amount=10.0,
        timestamp=1,
    )
    dummy_trade = SpotTrade(
        trade_id="dummy_init_trade",
        order=dummy_order,
        pair=Pair(
            asset=Token("BTC", 10.0),
            value=Token("USDT", 500000.0),
        ),
        timestamp=1,
        fee=None,
    )
    # USDT 추가 입금 (더미 거래용)
    portfolio.deposit_currency("USDT", 500000.0)
    portfolio.process_trade(dummy_trade)

    return portfolio


@pytest.fixture
def orderbook():
    """테스트용 OrderBook 생성."""
    return OrderBook()


@pytest.fixture
def market_data():
    """테스트용 MarketData 생성."""
    data = {
        "BTC/USDT": [
            Price(exchange="test", market="BTC/USDT", t=1000, o=50000, h=51000, l=49000, c=50000, v=100),
            Price(exchange="test", market="BTC/USDT", t=2000, o=50000, h=52000, l=49000, c=51000, v=150),
        ]
    }
    return MarketData(data)


@pytest.fixture
def trade_simulation():
    """테스트용 TradeSimulation mock 생성."""
    return Mock()


@pytest.fixture
def stock_address():
    """테스트용 StockAddress 생성."""
    return StockAddress(
        archetype="spot",
        exchange="test",
        tradetype="spot",
        base="BTC",
        quote="USDT",
        timeframe="1m"
    )


@pytest.fixture
def executor(portfolio, orderbook, market_data, trade_simulation):
    """테스트용 OrderExecutor 생성."""
    return OrderExecutor(portfolio, orderbook, market_data, trade_simulation)


def create_spot_trade(trade_id: str, order: SpotOrder, fill_amount: float, fill_price: float) -> SpotTrade:
    """테스트용 SpotTrade 생성 헬퍼 함수."""
    trade_value = fill_price * fill_amount
    return SpotTrade(
        trade_id=trade_id,
        order=order,
        pair=Pair(
            asset=Token(order.stock_address.base.upper(), fill_amount),
            value=Token(order.stock_address.quote.upper(), trade_value),
        ),
        timestamp=order.timestamp,
        fee=None,
    )


class TestOrderExecutorFullFill:
    """완전 체결 테스트."""

    def test_buy_order_full_fill(self, executor, stock_address, trade_simulation, portfolio, orderbook):
        """BUY 주문 완전 체결."""
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=1000,
        )

        # TradeSimulation이 완전 체결 반환
        trade = create_spot_trade("trade_1", order, 1.0, 50000.0)
        trade_simulation.process.return_value = [trade]

        initial_usdt = portfolio.get_balance("USDT")
        initial_btc_position = portfolio.get_positions().get("BTC-USDT", 0.0)

        # 주문 실행
        trades = executor.execute_order(order)

        # 체결 확인
        assert len(trades) == 1
        assert trades[0] == trade

        # Portfolio 업데이트 확인 (BUY: USDT 차감, BTC 포지션 증가)
        assert portfolio.get_balance("USDT") == initial_usdt - 50000.0
        assert portfolio.get_positions()["BTC-USDT"] == initial_btc_position + 1.0

        # OrderBook에 추가되지 않음 (완전 체결)
        assert orderbook.get_order("order_1") is None

    def test_sell_order_full_fill(self, executor, stock_address, trade_simulation, portfolio, orderbook):
        """SELL 주문 완전 체결."""
        order = SpotOrder(
            order_id="order_2",
            stock_address=stock_address,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=1000,
        )

        # TradeSimulation이 완전 체결 반환
        trade = create_spot_trade("trade_2", order, 1.0, 50000.0)
        trade_simulation.process.return_value = [trade]

        initial_usdt = portfolio.get_balance("USDT")
        initial_btc_position = portfolio.get_positions()["BTC-USDT"]

        # 주문 실행
        trades = executor.execute_order(order)

        # 체결 확인
        assert len(trades) == 1
        assert trades[0] == trade

        # Portfolio 업데이트 확인 (SELL: BTC 포지션 차감, USDT 증가)
        assert portfolio.get_balance("USDT") == initial_usdt + 50000.0
        assert portfolio.get_positions()["BTC-USDT"] == initial_btc_position - 1.0

        # OrderBook에 추가되지 않음 (완전 체결)
        assert orderbook.get_order("order_2") is None


class TestOrderExecutorPartialFill:
    """부분 체결 테스트."""

    def test_buy_order_partial_fill(self, executor, stock_address, trade_simulation, portfolio, orderbook):
        """BUY 주문 부분 체결 - 미체결 수량 OrderBook 추가 및 자산 잠금."""
        order = SpotOrder(
            order_id="order_3",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=2.0,
            timestamp=1000,
        )

        # TradeSimulation이 부분 체결 반환 (1.0 BTC만 체결)
        trade = create_spot_trade("trade_3", order, 1.0, 50000.0)
        trade_simulation.process.return_value = [trade]

        initial_usdt = portfolio.get_balance("USDT")
        initial_btc_position = portfolio.get_positions().get("BTC-USDT", 0.0)

        # 주문 실행
        trades = executor.execute_order(order)

        # 체결 확인 (1.0만 체결)
        assert len(trades) == 1
        assert trades[0].pair.get_asset() == 1.0

        # Portfolio 업데이트 확인 (체결된 1.0만큼만)
        assert portfolio.get_balance("USDT") == initial_usdt - 50000.0
        assert portfolio.get_positions()["BTC-USDT"] == initial_btc_position + 1.0

        # OrderBook에 미체결 주문 추가 확인
        pending_order = orderbook.get_order("order_3")
        assert pending_order is not None
        assert pending_order.amount == 2.0  # 원래 주문 수량

        # 미체결 수량만큼 자산 잠금 확인 (1.0 BTC * 50000 = 50000 USDT)
        assert portfolio.get_locked_balance("USDT") == 50000.0

    def test_sell_order_partial_fill(self, executor, stock_address, trade_simulation, portfolio, orderbook):
        """SELL 주문 부분 체결 - 미체결 수량 OrderBook 추가 및 자산 잠금."""
        order = SpotOrder(
            order_id="order_4",
            stock_address=stock_address,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=2.0,
            timestamp=1000,
        )

        # TradeSimulation이 부분 체결 반환 (1.0 BTC만 체결)
        trade = create_spot_trade("trade_4", order, 1.0, 50000.0)
        trade_simulation.process.return_value = [trade]

        initial_usdt = portfolio.get_balance("USDT")
        initial_btc_position = portfolio.get_positions()["BTC-USDT"]

        # 주문 실행
        trades = executor.execute_order(order)

        # 체결 확인 (1.0만 체결)
        assert len(trades) == 1
        assert trades[0].pair.get_asset() == 1.0

        # Portfolio 업데이트 확인 (체결된 1.0만큼만)
        assert portfolio.get_balance("USDT") == initial_usdt + 50000.0
        assert portfolio.get_positions()["BTC-USDT"] == initial_btc_position - 1.0

        # OrderBook에 미체결 주문 추가 확인
        pending_order = orderbook.get_order("order_4")
        assert pending_order is not None

        # 미체결 수량만큼 자산 잠금 확인 (1.0 BTC)
        # SELL은 포지션(BTC-USDT ticker)을 잠금
        assert portfolio.get_locked_position("BTC-USDT") == 1.0


class TestOrderExecutorNoFill:
    """체결 실패 테스트."""

    def test_no_fill_order(self, executor, stock_address, trade_simulation, portfolio, orderbook):
        """체결 실패 - OrderBook 추가 및 자산 잠금."""
        order = SpotOrder(
            order_id="order_5",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=1000,
        )

        # TradeSimulation이 빈 리스트 반환 (체결 실패)
        trade_simulation.process.return_value = []

        initial_usdt = portfolio.get_balance("USDT")
        initial_btc_position = portfolio.get_positions().get("BTC-USDT", 0.0)

        # 주문 실행
        trades = executor.execute_order(order)

        # 체결 없음
        assert len(trades) == 0

        # Portfolio 변화 없음
        assert portfolio.get_balance("USDT") == initial_usdt
        assert portfolio.get_positions().get("BTC-USDT", 0.0) == initial_btc_position

        # OrderBook에 추가 확인
        pending_order = orderbook.get_order("order_5")
        assert pending_order is not None

        # 전체 수량만큼 자산 잠금 확인
        assert portfolio.get_locked_balance("USDT") == 50000.0


class TestOrderExecutorTimeInForce:
    """TimeInForce 처리 테스트."""

    def test_fok_full_fill_success(self, executor, stock_address, trade_simulation, portfolio, orderbook):
        """FOK 주문 - 완전 체결 성공."""
        order = SpotOrder(
            order_id="order_6",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=1000,
            time_in_force=TimeInForce.FOK,
        )

        # 완전 체결
        trade = create_spot_trade("trade_6", order, 1.0, 50000.0)
        trade_simulation.process.return_value = [trade]

        # 주문 실행
        trades = executor.execute_order(order)

        # 성공
        assert len(trades) == 1
        assert orderbook.get_order("order_6") is None

    def test_fok_partial_fill_failure(self, executor, stock_address, trade_simulation, portfolio, orderbook):
        """FOK 주문 - 부분 체결 실패."""
        order = SpotOrder(
            order_id="order_7",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=2.0,
            timestamp=1000,
            time_in_force=TimeInForce.FOK,
        )

        # 부분 체결
        trade = create_spot_trade("trade_7", order, 1.0, 50000.0)
        trade_simulation.process.return_value = [trade]

        initial_usdt = portfolio.get_balance("USDT")
        initial_btc_position = portfolio.get_positions().get("BTC-USDT", 0.0)

        # 예외 발생 확인
        with pytest.raises(ValueError, match="FOK 주문 실패"):
            executor.execute_order(order)

        # Portfolio 롤백 확인 (변화 없음)
        assert portfolio.get_balance("USDT") == initial_usdt
        assert portfolio.get_positions().get("BTC-USDT", 0.0) == initial_btc_position

        # OrderBook에 추가되지 않음
        assert orderbook.get_order("order_7") is None

    def test_ioc_partial_fill(self, executor, stock_address, trade_simulation, portfolio, orderbook):
        """IOC 주문 - 부분 체결 후 미체결 즉시 취소."""
        order = SpotOrder(
            order_id="order_8",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=2.0,
            timestamp=1000,
            time_in_force=TimeInForce.IOC,
        )

        # 부분 체결
        trade = create_spot_trade("trade_8", order, 1.0, 50000.0)
        trade_simulation.process.return_value = [trade]

        # 주문 실행
        trades = executor.execute_order(order)

        # 체결된 부분만 처리
        assert len(trades) == 1
        assert trades[0].pair.get_asset() == 1.0

        # OrderBook에 추가되지 않음 (IOC는 미체결 즉시 취소)
        assert orderbook.get_order("order_8") is None

        # 자산 잠금 없음
        assert portfolio.get_locked_balance("USDT") == 0.0


class TestOrderExecutorCancelOrder:
    """주문 취소 테스트."""

    def test_cancel_pending_order(self, executor, stock_address, trade_simulation, portfolio, orderbook):
        """미체결 주문 취소 - OrderBook 제거 및 자산 해제."""
        order = SpotOrder(
            order_id="order_9",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=1000,
        )

        # 체결 실패로 OrderBook에 추가
        trade_simulation.process.return_value = []
        executor.execute_order(order)

        # 자산 잠금 확인
        assert portfolio.get_locked_balance("USDT") == 50000.0
        assert orderbook.get_order("order_9") is not None

        # 주문 취소
        executor.cancel_order("order_9")

        # OrderBook에서 제거 확인
        assert orderbook.get_order("order_9") is None

        # 자산 해제 확인
        assert portfolio.get_locked_balance("USDT") == 0.0

    def test_cancel_nonexistent_order(self, executor):
        """존재하지 않는 주문 취소 - KeyError 발생."""
        with pytest.raises(KeyError):
            executor.cancel_order("nonexistent_order")
