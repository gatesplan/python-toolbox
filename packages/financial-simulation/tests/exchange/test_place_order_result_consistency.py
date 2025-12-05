"""place_order 결과 일관성 테스트

place_order() 반환값과 거래소 내부 상태(OrderBook, OrderHistory, Portfolio, trade_history) 간의 일관성 검증
"""

import pytest
import pandas as pd
import uuid
from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.candle import Candle
from financial_assets.multicandle import MultiCandle
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType, OrderStatus, TimeInForce
from financial_assets.order import SpotOrder


class TestPlaceOrderResultConsistency:
    """place_order() 결과 일관성 테스트"""

    @pytest.fixture
    def market_data(self):
        """테스트용 MarketData 생성"""
        btc_addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        btc_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(100)],
            'open': [50000.0] * 100,
            'high': [51000.0] * 100,
            'low': [49000.0] * 100,
            'close': [50000.0] * 100,
            'volume': [100.0] * 100
        })
        btc_candle = Candle(btc_addr, btc_df)
        mc = MultiCandle([btc_candle])
        return MarketData(mc, start_offset=10)

    @pytest.fixture
    def exchange(self, market_data):
        """테스트용 SpotExchange 생성"""
        return SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

    @pytest.fixture
    def btc_address(self):
        """BTC/USDT StockAddress"""
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    # ========== 1. place_order 반환값과 OrderHistory 일치 검증 ==========

    def test_place_order_trades_recorded_in_history(self, exchange, btc_address):
        """place_order 반환된 trades가 trade_history에 정확히 기록되는지 검증"""
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )

        # place_order 실행
        trades = exchange.place_order(order)

        # 반환된 trades의 총 체결량 계산
        total_filled_from_trades = sum(trade.pair.get_asset() for trade in trades)

        # trade_history에서 해당 order_id의 trades 조회
        history_trades = exchange.get_trades_by_order_id(order.order_id)

        # trade_history의 체결량 계산
        total_filled_from_history = sum(t.pair.get_asset() for t in history_trades)

        # 일치 검증
        assert abs(total_filled_from_trades - total_filled_from_history) < 1e-10, \
            f"trades 체결량({total_filled_from_trades})과 trade_history 체결량({total_filled_from_history})이 불일치"

        # OrderHistory에 주문이 기록되었는지 확인
        record = exchange._order_history.get_record(order.order_id)
        assert record is not None, "OrderHistory에 주문 기록이 없음"

    def test_place_order_trades_have_correct_order_id(self, exchange, btc_address):
        """반환된 trades의 order_id가 원본 order.order_id와 일치하는지 검증"""
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.05,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )

        trades = exchange.place_order(order)

        assert len(trades) > 0, "체결이 발생해야 함"

        for trade in trades:
            assert trade.order.order_id == order.order_id, \
                f"trade의 order_id({trade.order.order_id})가 원본({order.order_id})과 다름"

    # ========== 2. 전체 체결 시 OrderBook에서 제거 검증 ==========

    def test_full_fill_removes_from_orderbook(self, exchange, btc_address):
        """전체 체결 시 OrderBook에서 제거되는지 확인"""
        # MARKET 주문 (즉시 전체 체결 예상)
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.01,  # 소량 주문으로 전체 체결 보장
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )

        trades = exchange.place_order(order)
        total_filled = sum(trade.pair.get_asset() for trade in trades)

        # 전체 체결 확인
        if total_filled >= order.amount:
            # OrderBook에서 조회 시 None이어야 함
            orderbook_order = exchange._orderbook.get_order(order.order_id)
            assert orderbook_order is None, \
                f"전체 체결된 주문({order.order_id})이 OrderBook에 남아있음"
        else:
            pytest.skip("MARKET 주문이 전체 체결되지 않아 테스트 건너뜀")

    # ========== 3. 부분 체결 시 OrderBook에 잔여 수량 유지 ==========

    def test_partial_fill_keeps_in_orderbook(self, exchange, btc_address):
        """부분 체결 시 OrderBook에 잔여 수량이 정확하게 유지되는지 확인"""
        current_price = exchange.get_current_price("BTC/USDT")

        # LIMIT 주문 (현재가보다 낮은 가격 = 미체결 상태)
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price * 0.5,  # 현재가의 50%
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )

        trades = exchange.place_order(order)
        total_filled = sum(trade.pair.get_asset() for trade in trades)

        # 부분 체결 또는 미체결 확인
        if total_filled < order.amount:
            # OrderBook에 남아있어야 함
            orderbook_order = exchange._orderbook.get_order(order.order_id)
            assert orderbook_order is not None, \
                f"부분 체결/미체결 주문({order.order_id})이 OrderBook에 없음"

            # OrderBook의 주문은 원본과 동일해야 함
            assert orderbook_order.order_id == order.order_id
            assert orderbook_order.amount == order.amount
        else:
            pytest.skip("LIMIT 주문이 즉시 전체 체결되어 테스트 의미 없음")

    # ========== 4. trade_history에 추가 검증 ==========

    def test_trade_history_records_all_fills(self, exchange, btc_address):
        """모든 체결이 trade_history에 기록되는지 확인"""
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )

        # place_order 전 trade_history 개수
        history_before = len(exchange.get_trade_history())

        trades = exchange.place_order(order)

        # place_order 후 trade_history 개수
        history_after = len(exchange.get_trade_history())

        # 추가된 trade 개수가 반환된 trades 개수와 일치해야 함
        added_trades = history_after - history_before
        assert added_trades == len(trades), \
            f"trade_history에 추가된 개수({added_trades})가 반환된 trades 개수({len(trades)})와 다름"

        # trade_history에서 해당 주문의 trades 조회
        history_trades = exchange.get_trades_by_order_id(order.order_id)

        assert len(history_trades) == len(trades), \
            f"trade_history의 해당 주문 trades({len(history_trades)})가 반환값({len(trades)})과 다름"

    # ========== 5. 주문 상태 전이 검증 ==========

    def test_order_status_transition_new_to_filled(self, exchange, btc_address):
        """주문 상태 전이 검증: NEW → FILLED"""
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.01,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )

        trades = exchange.place_order(order)
        total_filled = sum(trade.pair.get_asset() for trade in trades)

        # 전체 체결 시 상태 확인
        if total_filled >= order.amount:
            status = exchange.get_order_status(order.order_id)
            assert status == OrderStatus.FILLED, \
                f"전체 체결 후 상태가 FILLED가 아님: {status}"

    def test_order_status_transition_new_to_canceled(self, exchange, btc_address):
        """주문 상태 전이 검증: NEW → CANCELED"""
        current_price = exchange.get_current_price("BTC/USDT")

        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price * 0.5,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )

        exchange.place_order(order)
        exchange.cancel_order(order.order_id)

        status = exchange.get_order_status(order.order_id)
        assert status == OrderStatus.CANCELED, \
            f"취소 후 상태가 CANCELED가 아님: {status}"

    # ========== 6. 여러 주문 독립성 검증 ==========

    def test_multiple_orders_independence(self, exchange, btc_address):
        """여러 주문이 독립적으로 처리되는지 확인"""
        orders = []
        all_trades = []

        # 3개의 독립적인 주문 생성
        for i in range(3):
            order = SpotOrder(
                order_id=f"order_{i}_{uuid.uuid4().hex[:8]}",
                stock_address=btc_address,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                price=None,
                amount=0.01 * (i + 1),  # 각각 다른 수량
                timestamp=exchange.get_current_timestamp(),
                min_trade_amount=0.01
            )
            orders.append(order)

            trades = exchange.place_order(order)
            all_trades.append(trades)

        # 각 주문의 trades가 올바른 order_id를 가지는지 확인
        for i, (order, trades) in enumerate(zip(orders, all_trades)):
            for trade in trades:
                assert trade.order.order_id == order.order_id, \
                    f"주문 {i}의 trade가 잘못된 order_id를 가짐"

        # 각 주문의 OrderHistory 기록이 독립적인지 확인
        for order in orders:
            record = exchange._order_history.get_record(order.order_id)
            assert record is not None, f"주문 {order.order_id}의 기록이 없음"
            assert record.order.order_id == order.order_id

    # ========== 7. client_order_id 추적 검증 ==========

    def test_client_order_id_tracking(self, exchange, btc_address):
        """client_order_id로 주문을 추적할 수 있는지 확인"""
        client_id = f"client_{uuid.uuid4().hex[:8]}"

        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.05,
            timestamp=exchange.get_current_timestamp(),
            client_order_id=client_id,
            min_trade_amount=0.01
        )

        trades = exchange.place_order(order)

        # trades에 client_order_id가 포함되어 있는지 확인
        for trade in trades:
            assert trade.order.client_order_id == client_id, \
                f"trade의 client_order_id({trade.order.client_order_id})가 원본({client_id})과 다름"

        # OrderHistory에서 client_order_id로 조회 가능한지 확인
        record = exchange._order_history.get_record(order.order_id)
        assert record.order.client_order_id == client_id, \
            f"OrderHistory의 client_order_id가 일치하지 않음"

