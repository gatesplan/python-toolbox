"""IndexMapper 테스트"""

import pytest
import numpy as np
from financial_assets.multicandle.Core.IndexMapper.IndexMapper import IndexMapper


class TestBuildSymbolMapping:
    """symbol 매핑 생성 테스트"""

    def test_build_symbol_mapping_normal(self):
        """정상 케이스: 심볼 리스트 → 매핑 생성"""
        symbols = ["BTC/USDT", "ETH/USDT", "XRP/USDT"]

        symbol_to_idx, idx_to_symbol = IndexMapper.build_symbol_mapping(symbols)

        # symbol_to_idx 검증
        assert symbol_to_idx["BTC/USDT"] == 0
        assert symbol_to_idx["ETH/USDT"] == 1
        assert symbol_to_idx["XRP/USDT"] == 2
        assert len(symbol_to_idx) == 3

        # idx_to_symbol 검증
        assert idx_to_symbol[0] == "BTC/USDT"
        assert idx_to_symbol[1] == "ETH/USDT"
        assert idx_to_symbol[2] == "XRP/USDT"
        assert len(idx_to_symbol) == 3

    def test_build_symbol_mapping_single(self):
        """단일 심볼"""
        symbols = ["BTC/USDT"]

        symbol_to_idx, idx_to_symbol = IndexMapper.build_symbol_mapping(symbols)

        assert symbol_to_idx["BTC/USDT"] == 0
        assert idx_to_symbol[0] == "BTC/USDT"

    def test_build_symbol_mapping_bidirectional_consistency(self):
        """양방향 매핑 일치성 검증"""
        symbols = ["BTC/USDT", "ETH/USDT", "XRP/USDT"]

        symbol_to_idx, idx_to_symbol = IndexMapper.build_symbol_mapping(symbols)

        # 양방향 일치성
        for idx, symbol in enumerate(symbols):
            assert symbol_to_idx[symbol] == idx
            assert idx_to_symbol[idx] == symbol

    def test_build_symbol_mapping_empty_list(self):
        """빈 리스트 예외"""
        symbols = []

        with pytest.raises(ValueError, match="비어있"):
            IndexMapper.build_symbol_mapping(symbols)

    def test_build_symbol_mapping_duplicates(self):
        """중복 심볼 예외"""
        symbols = ["BTC/USDT", "ETH/USDT", "BTC/USDT"]

        with pytest.raises(ValueError, match="중복"):
            IndexMapper.build_symbol_mapping(symbols)


class TestBuildTimestampMapping:
    """timestamp 매핑 생성 테스트"""

    def test_build_timestamp_mapping_normal(self):
        """정상 케이스: 타임스탬프 배열 → 매핑 생성"""
        timestamps = np.array([1609459200, 1609459260, 1609459320])

        timestamp_to_idx, idx_to_timestamp = IndexMapper.build_timestamp_mapping(timestamps)

        # timestamp_to_idx 검증
        assert timestamp_to_idx[1609459200] == 0
        assert timestamp_to_idx[1609459260] == 1
        assert timestamp_to_idx[1609459320] == 2
        assert len(timestamp_to_idx) == 3

        # idx_to_timestamp 검증
        assert idx_to_timestamp[0] == 1609459200
        assert idx_to_timestamp[1] == 1609459260
        assert idx_to_timestamp[2] == 1609459320
        assert len(idx_to_timestamp) == 3

    def test_build_timestamp_mapping_single(self):
        """단일 타임스탬프"""
        timestamps = np.array([1609459200])

        timestamp_to_idx, idx_to_timestamp = IndexMapper.build_timestamp_mapping(timestamps)

        assert timestamp_to_idx[1609459200] == 0
        assert idx_to_timestamp[0] == 1609459200

    def test_build_timestamp_mapping_bidirectional_consistency(self):
        """양방향 매핑 일치성 검증"""
        timestamps = np.array([1609459200, 1609459260, 1609459320, 1609459380])

        timestamp_to_idx, idx_to_timestamp = IndexMapper.build_timestamp_mapping(timestamps)

        # 양방향 일치성
        for idx, ts in enumerate(timestamps):
            assert timestamp_to_idx[int(ts)] == idx
            assert idx_to_timestamp[idx] == ts

    def test_build_timestamp_mapping_empty_array(self):
        """빈 배열 예외"""
        timestamps = np.array([])

        with pytest.raises(ValueError, match="비어있"):
            IndexMapper.build_timestamp_mapping(timestamps)

    def test_build_timestamp_mapping_duplicates(self):
        """중복 타임스탬프 예외"""
        timestamps = np.array([1609459200, 1609459260, 1609459200])

        with pytest.raises(ValueError, match="중복"):
            IndexMapper.build_timestamp_mapping(timestamps)

    def test_build_timestamp_mapping_preserves_array_type(self):
        """idx_to_timestamp가 numpy array임을 보장"""
        timestamps = np.array([1609459200, 1609459260, 1609459320])

        timestamp_to_idx, idx_to_timestamp = IndexMapper.build_timestamp_mapping(timestamps)

        assert isinstance(idx_to_timestamp, np.ndarray)
        assert idx_to_timestamp.dtype == timestamps.dtype
