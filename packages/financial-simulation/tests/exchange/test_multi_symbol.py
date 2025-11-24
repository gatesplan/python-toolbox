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


class TestMarketDataCandles:
    """MarketData 캔들 조회 기능 테스트"""

    @pytest.fixture
    def market_data_with_candles(self):
        """캔들 데이터를 가진 MarketData 생성"""
        # BTC/USDT Candle 생성 (20개)
        btc_addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        btc_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(20)],
            'open': [50000.0 + i * 100 for i in range(20)],
            'high': [51000.0 + i * 100 for i in range(20)],
            'low': [49000.0 + i * 100 for i in range(20)],
            'close': [50000.0 + i * 100 for i in range(20)],
            'volume': [100.0 + i * 5 for i in range(20)]
        })
        btc_candle = Candle(btc_addr, btc_df)

        # ETH/USDT Candle 생성 (20개)
        eth_addr = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
        eth_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(20)],
            'open': [3000.0 + i * 10 for i in range(20)],
            'high': [3100.0 + i * 10 for i in range(20)],
            'low': [2900.0 + i * 10 for i in range(20)],
            'close': [3000.0 + i * 10 for i in range(20)],
            'volume': [200.0 + i * 10 for i in range(20)]
        })
        eth_candle = Candle(eth_addr, eth_df)

        # MultiCandle 생성
        mc = MultiCandle([btc_candle, eth_candle])

        # MarketData 생성 (커서를 중간으로)
        market_data = MarketData(mc, start_offset=5)
        return market_data

    def test_get_candles_full_range(self, market_data_with_candles):
        """전체 범위 캔들 조회 테스트"""
        # start_ts, end_ts 모두 None이면 처음부터 현재 커서까지
        df = market_data_with_candles.get_candles("BTC/USDT")

        # DataFrame 구조 확인
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        # 데이터 개수 확인 (start_offset=5이므로 0~5 인덱스, 총 6개)
        assert len(df) == 6

        # 첫 번째 데이터 확인
        assert df.iloc[0]['timestamp'] == 1000
        assert df.iloc[0]['open'] == 50000.0
        assert df.iloc[0]['close'] == 50000.0

        # 마지막 데이터 확인 (인덱스 5)
        assert df.iloc[-1]['timestamp'] == 1000 + 5 * 60
        assert df.iloc[-1]['open'] == 50000.0 + 5 * 100

    def test_get_candles_with_start_end(self, market_data_with_candles):
        """시작/종료 타임스탬프 지정 캔들 조회 테스트"""
        start_ts = 1000 + 2 * 60  # 인덱스 2
        end_ts = 1000 + 8 * 60    # 인덱스 8

        df = market_data_with_candles.get_candles(
            "BTC/USDT",
            start_ts=start_ts,
            end_ts=end_ts
        )

        # 인덱스 2부터 8까지 (2, 3, 4, 5, 6, 7, 8 = 7개)
        assert len(df) >= 5  # 최소 5개 이상

        # 타임스탬프 범위 확인
        assert df.iloc[0]['timestamp'] >= start_ts
        assert df.iloc[-1]['timestamp'] <= end_ts

    def test_get_candles_with_limit(self, market_data_with_candles):
        """limit 지정 캔들 조회 테스트"""
        # 전체 범위에서 최근 3개만
        df = market_data_with_candles.get_candles(
            "BTC/USDT",
            limit=3
        )

        # 정확히 3개
        assert len(df) == 3

        # 가장 최근 데이터부터 3개 (인덱스 3, 4, 5)
        assert df.iloc[-1]['timestamp'] == 1000 + 5 * 60

    def test_get_candles_with_start_and_limit(self, market_data_with_candles):
        """시작 타임스탬프 + limit 조회 테스트"""
        start_ts = 1000  # 처음부터

        df = market_data_with_candles.get_candles(
            "BTC/USDT",
            start_ts=start_ts,
            limit=4
        )

        # 최대 4개
        assert len(df) <= 4

    def test_get_candles_multiple_symbols(self, market_data_with_candles):
        """여러 심볼 캔들 조회 테스트"""
        btc_df = market_data_with_candles.get_candles("BTC/USDT")
        eth_df = market_data_with_candles.get_candles("ETH/USDT")

        # 둘 다 조회 가능
        assert len(btc_df) > 0
        assert len(eth_df) > 0

        # 동일한 개수
        assert len(btc_df) == len(eth_df)

        # 동일한 타임스탬프
        assert list(btc_df['timestamp']) == list(eth_df['timestamp'])

    def test_get_candles_invalid_symbol(self, market_data_with_candles):
        """존재하지 않는 심볼 조회 테스트"""
        with pytest.raises(KeyError):
            market_data_with_candles.get_candles("INVALID/USDT")

    def test_get_candles_dataframe_types(self, market_data_with_candles):
        """DataFrame 데이터 타입 확인 테스트"""
        df = market_data_with_candles.get_candles("BTC/USDT")

        # 각 컬럼의 데이터 타입 확인
        assert df['timestamp'].dtype in [int, 'int64']
        assert df['open'].dtype in [float, 'float64']
        assert df['high'].dtype in [float, 'float64']
        assert df['low'].dtype in [float, 'float64']
        assert df['close'].dtype in [float, 'float64']
        assert df['volume'].dtype in [float, 'float64']

    def test_get_candles_values_consistency(self, market_data_with_candles):
        """캔들 데이터 값 일관성 테스트"""
        df = market_data_with_candles.get_candles("BTC/USDT")

        for _, row in df.iterrows():
            # high >= open, close, low
            assert row['high'] >= row['open']
            assert row['high'] >= row['close']
            assert row['high'] >= row['low']

            # low <= open, close, high
            assert row['low'] <= row['open']
            assert row['low'] <= row['close']
            assert row['low'] <= row['high']

            # volume >= 0
            assert row['volume'] >= 0


