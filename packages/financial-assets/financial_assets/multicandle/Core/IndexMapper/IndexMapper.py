"""IndexMapper: symbol/timestamp와 텐서 인덱스 간 양방향 매핑 생성"""

import numpy as np
from simple_logger import func_logging


class IndexMapper:
    """symbol/timestamp와 텐서 인덱스 간 양방향 매핑을 생성하는 정적 유틸리티 클래스"""

    @staticmethod
    @func_logging(log_params=True)
    def build_symbol_mapping(symbols: list[str]) -> tuple[dict[str, int], list[str]]:
        """
        종목명과 인덱스 간 양방향 매핑 생성

        Args:
            symbols: 종목 리스트 (정렬된 상태)

        Returns:
            tuple[dict[str, int], list[str]]:
                - symbol_to_idx: 종목명 → 인덱스 매핑
                - idx_to_symbol: 인덱스 → 종목명 리스트

        Raises:
            ValueError: symbols가 비어있는 경우
            ValueError: symbols에 중복이 있는 경우
        """
        # 빈 리스트 검증
        if len(symbols) == 0:
            raise ValueError("symbols가 비어있습니다")

        # 중복 검증
        if len(symbols) != len(set(symbols)):
            raise ValueError("symbols에 중복이 있습니다")

        # symbol_to_idx 생성
        symbol_to_idx = {symbol: idx for idx, symbol in enumerate(symbols)}

        # idx_to_symbol (입력과 동일)
        idx_to_symbol = symbols

        return symbol_to_idx, idx_to_symbol

    @staticmethod
    @func_logging(log_params=True)
    def build_timestamp_mapping(
        timestamps: np.ndarray,
    ) -> tuple[dict[int, int], np.ndarray]:
        """
        타임스탬프와 인덱스 간 양방향 매핑 생성

        Args:
            timestamps: 타임스탬프 배열 (정렬된 상태, 초 단위)

        Returns:
            tuple[dict[int, int], np.ndarray]:
                - timestamp_to_idx: 타임스탬프 → 인덱스 매핑
                - idx_to_timestamp: 인덱스 → 타임스탬프 배열

        Raises:
            ValueError: timestamps가 비어있는 경우
            ValueError: timestamps에 중복이 있는 경우
        """
        # 빈 배열 검증
        if len(timestamps) == 0:
            raise ValueError("timestamps가 비어있습니다")

        # 중복 검증
        if len(timestamps) != len(np.unique(timestamps)):
            raise ValueError("timestamps에 중복이 있습니다")

        # timestamp_to_idx 생성
        timestamp_to_idx = {int(ts): idx for idx, ts in enumerate(timestamps)}

        # idx_to_timestamp (입력과 동일)
        idx_to_timestamp = timestamps

        return timestamp_to_idx, idx_to_timestamp
