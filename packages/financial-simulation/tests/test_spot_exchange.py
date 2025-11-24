"""Tests for SpotExchange"""

import pytest
import pandas as pd
from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_simulation.tradesim.API.TradeSimulation import TradeSimulation
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType, TimeInForce
from financial_assets.price import Price
from financial_assets.candle import Candle
from financial_assets.multicandle import MultiCandle


@pytest.fixture
def sample_market_data():
    """테스트용 MarketData 생성 (충분한 유동성 제공)"""
    # BTC/USDT Candle 생성
    btc_addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
    btc_df = pd.DataFrame({
        'timestamp': [1000 + i * 60 for i in range(10)],
        'open': [50000.0] * 10,
        'high': [51000.0] * 10,
        'low': [49000.0] * 10,
        'close': [50000.0] * 10,
        'volume': [100.0] * 10
    })
    btc_candle = Candle(btc_addr, btc_df)

    # ETH/USDT Candle 생성
    eth_addr = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
    eth_df = pd.DataFrame({
        'timestamp': [1000 + i * 60 for i in range(10)],
        'open': [3000.0] * 10,
        'high': [3100.0] * 10,
        'low': [2900.0] * 10,
        'close': [3000.0] * 10,
        'volume': [1000.0] * 10
    })
    eth_candle = Candle(eth_addr, eth_df)

    # MultiCandle 생성
    mc = MultiCandle([btc_candle, eth_candle])

    # MarketData 생성
    return MarketData(mc, start_offset=0)


@pytest.fixture
def trade_simulation():
    """TradeSimulation 인스턴스 생성"""
    return TradeSimulation()


@pytest.fixture
def exchange(sample_market_data, trade_simulation):
    """SpotExchange 인스턴스 생성"""
    return SpotExchange(
        initial_balance=100000.0,
        market_data=sample_market_data,
        trade_simulation=trade_simulation,
        quote_currency="USDT"
    )


class TestSpotExchangeInit:
    """SpotExchange 초기화 테스트"""

    def test_init_creates_portfolio_with_initial_balance(self, exchange):
        """초기 자금이 Portfolio에 정상 입금되는지 확인"""
        # 초기 잔고 확인
        usdt_balance = exchange.get_balance("USDT")

        assert usdt_balance == 100000.0

    def test_init_creates_empty_orderbook(self, exchange):
        """OrderBook이 비어있는 상태로 초기화되는지 확인"""
        # 미체결 주문이 없어야 함
        open_orders = exchange.get_open_orders()

        assert len(open_orders) == 0

    def test_init_creates_empty_trade_history(self, exchange):
        """거래 내역이 비어있는 상태로 초기화되는지 확인"""
        # 거래 내역이 없어야 함
        trade_history = exchange.get_trade_history()

        assert len(trade_history) == 0


class TestSpotExchangePlaceOrder:
    """SpotExchange.place_order 테스트"""

    def test_place_order_buy_limit_success(self, exchange):
        """BUY LIMIT 주문이 정상 실행되는지 확인"""
        # BUY LIMIT 주문 생성 (body 범위 가격으로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,  # body 범위 (o=c=50000)
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.GTC
        )

        # 주문 실행
        trades = exchange.place_order(order)

        # 체결 내역이 반환되어야 함
        assert isinstance(trades, list)
        # body 범위이므로 전량 체결되어야 함
        assert len(trades) > 0
        # 체결 수량 확인
        total_filled = sum(trade.pair.get_asset() for trade in trades)
        assert total_filled == 1.0

    def test_place_order_sell_limit_success(self, exchange):
        """SELL LIMIT 주문이 정상 실행되는지 확인"""
        # 먼저 BTC를 매수하여 보유 (body 범위 가격)
        buy_order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        buy_trades = exchange.place_order(buy_order)
        # BTC 매수 확인
        assert len(buy_trades) > 0

        # SELL LIMIT 주문 생성 (body 범위 가격)
        sell_order = SpotOrder(
            order_id="order_002",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=50000.0,  # body 범위
            amount=0.5,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.GTC
        )

        # 주문 실행
        trades = exchange.place_order(sell_order)

        # 체결 내역이 반환되어야 함
        assert isinstance(trades, list)
        # body 범위이므로 전량 체결
        assert len(trades) > 0
        total_filled = sum(trade.pair.get_asset() for trade in trades)
        assert total_filled == 0.5

    def test_place_order_insufficient_balance_raises_error(self, exchange):
        """잔고 부족 시 주문 실패"""
        # 잔고를 초과하는 BUY 주문 생성
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=100.0,  # 5,000,000 USDT 필요 (잔고 100,000 초과)
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.GTC
        )

        # 주문 실행 시 에러 발생
        with pytest.raises(ValueError, match="잔고 부족"):
            exchange.place_order(order)

    def test_place_order_insufficient_asset_raises_error(self, exchange):
        """보유 자산 부족 시 SELL 주문 실패"""
        # BTC를 보유하지 않은 상태에서 SELL 주문
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.GTC
        )

        # 주문 실행 시 에러 발생
        with pytest.raises(ValueError, match="자산 부족"):
            exchange.place_order(order)

    def test_place_order_adds_to_trade_history(self, exchange):
        """체결된 주문이 거래 내역에 추가되는지 확인"""
        # 주문 실행 전 거래 내역 개수
        initial_count = len(exchange.get_trade_history())

        # LIMIT BUY 주문 (body 범위로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,  # body 범위
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )

        # 주문 실행
        trades = exchange.place_order(order)

        # 체결이 발생했어야 함
        assert len(trades) > 0
        # 거래 내역이 증가해야 함
        final_count = len(exchange.get_trade_history())
        # 반환된 Trade 수만큼 증가
        assert final_count == initial_count + len(trades)