class TestSpotExchangeCandles:
    """SpotExchange 캔들 조회 기능 테스트"""

    @pytest.fixture
    def exchange_with_candles(self):
        """캔들 데이터를 가진 SpotExchange 생성"""
        # BTC/USDT Candle 생성
        btc_addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        btc_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(20)],
            'open': [50000.0 + i * 100 for i in range(20)],
            'high': [51000.0 + i * 100 for i in range(20)],
            'low': [49000.0 + i * 100 for i in range(20)],
            'close': [50000.0 + i * 100 for i in range(20)],
            'volume': [100.0 + i * 5 for i in range(20)]
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
            'volume': [200.0 + i * 10 for i in range(20)]
        })
        eth_candle = Candle(eth_addr, eth_df)

        # MultiCandle 생성
        mc = MultiCandle([btc_candle, eth_candle])

        # MarketData 생성
        market_data = MarketData(mc, start_offset=5)

        # SpotExchange 생성
        exchange = SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )
        return exchange

    def test_get_candles_through_exchange(self, exchange_with_candles):
        """SpotExchange를 통한 캔들 조회 테스트"""
        df = exchange_with_candles.get_candles("BTC/USDT")

        # DataFrame 구조 확인
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        # 데이터 존재 확인
        assert len(df) > 0

    def test_get_candles_with_parameters(self, exchange_with_candles):
        """SpotExchange 캔들 조회 파라미터 테스트"""
        start_time = 1000
        end_time = 1000 + 10 * 60
        limit = 5

        df = exchange_with_candles.get_candles(
            symbol="BTC/USDT",
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        # limit 적용 확인
        assert len(df) <= limit

    def test_get_candles_multiple_symbols_through_exchange(self, exchange_with_candles):
        """SpotExchange를 통한 여러 심볼 캔들 조회 테스트"""
        btc_df = exchange_with_candles.get_candles("BTC/USDT")
        eth_df = exchange_with_candles.get_candles("ETH/USDT")

        # 둘 다 조회 가능
        assert len(btc_df) > 0
        assert len(eth_df) > 0

        # 동일한 타임스탬프
        assert list(btc_df['timestamp']) == list(eth_df['timestamp'])
