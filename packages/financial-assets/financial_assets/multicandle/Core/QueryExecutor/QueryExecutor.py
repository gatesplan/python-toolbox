"""QueryExecutor: 텐서 슬라이싱을 통한 조회 로직"""

import numpy as np
from typing import Union, List
from simple_logger import func_logging
from ....price import Price


class QueryExecutor:
    """텐서 슬라이싱을 통한 조회 로직을 수행하는 정적 유틸리티 클래스"""

    @staticmethod
    @func_logging(log_params=True)
    def get_snapshot_data(
        tensor: np.ndarray,
        timestamp_idx: int,
        symbols: list[str],
        exchange: str,
        timestamp: int,
        as_price: bool
    ) -> Union[np.ndarray, dict[str, Price]]:
        """
        특정 시점의 모든 종목 스냅샷 조회

        Args:
            tensor: (n_symbols, n_timestamps, 5) 3D 텐서
            timestamp_idx: 조회할 타임스탬프의 인덱스
            symbols: 종목 리스트 (순서 중요)
            exchange: 거래소명
            timestamp: 조회할 타임스탬프 (초 단위)
            as_price: True면 Price 객체 dict 반환

        Returns:
            as_price=False: np.ndarray, shape (n_symbols, 5)
            as_price=True: dict[str, Price] (NaN 제외)
        """
        # 텐서 슬라이싱: 특정 시점의 모든 종목
        snapshot = tensor[:, timestamp_idx, :]

        if not as_price:
            return snapshot

        # Price 객체 dict 생성
        result = {}
        for symbol_idx, symbol in enumerate(symbols):
            row = snapshot[symbol_idx]

            # NaN 필터링 (open 값으로 확인)
            if np.isnan(row[0]):
                continue

            result[symbol] = Price(
                exchange=exchange,
                market=symbol,
                t=timestamp,
                o=float(row[0]),
                h=float(row[1]),
                l=float(row[2]),
                c=float(row[3]),
                v=float(row[4])
            )

        return result

    @staticmethod
    @func_logging(log_params=True)
    def get_symbol_range_data(
        tensor: np.ndarray,
        symbol_idx: int,
        start_idx: int,
        end_idx: int,
        symbol: str,
        exchange: str,
        timestamps: np.ndarray,
        as_price: bool
    ) -> Union[np.ndarray, List[Price]]:
        """
        특정 종목의 시간 범위 데이터 조회

        Args:
            tensor: (n_symbols, n_timestamps, 5) 3D 텐서
            symbol_idx: 조회할 종목의 인덱스
            start_idx: 시작 타임스탬프 인덱스 (포함)
            end_idx: 종료 타임스탬프 인덱스 (미포함)
            symbol: 종목명
            exchange: 거래소명
            timestamps: 타임스탬프 배열
            as_price: True면 Price 객체 리스트 반환

        Returns:
            as_price=False: np.ndarray, shape (n_times, 5)
            as_price=True: List[Price] (NaN 제외)
        """
        # 텐서 슬라이싱: 특정 종목의 시간 범위
        range_data = tensor[symbol_idx, start_idx:end_idx, :]

        if not as_price:
            return range_data

        # Price 객체 리스트 생성
        result = []
        for time_idx in range(start_idx, end_idx):
            row = tensor[symbol_idx, time_idx, :]

            # NaN 필터링
            if np.isnan(row[0]):
                continue

            result.append(Price(
                exchange=exchange,
                market=symbol,
                t=int(timestamps[time_idx]),
                o=float(row[0]),
                h=float(row[1]),
                l=float(row[2]),
                c=float(row[3]),
                v=float(row[4])
            ))

        return result

    @staticmethod
    @func_logging(log_params=True)
    def get_range_data(
        tensor: np.ndarray,
        start_idx: int,
        end_idx: int
    ) -> np.ndarray:
        """
        시간 범위 내 모든 종목 데이터 조회

        Args:
            tensor: (n_symbols, n_timestamps, 5) 3D 텐서
            start_idx: 시작 타임스탬프 인덱스 (포함)
            end_idx: 종료 타임스탬프 인덱스 (미포함)

        Returns:
            np.ndarray, shape (n_symbols, n_times, 5)
        """
        # 텐서 슬라이싱: 시간 범위의 모든 종목
        return tensor[:, start_idx:end_idx, :]
