"""Multi-symbol trading simulation tests"""

import pytest
import pandas as pd
from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType
from financial_assets.price import Price
from financial_assets.candle import Candle
from financial_assets.multicandle import MultiCandle


class TestMultiSymbolTrading:
    """복수 종목 동시 거래 시뮬레이션 테스트"""

    @pytest.fixture
    def multi_symbol_market_data(self):
        """복수 종목 시장 데이터 생성"""
        # BTC/USDT Candle 생성
        btc_addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        btc_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(20)],
            'open': [50000.0 + i * 100 for i in range(20)],
            'high': [51000.0 + i * 100 for i in range(20)],
            'low': [49000.0 + i * 100 for i in range(20)],
            'close': [50000.0 + i * 100 for i in range(20)],
            'volume': [100.0] * 20
        })
        btc_candle = Candle(btc_addr, btc_df)

        # ETH/USDT Candle 생성
        eth_addr = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
        eth_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(20)],
            'open': [3000.0 + i * 10 for i in range(20)],
            'high': [3100.0 + i * 10 for i in range(20)],
            'low': [2900.0 + i * 10 for i in range(20)],
            'close': [3000.0 + i * 10 for i in range(20)],
            'volume': [200.0] * 20
        })
        eth_candle = Candle(eth_addr, eth_df)

        # SOL/USDT Candle 생성
        sol_addr = StockAddress("candle", "binance", "spot", "SOL", "USDT", "1m")
        sol_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(20)],
            'open': [100.0 + i * 1 for i in range(20)],
            'high': [105.0 + i * 1 for i in range(20)],
            'low': [95.0 + i * 1 for i in range(20)],
            'close': [100.0 + i * 1 for i in range(20)],
            'volume': [500.0] * 20
        })
        sol_candle = Candle(sol_addr, sol_df)

        # MultiCandle 생성
        mc = MultiCandle([btc_candle, eth_candle, sol_candle])

        # MarketData 생성
        return MarketData(mc, start_offset=0)

    def test_multi_symbol_market_data_initialization(self, multi_symbol_market_data):
        """복수 종목 MarketData 초기화 테스트"""
        symbols = multi_symbol_market_data.get_symbols()

        assert len(symbols) == 3
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols
        assert "SOL/USDT" in symbols

        # 각 종목의 현재 가격 조회 가능
        btc_price = multi_symbol_market_data.get_current("BTC/USDT")
        eth_price = multi_symbol_market_data.get_current("ETH/USDT")
        sol_price = multi_symbol_market_data.get_current("SOL/USDT")

        assert btc_price is not None
        assert eth_price is not None
        assert sol_price is not None

    def test_multi_symbol_trading_sequence(self, multi_symbol_market_data):
        """복수 종목 동시 거래 시나리오 테스트"""
        exchange = SpotExchange(
            initial_balance=100000.0,
            market_data=multi_symbol_market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

        # 1. BTC 매수
        btc_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        btc_order = SpotOrder(
            order_id="btc_buy_1",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.5,
            timestamp=1000,
            min_trade_amount=0.01
        )
        btc_trades = exchange.place_order(btc_order)
        assert len(btc_trades) > 0

        # 2. ETH 매수
        eth_address = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
        eth_order = SpotOrder(
            order_id="eth_buy_1",
            stock_address=eth_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=2.0,
            timestamp=1000,
            min_trade_amount=0.01
        )
        eth_trades = exchange.place_order(eth_order)
        assert len(eth_trades) > 0

        # 3. SOL 매수
        sol_address = StockAddress("candle", "binance", "spot", "SOL", "USDT", "1m")
        sol_order = SpotOrder(
            order_id="sol_buy_1",
            stock_address=sol_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=10.0,
            timestamp=1000,
            min_trade_amount=0.01
        )
        sol_trades = exchange.place_order(sol_order)
        assert len(sol_trades) > 0

        # 4. 포지션 확인
        positions = exchange.get_positions()
        assert "BTC-USDT" in positions
        assert "ETH-USDT" in positions
        assert "SOL-USDT" in positions

        # 5. 각 포지션 가치 확인
        btc_value = exchange.get_position_value("BTC-USDT")
        eth_value = exchange.get_position_value("ETH-USDT")
        sol_value = exchange.get_position_value("SOL-USDT")

        assert btc_value["book_value"] > 0
        assert eth_value["book_value"] > 0
        assert sol_value["book_value"] > 0

        # 6. 전체 통계 확인
        stats = exchange.get_statistics()
        assert stats["total_value"] > 0
        assert stats["position_value"] > 0
        assert "allocation" in stats

    def test_multi_symbol_step_synchronization(self, multi_symbol_market_data):
        """복수 종목 시간 동기화 테스트"""
        exchange = SpotExchange(
            initial_balance=100000.0,
            market_data=multi_symbol_market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

        # 초기 가격 저장
        initial_btc = multi_symbol_market_data.get_current("BTC/USDT")
        initial_eth = multi_symbol_market_data.get_current("ETH/USDT")
        initial_sol = multi_symbol_market_data.get_current("SOL/USDT")

        # 시간 진행
        assert exchange.step() == True

        # 모든 종목의 가격이 변경되었는지 확인
        new_btc = multi_symbol_market_data.get_current("BTC/USDT")
        new_eth = multi_symbol_market_data.get_current("ETH/USDT")
        new_sol = multi_symbol_market_data.get_current("SOL/USDT")

        assert new_btc.t > initial_btc.t
        assert new_eth.t > initial_eth.t
        assert new_sol.t > initial_sol.t

        # 모든 종목의 타임스탬프가 동일한지 확인
        assert new_btc.t == new_eth.t == new_sol.t

    def test_multi_symbol_balance_sharing(self, multi_symbol_market_data):
        """복수 종목 간 자금 공유 테스트"""
        exchange = SpotExchange(
            initial_balance=10000.0,  # 작은 초기 자금
            market_data=multi_symbol_market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

        # BTC 매수로 자금 대부분 사용
        btc_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        btc_order = SpotOrder(
            order_id="btc_buy_1",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.15,
            timestamp=1000,
            min_trade_amount=0.01
        )
        exchange.place_order(btc_order)

        # 남은 잔고 확인
        remaining_balance = exchange.get_balance("USDT")
        assert remaining_balance < 10000.0

        # ETH 매수 시도 (남은 잔고로 매수 가능한 만큼만)
        eth_address = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

        # 남은 잔고로 살 수 있는 ETH 수량 계산
        eth_price = multi_symbol_market_data.get_current("ETH/USDT").c
        affordable_eth = (remaining_balance * 0.8) / eth_price  # 안전마진 20%

        eth_order = SpotOrder(
            order_id="eth_buy_1",
            stock_address=eth_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=affordable_eth,
            timestamp=1000,
            min_trade_amount=0.01
        )

        # 부분 체결될 수 있음
        eth_trades = exchange.place_order(eth_order)
        # 거래가 발생했다면 잔고가 더 줄어듦
        if len(eth_trades) > 0:
            final_balance = exchange.get_balance("USDT")
            assert final_balance < remaining_balance

            # 두 종목 모두 포지션이 있어야 함
            positions = exchange.get_positions()
            assert "BTC-USDT" in positions
            assert "ETH-USDT" in positions

    def test_multi_symbol_sell_different_assets(self, multi_symbol_market_data):
        """복수 종목 개별 매도 테스트"""
        exchange = SpotExchange(
            initial_balance=100000.0,
            market_data=multi_symbol_market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

        # 복수 종목 매수
        btc_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        eth_address = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

        btc_buy = SpotOrder(
            order_id="btc_buy",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.5,
            timestamp=1000,
            min_trade_amount=0.01
        )
        eth_buy = SpotOrder(
            order_id="eth_buy",
            stock_address=eth_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=2.0,
            timestamp=1000,
            min_trade_amount=0.01
        )

        exchange.place_order(btc_buy)
        exchange.place_order(eth_buy)

        positions_before = exchange.get_positions()
        btc_amount = positions_before["BTC-USDT"]
        eth_amount = positions_before["ETH-USDT"]

        # BTC만 일부 매도
        btc_sell = SpotOrder(
            order_id="btc_sell",
            stock_address=btc_address,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=btc_amount * 0.5,  # 절반만 매도
            timestamp=1000,
            min_trade_amount=0.01
        )
        exchange.place_order(btc_sell)

        positions_after = exchange.get_positions()

        # BTC는 줄어들고 ETH는 그대로
        assert positions_after["BTC-USDT"] < btc_amount
        assert positions_after["ETH-USDT"] == eth_amount
