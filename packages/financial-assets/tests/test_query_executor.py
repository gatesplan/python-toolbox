"""QueryExecutor 테스트"""

import pytest
import numpy as np
from financial_assets.price import Price
from financial_assets.multicandle.Core.QueryExecutor.QueryExecutor import QueryExecutor


class TestGetSnapshotData:
    """시점 기반 조회 테스트"""

    def setup_method(self):
        """테스트용 텐서 및 메타데이터 준비"""
        # 2 종목, 3 시점, OHLCV
        self.tensor = np.array([
            # BTC/USDT
            [
                [29000.0, 29100.0, 28900.0, 29050.0, 100.0],  # ts=0
                [29100.0, 29200.0, 29000.0, 29150.0, 110.0],  # ts=1
                [29200.0, 29300.0, 29100.0, 29250.0, 120.0],  # ts=2
            ],
            # ETH/USDT
            [
                [730.0, 740.0, 725.0, 735.0, 1000.0],
                [735.0, 745.0, 730.0, 740.0, 1100.0],
                [740.0, 750.0, 735.0, 745.0, 1200.0],
            ]
        ])
        self.symbols = ["BTC/USDT", "ETH/USDT"]
        self.timestamps = np.array([1609459200, 1609459260, 1609459320])
        self.exchange = "binance"

    def test_get_snapshot_data_as_array(self):
        """시점 조회 - numpy array 반환"""
        result = QueryExecutor.get_snapshot_data(
            self.tensor,
            timestamp_idx=0,
            symbols=self.symbols,
            exchange=self.exchange,
            timestamp=self.timestamps[0],
            as_price=False
        )

        # shape 검증
        assert result.shape == (2, 5)

        # 내용 검증
        assert result[0, 0] == 29000.0  # BTC open
        assert result[0, 3] == 29050.0  # BTC close
        assert result[1, 0] == 730.0    # ETH open
        assert result[1, 3] == 735.0    # ETH close

    def test_get_snapshot_data_as_price(self):
        """시점 조회 - Price 객체 dict 반환"""
        result = QueryExecutor.get_snapshot_data(
            self.tensor,
            timestamp_idx=1,
            symbols=self.symbols,
            exchange=self.exchange,
            timestamp=self.timestamps[1],
            as_price=True
        )

        # dict 구조 검증
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "BTC/USDT" in result
        assert "ETH/USDT" in result

        # Price 객체 검증
        btc_price = result["BTC/USDT"]
        assert isinstance(btc_price, Price)
        assert btc_price.exchange == "binance"
        assert btc_price.market == "BTC/USDT"
        assert btc_price.t == 1609459260
        assert btc_price.o == 29100.0
        assert btc_price.h == 29200.0
        assert btc_price.l == 29000.0
        assert btc_price.c == 29150.0
        assert btc_price.v == 110.0

    def test_get_snapshot_data_with_nan_filtering(self):
        """NaN 필터링 - as_price=True 시 누락 종목 제외"""
        # NaN 포함 텐서
        tensor_with_nan = self.tensor.copy()
        tensor_with_nan[1, 0, :] = np.nan  # ETH의 첫 시점 NaN

        result = QueryExecutor.get_snapshot_data(
            tensor_with_nan,
            timestamp_idx=0,
            symbols=self.symbols,
            exchange=self.exchange,
            timestamp=self.timestamps[0],
            as_price=True
        )

        # BTC만 반환, ETH는 제외
        assert len(result) == 1
        assert "BTC/USDT" in result
        assert "ETH/USDT" not in result

    def test_get_snapshot_data_all_nan(self):
        """모든 종목이 NaN인 경우 - 빈 dict 반환"""
        tensor_all_nan = np.full((2, 3, 5), np.nan)

        result = QueryExecutor.get_snapshot_data(
            tensor_all_nan,
            timestamp_idx=0,
            symbols=self.symbols,
            exchange=self.exchange,
            timestamp=self.timestamps[0],
            as_price=True
        )

        assert isinstance(result, dict)
        assert len(result) == 0