class TestSpotExchangeCancelOrder:
    """SpotExchange.cancel_order 테스트"""

    def test_cancel_order_success(self, exchange):
        """미체결 주문 취소 성공"""
        # 미체결 주문 생성 (체결되기 어려운 가격으로)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10000.0,  # 현재가보다 훨씬 낮은 가격
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(order)

        # 미체결 주문 확인
        open_orders_before = len(exchange.get_open_orders())

        # 주문 취소
        exchange.cancel_order("order_001")

        # 미체결 주문이 감소해야 함
        open_orders_after = len(exchange.get_open_orders())
        assert open_orders_after == open_orders_before - 1

    def test_cancel_order_nonexistent_raises_error(self, exchange):
        """존재하지 않는 주문 취소 시 에러"""
        # 존재하지 않는 주문 ID로 취소 시도
        with pytest.raises(KeyError):
            exchange.cancel_order("nonexistent_order")


class TestSpotExchangeGetOpenOrders:
    """SpotExchange.get_open_orders 테스트"""

    def test_get_open_orders_all(self, exchange):
        """전체 미체결 주문 조회"""
        # 미체결 주문 2개 생성
        order1 = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10000.0,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.GTC
        )
        order2 = SpotOrder(
            order_id="order_002",
            stock_address=StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=1000.0,
            amount=5.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(order1)
        exchange.place_order(order2)

        # 전체 미체결 주문 조회
        open_orders = exchange.get_open_orders()

        # 2개가 조회되어야 함
        assert len(open_orders) == 2

    def test_get_open_orders_by_symbol(self, exchange):
        """심볼별 미체결 주문 조회"""
        # 서로 다른 심볼의 미체결 주문 생성
        order1 = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10000.0,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.GTC
        )
        order2 = SpotOrder(
            order_id="order_002",
            stock_address=StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=1000.0,
            amount=5.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(order1)
        exchange.place_order(order2)

        # BTC 심볼만 조회
        btc_orders = exchange.get_open_orders(symbol="BTC/USDT")

        # 1개만 조회되어야 함
        assert len(btc_orders) == 1
        assert btc_orders[0].stock_address.base == "BTC"


class TestSpotExchangeGetTradeHistory:
    """SpotExchange.get_trade_history 테스트"""

    def test_get_trade_history_all(self, exchange):
        """전체 거래 내역 조회"""
        # LIMIT 주문 2개 실행 (body 범위로 체결 보장)
        order1 = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        order2 = SpotOrder(
            order_id="order_002",
            stock_address=StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=3000.0,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades1 = exchange.place_order(order1)
        trades2 = exchange.place_order(order2)

        # 체결 확인
        assert len(trades1) > 0
        assert len(trades2) > 0
        # 전체 거래 내역 조회
        trade_history = exchange.get_trade_history()

        # 체결된 Trade가 있어야 함
        assert len(trade_history) == len(trades1) + len(trades2)

    def test_get_trade_history_by_symbol(self, exchange):
        """심볼별 거래 내역 조회"""
        # 서로 다른 심볼의 주문 실행 (body 범위로 체결 보장)
        order1 = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        order2 = SpotOrder(
            order_id="order_002",
            stock_address=StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=3000.0,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades1 = exchange.place_order(order1)
        trades2 = exchange.place_order(order2)

        # 체결 확인
        assert len(trades1) > 0
        assert len(trades2) > 0
        # BTC 심볼만 조회
        btc_trades = exchange.get_trade_history(symbol="BTC/USDT")

        # BTC 거래 내역만 반환되어야 함
        assert len(btc_trades) == len(trades1)


class TestSpotExchangeBalance:
    """SpotExchange.get_balance 테스트"""

    def test_get_balance_single_currency(self, exchange):
        """단일 화폐 잔고 조회"""
        # USDT 잔고 조회
        usdt_balance = exchange.get_balance("USDT")

        # 초기 자금 확인
        assert usdt_balance == 100000.0

    def test_get_balance_all_currencies(self, exchange):
        """전체 화폐 잔고 조회"""
        # 전체 잔고 조회
        all_balances = exchange.get_balance()

        # dict 형식으로 반환
        assert isinstance(all_balances, dict)
        # USDT가 포함되어야 함
        assert "USDT" in all_balances

    def test_get_balance_after_trade(self, exchange):
        """거래 후 잔고 변화 확인"""
        # 초기 잔고
        initial_balance = exchange.get_balance("USDT")

        # BTC 매수 (body 범위로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades = exchange.place_order(order)

        # 체결 확인
        assert len(trades) > 0
        # USDT 잔고가 감소해야 함
        final_balance = exchange.get_balance("USDT")
        assert final_balance < initial_balance


class TestSpotExchangePositions:
    """SpotExchange.get_positions 테스트"""

    def test_get_positions_empty(self, exchange):
        """초기 상태에서 포지션 없음"""
        # 포지션 조회
        positions = exchange.get_positions()

        # 빈 dict
        assert len(positions) == 0

    def test_get_positions_after_buy(self, exchange):
        """매수 후 포지션 생성 확인"""
        # BTC 매수 (body 범위로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.5,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades = exchange.place_order(order)

        # 체결 확인
        assert len(trades) > 0
        # 포지션 조회
        positions = exchange.get_positions()

        # BTC 포지션이 생성되어야 함
        assert len(positions) > 0


class TestSpotExchangePositionValue:
    """SpotExchange.get_position_value 테스트"""

    def test_get_position_value(self, exchange):
        """포지션 가치 조회"""
        # BTC 매수 (body 범위로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.5,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades = exchange.place_order(order)

        # 체결 확인
        assert len(trades) > 0
        # 포지션 가치 조회
        positions = exchange.get_positions()
        assert len(positions) > 0

        ticker = list(positions.keys())[0]
        position_value = exchange.get_position_value(ticker)

        # 필수 키 확인
        assert "book_value" in position_value
        assert "market_value" in position_value
        assert "pnl" in position_value
        assert "pnl_ratio" in position_value


class TestSpotExchangeTotalValue:
    """SpotExchange.get_total_value 테스트"""

    def test_get_total_value_initial(self, exchange):
        """초기 총 자산 가치"""
        # 총 자산 조회
        total_value = exchange.get_total_value()

        # 초기 자금과 동일해야 함
        assert total_value == 100000.0

    def test_get_total_value_after_trade(self, exchange):
        """거래 후 총 자산 가치"""
        # BTC 매수 (body 범위로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.5,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades = exchange.place_order(order)

        # 체결 확인
        assert len(trades) > 0
        # 총 자산 조회 (Currency + Position)
        total_value = exchange.get_total_value()

        # 양수여야 함
        assert total_value > 0


class TestSpotExchangeStatistics:
    """SpotExchange.get_statistics 테스트"""

    def test_get_statistics(self, exchange):
        """포트폴리오 통계 조회"""
        # BTC 매수 (body 범위로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.5,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades = exchange.place_order(order)

        # 체결 확인
        assert len(trades) > 0
        # 통계 조회
        stats = exchange.get_statistics()

        # 필수 키 확인
        assert "total_value" in stats
        assert "total_pnl" in stats
        assert "total_pnl_ratio" in stats
        assert "currency_value" in stats
        assert "position_value" in stats
        assert "allocation" in stats


class TestSpotExchangeStep:
    """SpotExchange.step 테스트"""

    def test_step_advances_market_data(self, exchange):
        """step()이 MarketData 커서를 이동시키는지 확인"""
        # 초기 타임스탬프
        initial_timestamp = exchange.get_current_timestamp()

        # 다음 틱으로 이동
        can_continue = exchange.step()

        # 타임스탬프가 변경되어야 함
        current_timestamp = exchange.get_current_timestamp()
        assert current_timestamp != initial_timestamp
        # 계속 진행 가능해야 함
        assert can_continue is True

    def test_step_expires_gtd_orders(self, exchange):
        """step()이 GTD 주문 만료를 처리하는지 확인"""
        # 현재 시각보다 1틱 후에 만료되는 GTD 주문 생성
        current_time = exchange.get_current_timestamp()
        expire_time = current_time + 120  # 2분 후 만료

        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10000.0,  # 체결되기 어려운 가격
            amount=1.0,
            timestamp=current_time,
            time_in_force=TimeInForce.GTD,
            expire_timestamp=expire_time
        )
        exchange.place_order(order)

        # 미체결 주문 확인
        open_orders_before = len(exchange.get_open_orders())
        assert open_orders_before == 1

        # 3번 step (만료 시각 도달)
        exchange.step()
        exchange.step()
        exchange.step()

        # GTD 주문이 만료되어 제거되어야 함
        open_orders_after = len(exchange.get_open_orders())
        assert open_orders_after == 0

    def test_step_returns_false_at_end(self, exchange):
        """데이터 끝에 도달하면 False 반환"""
        # 모든 틱을 소진
        while exchange.step():
            pass

        # is_finished()가 True여야 함
        assert exchange.is_finished() is True


class TestSpotExchangeReset:
    """SpotExchange.reset 테스트"""

    def test_reset_clears_positions(self, exchange):
        """reset()이 포지션을 초기화하는지 확인"""
        # BTC 매수 (body 범위로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.5,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades = exchange.place_order(order)

        # 체결 및 포지션 확인
        assert len(trades) > 0
        assert len(exchange.get_positions()) > 0

        # 리셋
        exchange.reset()

        # 포지션이 초기화되어야 함
        assert len(exchange.get_positions()) == 0

    def test_reset_clears_trade_history(self, exchange):
        """reset()이 거래 내역을 초기화하는지 확인"""
        # 주문 실행 (body 범위로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades = exchange.place_order(order)

        # 거래 내역 확인
        assert len(trades) > 0
        assert len(exchange.get_trade_history()) > 0

        # 리셋
        exchange.reset()

        # 거래 내역이 초기화되어야 함
        assert len(exchange.get_trade_history()) == 0

    def test_reset_restores_initial_balance(self, exchange):
        """reset()이 초기 잔고를 복원하는지 확인"""
        # BTC 매수 (잔고 소비, body 범위로 체결 보장)
        order = SpotOrder(
            order_id="order_001",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.5,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        trades = exchange.place_order(order)

        # 체결 확인
        assert len(trades) > 0
        # 잔고 감소 확인
        assert exchange.get_balance("USDT") < 100000.0

        # 리셋
        exchange.reset()

        # 초기 잔고로 복원되어야 함
        assert exchange.get_balance("USDT") == 100000.0


class TestSpotExchangeMarketDataQueries:
    """SpotExchange MarketData 조회 메서드 테스트"""

    def test_get_current_timestamp(self, exchange):
        """현재 타임스탬프 조회"""
        # 타임스탬프 조회
        timestamp = exchange.get_current_timestamp()

        # 양수여야 함
        assert timestamp > 0

    def test_get_current_price(self, exchange):
        """현재 가격 조회"""
        # BTC/USDT 가격 조회
        price = exchange.get_current_price("BTC/USDT")

        # 가격이 존재해야 함
        assert price is not None
        assert price > 0

    def test_get_current_price_nonexistent_symbol(self, exchange):
        """존재하지 않는 심볼 가격 조회"""
        # 존재하지 않는 심볼
        price = exchange.get_current_price("NONEXISTENT/USDT")

        # None 반환
        assert price is None

    def test_is_finished_initial(self, exchange):
        """초기 상태에서는 종료되지 않음"""
        # 시뮬레이션 시작 상태
        assert exchange.is_finished() is False

    def test_is_finished_after_exhausting_data(self, exchange):
        """데이터 소진 후 종료 확인"""
        # 모든 틱 소진
        while exchange.step():
            pass

        # 종료 상태
        assert exchange.is_finished() is True
