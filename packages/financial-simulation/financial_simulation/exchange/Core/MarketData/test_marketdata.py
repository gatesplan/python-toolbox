"""MarketData 테스트 - MultiCandle 기반"""

import pytest
import pandas as pd
import numpy as np
from financial_assets.candle import Candle
from financial_assets.stock_address import StockAddress
from financial_assets.multicandle import MultiCandle
from financial_assets.price import Price
from .MarketData import MarketData


def make_candle(symbol: str, timestamps: list[int], closes: list[float]) -> Candle:
    """테스트용 Candle 생성 헬퍼"""
    base, quote = symbol.split("/")
    addr = StockAddress("candle", "binance", "spot", base, quote, "1m")

    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': closes,
        'high': [c * 1.01 for c in closes],
        'low': [c * 0.99 for c in closes],
        'close': closes,
        'volume': [100.0] * len(closes)
    })

    return Candle(addr, df)


class TestMarketDataInit:
    """초기화 테스트"""

    def test_init_basic(self):
        """기본 초기화"""
        candle1 = make_candle("BTC/USDT", [1000, 2000, 3000], [50000, 51000, 52000])
        candle2 = make_candle("ETH/USDT", [1000, 2000, 3000], [3000, 3100, 3200])

        mc = MultiCandle([candle1, candle2])
        market = MarketData(mc)

        assert market.get_cursor_idx() == 0
        assert len(market.get_symbols()) == 2
        assert market.get_current_timestamp() == 1000

    def test_init_with_offset(self):
        """offset 적용 초기화"""
        candle = make_candle("BTC/USDT", list(range(1000, 11000, 1000)), [50000] * 10)

        mc = MultiCandle([candle])
        market = MarketData(mc, start_offset=5)

        assert market.get_cursor_idx() == 5
        assert market.get_current_timestamp() == 6000

    def test_init_with_random_offset(self):
        """random_offset 적용 초기화"""
        candle = make_candle("BTC/USDT", list(range(1000, 101000, 1000)), [50000] * 100)

        mc = MultiCandle([candle])
        market = MarketData(mc, random_offset=True)

        # 랜덤이므로 범위만 확인
        assert 0 <= market.get_cursor_idx() < 100

    def test_init_with_offset_and_random(self):
        """offset + random_offset 복합"""
        candle = make_candle("BTC/USDT", list(range(1000, 101000, 1000)), [50000] * 100)

        mc = MultiCandle([candle])
        market = MarketData(mc, start_offset=10, random_offset=True)

        # start_offset 10 + random
        assert market.get_cursor_idx() >= 10


class TestMarketDataQuery:
    """데이터 조회 테스트"""

    @pytest.fixture
    def market_data(self):
        """테스트용 MarketData"""
        candle1 = make_candle("BTC/USDT", [1000, 2000, 3000], [50000, 51000, 52000])
        candle2 = make_candle("ETH/USDT", [1000, 2000, 3000], [3000, 3100, 3200])

        mc = MultiCandle([candle1, candle2])
        return MarketData(mc)

    def test_get_current(self, market_data):
        """특정 심볼의 현재 가격 조회"""
        price = market_data.get_current("BTC/USDT")

        assert isinstance(price, Price)
        assert price.t == 1000
        assert price.c == 50000

    def test_get_current_invalid_symbol(self, market_data):
        """존재하지 않는 심볼 조회 - KeyError"""
        with pytest.raises(KeyError):
            market_data.get_current("INVALID/USDT")

    def test_get_current_all(self, market_data):
        """모든 심볼의 현재 가격 조회"""
        prices = market_data.get_current_all()

        assert isinstance(prices, dict)
        assert len(prices) == 2
        assert "BTC/USDT" in prices
        assert "ETH/USDT" in prices
        assert isinstance(prices["BTC/USDT"], Price)

    def test_get_current_timestamp(self, market_data):
        """현재 타임스탬프 조회"""
        timestamp = market_data.get_current_timestamp()
        assert timestamp == 1000

    def test_get_symbols(self, market_data):
        """심볼 리스트 조회"""
        symbols = market_data.get_symbols()
        assert len(symbols) == 2
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols


class TestMarketDataStep:
    """커서 이동 테스트"""

    def test_step_basic(self):
        """기본 step 동작"""
        candle = make_candle("BTC/USDT", [1000, 2000, 3000], [50000, 51000, 52000])

        mc = MultiCandle([candle])
        market = MarketData(mc)

        initial_idx = market.get_cursor_idx()
        initial_ts = market.get_current_timestamp()

        success = market.step()

        assert success is True
        assert market.get_cursor_idx() == initial_idx + 1
        assert market.get_current_timestamp() == 2000

    def test_step_until_end(self):
        """끝까지 step"""
        candle = make_candle("BTC/USDT", [1000, 2000, 3000], [50000, 51000, 52000])

        mc = MultiCandle([candle])
        market = MarketData(mc)

        # 3개 데이터: 인덱스 0, 1, 2
        # step 2번 가능, 3번째는 False
        assert market.step() is True  # 0 -> 1
        assert market.step() is True  # 1 -> 2
        assert market.step() is False  # 2 -> 끝

    def test_step_changes_current(self):
        """step 후 current 값 변경 확인"""
        candle = make_candle("BTC/USDT", [1000, 2000, 3000], [50000, 51000, 52000])

        mc = MultiCandle([candle])
        market = MarketData(mc)

        first_price = market.get_current("BTC/USDT")
        market.step()
        second_price = market.get_current("BTC/USDT")

        assert first_price.c == 50000
        assert second_price.c == 51000


