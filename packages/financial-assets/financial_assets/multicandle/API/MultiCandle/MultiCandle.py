"""MultiCandle: 여러 종목의 캔들 데이터 조회 인터페이스"""

import numpy as np
from typing import List, Union, Iterator
from simple_logger import init_logging, func_logging

from ...Core.TensorBuilder import TensorBuilder
from ...Core.IndexMapper import IndexMapper
from ...Core.QueryExecutor import QueryExecutor


class MultiCandle:
    """
    여러 종목의 캔들 데이터를 통합 관리하고 효율적으로 조회하는 컨트롤러 클래스

    시뮬레이션 및 분석용 고성능 조회 인터페이스 제공
    """

    @init_logging
    def __init__(self, candles: List):
        """
        여러 Candle 객체로 MultiCandle 초기화

        Args:
            candles: Candle 객체 리스트 (동일 exchange, timeframe 가정)

        Raises:
            ValueError: candles가 비어있는 경우
            ValueError: candles의 exchange가 다른 경우
        """
        # TensorBuilder로 텐서 구축
        self._tensor, self._symbols, self._timestamps = TensorBuilder.build(candles)

        # IndexMapper로 매핑 생성
        self._symbol_to_idx, _ = IndexMapper.build_symbol_mapping(self._symbols)
        self._timestamp_to_idx, _ = IndexMapper.build_timestamp_mapping(self._timestamps)

        # exchange 저장
        self._exchange = candles[0].address.exchange

    @func_logging(log_params=True)
    def get_snapshot(self, timestamp: int, as_price: bool = False) -> Union[np.ndarray, dict]:
        """
        특정 시점의 모든 종목 스냅샷 조회

        Args:
            timestamp: 조회할 타임스탬프 (초 단위)
            as_price: True면 Price 객체 dict 반환, False면 numpy array 반환

        Returns:
            as_price=False: np.ndarray, shape (n_symbols, 5)
            as_price=True: dict[str, Price]

        Raises:
            KeyError: timestamp가 존재하지 않는 경우
        """
        timestamp_idx = self._timestamp_to_idx[timestamp]

        return QueryExecutor.get_snapshot_data(
            self._tensor,
            timestamp_idx,
            self._symbols,
            self._exchange,
            timestamp,
            as_price
        )

    @func_logging(log_params=True)
    def get_symbol_range(
        self,
        symbol: str,
        start_ts: int,
        end_ts: int,
        as_price: bool = False
    ) -> Union[np.ndarray, list]:
        """
        특정 종목의 시간 범위 데이터 조회

        Args:
            symbol: 종목명 (예: "BTC/USDT")
            start_ts: 시작 타임스탬프 (포함)
            end_ts: 종료 타임스탬프 (미포함)
            as_price: True면 Price 객체 리스트 반환

        Returns:
            as_price=False: np.ndarray, shape (n_times, 5)
            as_price=True: List[Price]

        Raises:
            KeyError: symbol이 존재하지 않는 경우
            KeyError: start_ts 또는 end_ts가 범위 밖인 경우
        """
        symbol_idx = self._symbol_to_idx[symbol]
        start_idx = self._timestamp_to_idx[start_ts]
        end_idx = self._timestamp_to_idx[end_ts]

        return QueryExecutor.get_symbol_range_data(
            self._tensor,
            symbol_idx,
            start_idx,
            end_idx,
            symbol,
            self._exchange,
            self._timestamps,
            as_price
        )

    @func_logging(log_params=True)
    def get_range(self, start_ts: int, end_ts: int, as_price: bool = False) -> np.ndarray:
        """
        시간 범위 내 모든 종목 데이터 조회

        Args:
            start_ts: 시작 타임스탬프 (포함)
            end_ts: 종료 타임스탬프 (미포함)
            as_price: 현재 지원 안 됨

        Returns:
            np.ndarray, shape (n_symbols, n_times, 5)

        Raises:
            KeyError: start_ts 또는 end_ts가 범위 밖인 경우
        """
        start_idx = self._timestamp_to_idx[start_ts]
        end_idx = self._timestamp_to_idx[end_ts]

        return QueryExecutor.get_range_data(
            self._tensor,
            start_idx,
            end_idx
        )

    @func_logging(log_params=True)
    def iter_time(
        self,
        start_ts: int,
        end_ts: int,
        as_price: bool = False
    ) -> Iterator[tuple[int, Union[np.ndarray, dict]]]:
        """
        시간 순회 반복자

        Args:
            start_ts: 시작 타임스탬프 (포함)
            end_ts: 종료 타임스탬프 (미포함)
            as_price: True면 Price dict 반환, False면 numpy array 반환

        Yields:
            tuple[int, np.ndarray | dict[str, Price]]
                - timestamp: 현재 타임스탬프
                - data: 해당 시점의 스냅샷

        Raises:
            KeyError: start_ts 또는 end_ts가 범위 밖인 경우
        """
        start_idx = self._timestamp_to_idx[start_ts]
        end_idx = self._timestamp_to_idx[end_ts]

        for idx in range(start_idx, end_idx):
            timestamp = int(self._timestamps[idx])
            snapshot = self.get_snapshot(timestamp, as_price)
            yield (timestamp, snapshot)

    @func_logging(log_params=True)
    def symbol_to_idx(self, symbol: str) -> int:
        """
        종목명을 텐서 인덱스로 변환

        Args:
            symbol: 종목명 (예: "BTC/USDT")

        Returns:
            int: 텐서의 axis 0 인덱스

        Raises:
            KeyError: symbol이 존재하지 않는 경우
        """
        return self._symbol_to_idx[symbol]

    @func_logging(log_params=True)
    def idx_to_symbol(self, idx: int) -> str:
        """
        텐서 인덱스를 종목명으로 변환

        Args:
            idx: 텐서의 axis 0 인덱스

        Returns:
            str: 종목명

        Raises:
            IndexError: idx가 범위 밖인 경우
        """
        return self._symbols[idx]

    @func_logging(log_params=True)
    def timestamp_to_idx(self, timestamp: int) -> int:
        """
        타임스탬프를 텐서 인덱스로 변환

        Args:
            timestamp: 타임스탬프 (초 단위)

        Returns:
            int: 텐서의 axis 1 인덱스

        Raises:
            KeyError: timestamp가 존재하지 않는 경우
        """
        return self._timestamp_to_idx[timestamp]

    @func_logging(log_params=True)
    def idx_to_timestamp(self, idx: int) -> int:
        """
        텐서 인덱스를 타임스탬프로 변환

        Args:
            idx: 텐서의 axis 1 인덱스

        Returns:
            int: 타임스탬프 (초 단위)

        Raises:
            IndexError: idx가 범위 밖인 경우
        """
        return int(self._timestamps[idx])
