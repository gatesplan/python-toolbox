"""MultiCandle 테스트"""

import pytest
import pandas as pd
import numpy as np
from financial_assets.candle import Candle
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price
from financial_assets.multicandle import MultiCandle


class TestMultiCandleInit:
    """MultiCandle 초기화 테스트"""

    def test_init_with_two_candles(self):
        """2개 Candle로 초기화"""
        addr1 = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        addr2 = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

        df1 = pd.DataFrame({
            'timestamp': [1609459200, 1609459260],
            'open': [29000.0, 29100.0],
            'high': [29100.0, 29200.0],
            'low': [28900.0, 29000.0],
            'close': [29050.0, 29150.0],
            'volume': [100.0, 110.0]
        })

        df2 = pd.DataFrame({
            'timestamp': [1609459200, 1609459260],
            'open': [730.0, 735.0],
            'high': [740.0, 745.0],
            'low': [725.0, 730.0],
            'close': [735.0, 740.0],
            'volume': [1000.0, 1100.0]
        })

        candle1 = Candle(addr1, df1)
        candle2 = Candle(addr2, df2)

        mc = MultiCandle([candle1, candle2])

        # 내부 상태 확인
        assert mc._tensor.shape == (2, 2, 5)
        assert len(mc._symbols) == 2
        assert len(mc._timestamps) == 2
        assert mc._exchange == "binance"


class TestGetSnapshot:
    """시점 기반 조회 테스트"""

    def setup_method(self):
        """테스트용 MultiCandle 생성"""
        addr1 = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        addr2 = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

        df1 = pd.DataFrame({
            'timestamp': [1609459200, 1609459260, 1609459320],
            'open': [29000.0, 29100.0, 29200.0],
            'high': [29100.0, 29200.0, 29300.0],
            'low': [28900.0, 29000.0, 29100.0],
            'close': [29050.0, 29150.0, 29250.0],
            'volume': [100.0, 110.0, 120.0]
        })

        df2 = pd.DataFrame({
            'timestamp': [1609459200, 1609459260, 1609459320],
            'open': [730.0, 735.0, 740.0],
            'high': [740.0, 745.0, 750.0],
            'low': [725.0, 730.0, 735.0],
            'close': [735.0, 740.0, 745.0],
            'volume': [1000.0, 1100.0, 1200.0]
        })

        candle1 = Candle(addr1, df1)
        candle2 = Candle(addr2, df2)

        self.mc = MultiCandle([candle1, candle2])

    def test_get_snapshot_as_array(self):
        """시점 조회 - numpy array"""
        result = self.mc.get_snapshot(1609459200, as_price=False)

        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 5)

    def test_get_snapshot_as_price(self):
        """시점 조회 - Price 객체 dict"""
        result = self.mc.get_snapshot(1609459260, as_price=True)

        assert isinstance(result, dict)
        assert "BTC/USDT" in result
        assert "ETH/USDT" in result

        btc_price = result["BTC/USDT"]
        assert isinstance(btc_price, Price)
        assert btc_price.t == 1609459260
        assert btc_price.c == 29150.0

    def test_get_snapshot_invalid_timestamp(self):
        """존재하지 않는 timestamp - KeyError"""
        with pytest.raises(KeyError):
            self.mc.get_snapshot(9999999999)


class TestGetSymbolRange:
    """종목 기반 범위 조회 테스트"""

    def setup_method(self):
        """테스트용 MultiCandle 생성"""
        addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        df = pd.DataFrame({
            'timestamp': [1609459200, 1609459260, 1609459320],
            'open': [29000.0, 29100.0, 29200.0],
            'high': [29100.0, 29200.0, 29300.0],
            'low': [28900.0, 29000.0, 29100.0],
            'close': [29050.0, 29150.0, 29250.0],
            'volume': [100.0, 110.0, 120.0]
        })
        candle = Candle(addr, df)
        self.mc = MultiCandle([candle])

    def test_get_symbol_range_as_array(self):
        """종목 범위 조회 - numpy array"""
        result = self.mc.get_symbol_range("BTC/USDT", 1609459200, 1609459320, as_price=False)

        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 5)

    def test_get_symbol_range_as_price(self):
        """종목 범위 조회 - Price 객체 리스트"""
        result = self.mc.get_symbol_range("BTC/USDT", 1609459200, 1609459320, as_price=True)

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], Price)

    def test_get_symbol_range_invalid_symbol(self):
        """존재하지 않는 종목 - KeyError"""
        with pytest.raises(KeyError):
            self.mc.get_symbol_range("XRP/USDT", 1609459200, 1609459320)


