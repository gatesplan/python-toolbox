"""TensorBuilder 테스트"""

import pytest
import pandas as pd
import numpy as np
from financial_assets.candle import Candle
from financial_assets.stock_address import StockAddress
from financial_assets.multicandle.Core.TensorBuilder.TensorBuilder import TensorBuilder


class TestBuildTensor:
    """텐서 구축 테스트"""

    def test_build_with_two_candles(self):
        """2개 Candle로 텐서 구축 - 정상 케이스"""
        # 테스트용 Candle 생성
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

        # 텐서 구축
        tensor, symbols, timestamps = TensorBuilder.build([candle1, candle2])

        # shape 검증
        assert tensor.shape == (2, 3, 5)  # (2 종목, 3 시점, OHLCV 5개)

        # symbols 검증
        assert len(symbols) == 2
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols

        # timestamps 검증
        assert len(timestamps) == 3
        assert timestamps[0] == 1609459200
        assert timestamps[1] == 1609459260
        assert timestamps[2] == 1609459320

        # dtype 검증
        assert tensor.dtype == np.float64

    def test_build_tensor_content(self):
        """텐서 내용 검증"""
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

        tensor, symbols, timestamps = TensorBuilder.build([candle])

        # BTC의 첫 번째 캔들 검증
        btc_idx = symbols.index("BTC/USDT")
        first_candle = tensor[btc_idx, 0, :]

        assert first_candle[0] == 29000.0  # open
        assert first_candle[1] == 29100.0  # high
        assert first_candle[2] == 28900.0  # low
        assert first_candle[3] == 29050.0  # close
        assert first_candle[4] == 100.0    # volume

        # BTC의 두 번째 캔들 검증
        second_candle = tensor[btc_idx, 1, :]
        assert second_candle[0] == 29100.0  # open
        assert second_candle[3] == 29150.0  # close

    def test_build_with_different_start_times(self):
        """시작 시점이 다른 Candle들 - 종목 정렬 검증"""
        # BTC는 나중에 시작
        addr_btc = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        addr_eth = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

        df_btc = pd.DataFrame({
            'timestamp': [1609459260, 1609459320],  # 나중 시작
            'open': [29000.0, 29100.0],
            'high': [29100.0, 29200.0],
            'low': [28900.0, 29000.0],
            'close': [29050.0, 29150.0],
            'volume': [100.0, 110.0]
        })

        df_eth = pd.DataFrame({
            'timestamp': [1609459200, 1609459260, 1609459320],  # 먼저 시작
            'open': [730.0, 735.0, 740.0],
            'high': [740.0, 745.0, 750.0],
            'low': [725.0, 730.0, 735.0],
            'close': [735.0, 740.0, 745.0],
            'volume': [1000.0, 1100.0, 1200.0]
        })

        candle_btc = Candle(addr_btc, df_btc)
        candle_eth = Candle(addr_eth, df_eth)

        tensor, symbols, timestamps = TensorBuilder.build([candle_btc, candle_eth])

        # ETH가 먼저 시작하므로 ETH가 0번 인덱스
        assert symbols[0] == "ETH/USDT"
        assert symbols[1] == "BTC/USDT"

        # timestamps는 합집합 (3개)
        assert len(timestamps) == 3
        assert timestamps[0] == 1609459200

        # BTC의 첫 시점은 NaN (데이터 없음)
        btc_idx = symbols.index("BTC/USDT")
        assert np.isnan(tensor[btc_idx, 0, 0])  # BTC의 첫 시점 open은 NaN

        # BTC의 두 번째 시점은 데이터 있음
        assert not np.isnan(tensor[btc_idx, 1, 0])

    def test_build_with_missing_timestamps(self):
        """중간 타임스탬프 누락 케이스 - NaN 처리 검증"""
        addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

        # timestamp가 불연속 (1609459260 누락)
        df = pd.DataFrame({
            'timestamp': [1609459200, 1609459320],
            'open': [29000.0, 29200.0],
            'high': [29100.0, 29300.0],
            'low': [28900.0, 29100.0],
            'close': [29050.0, 29250.0],
            'volume': [100.0, 120.0]
        })

        candle = Candle(addr, df)

        # 다른 종목은 연속 데이터
        addr2 = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
        df2 = pd.DataFrame({
            'timestamp': [1609459200, 1609459260, 1609459320],
            'open': [730.0, 735.0, 740.0],
            'high': [740.0, 745.0, 750.0],
            'low': [725.0, 730.0, 735.0],
            'close': [735.0, 740.0, 745.0],
            'volume': [1000.0, 1100.0, 1200.0]
        })
        candle2 = Candle(addr2, df2)

        tensor, symbols, timestamps = TensorBuilder.build([candle, candle2])

        # timestamps는 합집합 (3개)
        assert len(timestamps) == 3
        assert 1609459260 in timestamps

        # BTC의 중간 시점은 NaN
        btc_idx = symbols.index("BTC/USDT")
        ts_idx = list(timestamps).index(1609459260)
        assert np.isnan(tensor[btc_idx, ts_idx, 0])  # open이 NaN

    def test_build_empty_candles(self):
        """빈 Candle 리스트 예외"""
        with pytest.raises(ValueError, match="비어있"):
            TensorBuilder.build([])

    def test_build_different_exchanges(self):
        """exchange가 다른 Candle 예외"""
        addr1 = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        addr2 = StockAddress("candle", "upbit", "spot", "ETH", "USDT", "1m")

        df = pd.DataFrame({
            'timestamp': [1609459200],
            'open': [29000.0],
            'high': [29100.0],
            'low': [28900.0],
            'close': [29050.0],
            'volume': [100.0]
        })

        candle1 = Candle(addr1, df)
        candle2 = Candle(addr2, df)

        with pytest.raises(ValueError, match="exchange"):
            TensorBuilder.build([candle1, candle2])

    def test_build_single_candle(self):
        """단일 Candle"""
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

        tensor, symbols, timestamps = TensorBuilder.build([candle])

        assert tensor.shape == (1, 2, 5)
        assert len(symbols) == 1
        assert symbols[0] == "BTC/USDT"