class TestGetSymbolRangeData:
    """종목 기반 범위 조회 테스트"""

    def setup_method(self):
        """테스트용 텐서 준비"""
        self.tensor = np.array([
            # BTC/USDT
            [
                [29000.0, 29100.0, 28900.0, 29050.0, 100.0],
                [29100.0, 29200.0, 29000.0, 29150.0, 110.0],
                [29200.0, 29300.0, 29100.0, 29250.0, 120.0],
            ]
        ])
        self.timestamps = np.array([1609459200, 1609459260, 1609459320])
        self.exchange = "binance"

    def test_get_symbol_range_data_as_array(self):
        """종목 범위 조회 - numpy array 반환"""
        result = QueryExecutor.get_symbol_range_data(
            self.tensor,
            symbol_idx=0,
            start_idx=0,
            end_idx=2,
            symbol="BTC/USDT",
            exchange=self.exchange,
            timestamps=self.timestamps,
            as_price=False
        )

        # shape 검증
        assert result.shape == (2, 5)

        # 내용 검증
        assert result[0, 0] == 29000.0  # 첫 캔들 open
        assert result[1, 3] == 29150.0  # 둘째 캔들 close

    def test_get_symbol_range_data_as_price(self):
        """종목 범위 조회 - Price 객체 리스트 반환"""
        result = QueryExecutor.get_symbol_range_data(
            self.tensor,
            symbol_idx=0,
            start_idx=1,
            end_idx=3,
            symbol="BTC/USDT",
            exchange=self.exchange,
            timestamps=self.timestamps,
            as_price=True
        )

        # 리스트 검증
        assert isinstance(result, list)
        assert len(result) == 2

        # Price 객체 검증
        price1 = result[0]
        assert isinstance(price1, Price)
        assert price1.t == 1609459260
        assert price1.o == 29100.0

        price2 = result[1]
        assert price2.t == 1609459320
        assert price2.c == 29250.0

    def test_get_symbol_range_data_with_nan_filtering(self):
        """NaN 필터링 - as_price=True 시 누락 시점 제외"""
        tensor_with_nan = self.tensor.copy()
        tensor_with_nan[0, 1, :] = np.nan  # 중간 시점 NaN

        result = QueryExecutor.get_symbol_range_data(
            tensor_with_nan,
            symbol_idx=0,
            start_idx=0,
            end_idx=3,
            symbol="BTC/USDT",
            exchange=self.exchange,
            timestamps=self.timestamps,
            as_price=True
        )

        # NaN 제외하고 2개만 반환
        assert len(result) == 2
        assert result[0].t == 1609459200
        assert result[1].t == 1609459320  # 중간(1609459260) 제외


class TestGetRangeData:
    """범위 기반 조회 테스트"""

    def setup_method(self):
        """테스트용 텐서 준비"""
        self.tensor = np.array([
            # BTC
            [
                [29000.0, 29100.0, 28900.0, 29050.0, 100.0],
                [29100.0, 29200.0, 29000.0, 29150.0, 110.0],
                [29200.0, 29300.0, 29100.0, 29250.0, 120.0],
            ],
            # ETH
            [
                [730.0, 740.0, 725.0, 735.0, 1000.0],
                [735.0, 745.0, 730.0, 740.0, 1100.0],
                [740.0, 750.0, 735.0, 745.0, 1200.0],
            ]
        ])

    def test_get_range_data(self):
        """범위 조회 - 3D 텐서 슬라이스 반환"""
        result = QueryExecutor.get_range_data(
            self.tensor,
            start_idx=0,
            end_idx=2
        )

        # shape 검증
        assert result.shape == (2, 2, 5)  # 2 종목, 2 시점, OHLCV

        # 내용 검증
        assert result[0, 0, 0] == 29000.0  # BTC 첫 캔들 open
        assert result[1, 1, 3] == 740.0    # ETH 둘째 캔들 close

    def test_get_range_data_full(self):
        """전체 범위 조회"""
        result = QueryExecutor.get_range_data(
            self.tensor,
            start_idx=0,
            end_idx=3
        )

        assert result.shape == (2, 3, 5)
        # 원본과 동일
        np.testing.assert_array_equal(result, self.tensor)

    def test_get_range_data_single_timestamp(self):
        """단일 시점 범위"""
        result = QueryExecutor.get_range_data(
            self.tensor,
            start_idx=1,
            end_idx=2
        )

        assert result.shape == (2, 1, 5)
        assert result[0, 0, 0] == 29100.0  # BTC 둘째 캔들