class TestGetRange:
    """범위 기반 조회 테스트"""

    def setup_method(self):
        """테스트용 MultiCandle 생성"""
        addr1 = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        addr2 = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

        df1 = pd.DataFrame({
            'timestamp': [1609459200, 1609459260, 1609459320],
            'open': [29000.0, 29100.0, 29200.0],
            'high': [29100.0, 29200.0, 29300.0],
            'low': [28900.0, 29000.0, 29100.0],
            'close': [29050.0, 29150.0, 29250.0],
            'volume': [100.0, 110.0, 120.0]
        })

        df2 = pd.DataFrame({
            'timestamp': [1609459200, 1609459260, 1609459320],
            'open': [730.0, 735.0, 740.0],
            'high': [740.0, 745.0, 750.0],
            'low': [725.0, 730.0, 735.0],
            'close': [735.0, 740.0, 745.0],
            'volume': [1000.0, 1100.0, 1200.0]
        })

        candle1 = Candle(addr1, df1)
        candle2 = Candle(addr2, df2)
        self.mc = MultiCandle([candle1, candle2])

    def test_get_range(self):
        """범위 조회 - 3D 텐서"""
        result = self.mc.get_range(1609459200, 1609459320)

        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 2, 5)


class TestIterTime:
    """시간 반복자 테스트"""

    def setup_method(self):
        """테스트용 MultiCandle 생성"""
        addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        df = pd.DataFrame({
            'timestamp': [1609459200, 1609459260, 1609459320],
            'open': [29000.0, 29100.0, 29200.0],
            'high': [29100.0, 29200.0, 29300.0],
            'low': [28900.0, 29000.0, 29100.0],
            'close': [29050.0, 29150.0, 29250.0],
            'volume': [100.0, 110.0, 120.0]
        })
        candle = Candle(addr, df)
        self.mc = MultiCandle([candle])

    def test_iter_time_as_array(self):
        """시간 반복자 - numpy array"""
        results = list(self.mc.iter_time(1609459200, 1609459320, as_price=False))

        assert len(results) == 2
        timestamp, data = results[0]
        assert timestamp == 1609459200
        assert isinstance(data, np.ndarray)

    def test_iter_time_as_price(self):
        """시간 반복자 - Price 객체 dict"""
        results = list(self.mc.iter_time(1609459200, 1609459320, as_price=True))

        assert len(results) == 2
        timestamp, data = results[1]
        assert timestamp == 1609459260
        assert isinstance(data, dict)
        assert "BTC/USDT" in data


class TestMappingUtilities:
    """매핑 유틸리티 테스트"""

    def setup_method(self):
        """테스트용 MultiCandle 생성"""
        addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        df = pd.DataFrame({
            'timestamp': [1609459200, 1609459260],
            'open': [29000.0, 29100.0],
            'high': [29100.0, 29200.0],
            'low': [28900.0, 29000.0],
            'close': [29050.0, 29150.0],
            'volume': [100.0, 110.0]
        })
        candle = Candle(addr, df)
        self.mc = MultiCandle([candle])

    def test_symbol_to_idx(self):
        """종목명 → 인덱스"""
        idx = self.mc.symbol_to_idx("BTC/USDT")
        assert idx == 0

    def test_idx_to_symbol(self):
        """인덱스 → 종목명"""
        symbol = self.mc.idx_to_symbol(0)
        assert symbol == "BTC/USDT"

    def test_timestamp_to_idx(self):
        """타임스탬프 → 인덱스"""
        idx = self.mc.timestamp_to_idx(1609459200)
        assert idx == 0

    def test_idx_to_timestamp(self):
        """인덱스 → 타임스탬프"""
        ts = self.mc.idx_to_timestamp(1)
        assert ts == 1609459260

    def test_symbol_to_idx_invalid(self):
        """존재하지 않는 종목 - KeyError"""
        with pytest.raises(KeyError):
            self.mc.symbol_to_idx("XRP/USDT")

    def test_timestamp_to_idx_invalid(self):
        """존재하지 않는 타임스탬프 - KeyError"""
        with pytest.raises(KeyError):
            self.mc.timestamp_to_idx(9999999999)