class TestMarketDataReset:
    """리셋 테스트"""

    def test_reset_basic(self):
        """기본 reset"""
        candle = make_candle("BTC/USDT", list(range(1000, 6000, 1000)), [50000] * 5)

        mc = MultiCandle([candle])
        market = MarketData(mc)

        initial_idx = market.get_cursor_idx()

        # 몇 번 이동
        market.step()
        market.step()
        assert market.get_cursor_idx() != initial_idx

        # 리셋
        market.reset()
        assert market.get_cursor_idx() == initial_idx

    def test_reset_without_override(self):
        """override=False 리셋 (같은 시작점)"""
        candle = make_candle("BTC/USDT", list(range(1000, 11000, 1000)), [50000] * 10)

        mc = MultiCandle([candle])
        market = MarketData(mc, random_offset=True)

        first_start = market.get_cursor_idx()

        market.step()
        market.step()
        market.reset(override=False)

        assert market.get_cursor_idx() == first_start

    def test_reset_with_override(self):
        """override=True 리셋 (새로운 랜덤 시작점)"""
        candle = make_candle("BTC/USDT", list(range(1000, 101000, 1000)), [50000] * 100)

        mc = MultiCandle([candle])
        market = MarketData(mc, random_offset=True)

        first_start = market.get_cursor_idx()

        # override=True로 여러 번 리셋
        cursors = [first_start]
        for _ in range(10):
            market.reset(override=True)
            cursors.append(market.get_cursor_idx())

        # 최소한 한 번은 달라야 함 (확률적으로)
        assert len(set(cursors)) > 1

    def test_reset_without_random_offset(self):
        """random_offset=False일 때 override는 무의미"""
        candle = make_candle("BTC/USDT", list(range(1000, 11000, 1000)), [50000] * 10)

        mc = MultiCandle([candle])
        market = MarketData(mc, random_offset=False)

        first_start = market.get_cursor_idx()

        # override=True여도 random_offset=False면 같은 시작점
        market.reset(override=True)
        assert market.get_cursor_idx() == first_start


class TestMarketDataState:
    """상태 조회 테스트"""

    def test_is_finished(self):
        """종료 여부 확인"""
        candle = make_candle("BTC/USDT", [1000, 2000, 3000], [50000, 51000, 52000])

        mc = MultiCandle([candle])
        market = MarketData(mc)

        assert market.is_finished() is False

        # 끝까지 이동
        while market.step():
            pass

        assert market.is_finished() is True

    def test_get_progress(self):
        """진행률 확인"""
        candle = make_candle("BTC/USDT", list(range(1000, 11000, 1000)), [50000] * 10)

        mc = MultiCandle([candle])
        market = MarketData(mc)

        # 시작 (0/9)
        progress = market.get_progress()
        assert progress == 0.0

        # 중간 (5/9)
        for _ in range(5):
            market.step()
        mid_progress = market.get_progress()
        assert 0.5 <= mid_progress <= 0.6

        # 끝 (9/9)
        while market.step():
            pass
        final_progress = market.get_progress()
        assert final_progress == 1.0


class TestMarketDataVariableLength:
    """가변 길이 데이터 테스트 (NaN 처리)"""

    def test_variable_length_get_current(self):
        """길이가 다른 데이터에서 get_current"""
        # BTC: 10개, ETH: 5개 (뒤쪽 5개만)
        candle1 = make_candle("BTC/USDT", list(range(1000, 11000, 1000)), [50000] * 10)
        candle2 = make_candle("ETH/USDT", list(range(6000, 11000, 1000)), [3000] * 5)

        mc = MultiCandle([candle1, candle2])
        market = MarketData(mc)

        # 처음 (timestamp 1000): BTC만 있음, ETH는 NaN
        btc = market.get_current("BTC/USDT")
        assert btc is not None
        assert btc.c == 50000

        # ETH는 NaN이므로 조회 시 None 또는 예외
        # MultiCandle의 동작에 따라 달라질 수 있음

    def test_variable_length_get_current_all(self):
        """길이가 다른 데이터에서 get_current_all"""
        candle1 = make_candle("BTC/USDT", list(range(1000, 11000, 1000)), [50000] * 10)
        candle2 = make_candle("ETH/USDT", list(range(6000, 11000, 1000)), [3000] * 5)

        mc = MultiCandle([candle1, candle2])
        market = MarketData(mc)

        # 처음: BTC만 유효
        prices = market.get_current_all()
        assert "BTC/USDT" in prices
        # ETH는 NaN이므로 제외되어야 함 (get_current_all의 구현에 따라)

        # 중간으로 이동 (timestamp 6000)
        for _ in range(5):
            market.step()

        prices = market.get_current_all()
        assert "BTC/USDT" in prices
        assert "ETH/USDT" in prices


class TestMarketDataEdgeCases:
    """엣지 케이스 테스트"""

    def test_single_candle(self):
        """단일 Candle"""
        candle = make_candle("BTC/USDT", [1000], [50000])

        mc = MultiCandle([candle])
        market = MarketData(mc)

        assert market.get_current_timestamp() == 1000
        assert market.step() is False
        assert market.is_finished() is True

    def test_offset_at_boundary(self):
        """offset이 경계에 있는 경우"""
        candle = make_candle("BTC/USDT", [1000, 2000, 3000], [50000, 51000, 52000])

        mc = MultiCandle([candle])

        # 마지막 인덱스로 시작
        market = MarketData(mc, start_offset=2)
        assert market.get_current_timestamp() == 3000
        assert market.step() is False
        assert market.is_finished() is True

    def test_get_cursor_idx(self):
        """cursor_idx 접근"""
        candle = make_candle("BTC/USDT", [1000, 2000, 3000], [50000, 51000, 52000])

        mc = MultiCandle([candle])
        market = MarketData(mc)

        assert market.get_cursor_idx() == 0
        market.step()
        assert market.get_cursor_idx() == 1
