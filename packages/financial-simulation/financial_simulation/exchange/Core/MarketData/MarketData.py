"""MarketData: MultiCandle 기반 시뮬레이션 시장 데이터 관리"""

import random
from typing import Optional
from financial_assets.price import Price
from financial_assets.multicandle import MultiCandle
from simple_logger import init_logging, logger


class MarketData:
    """
    MultiCandle 위에 커서 관리 레이어를 추가한 시뮬레이션용 시장 데이터 관리자
    """

    @init_logging(level="INFO")
    def __init__(
        self,
        multicandle: MultiCandle,
        start_offset: int = 0,
        random_offset: bool = False,
    ) -> None:
        """
        Args:
            multicandle: MultiCandle 인스턴스
            start_offset: 시작 오프셋 (인덱스)
            random_offset: 랜덤 오프셋 추가 여부
        """
        self._multicandle = multicandle
        self._start_offset = start_offset
        self._random_offset = random_offset

        # timestamps 가져오기
        self._timestamps = multicandle._timestamps
        self._n_timestamps = len(self._timestamps)

        logger.info(
            f"MarketData 초기화: n_timestamps={self._n_timestamps}, "
            f"start_offset={start_offset}, random_offset={random_offset}"
        )

        # 시작 커서 계산
        self._start_idx = self._calculate_start_idx()
        self._cursor_idx = self._start_idx

        logger.info(f"MarketData 초기화 완료: start_idx={self._start_idx}")

    def _calculate_start_idx(self) -> int:
        """시작 인덱스 계산 (offset + random)"""
        start = self._start_offset

        if self._random_offset:
            # 남은 길이의 절반 범위 내에서 랜덤
            remaining = self._n_timestamps - start
            if remaining > 1:
                max_random = remaining // 2
                random_offset = random.randint(0, max_random)
                start += random_offset
                logger.debug(f"랜덤 오프셋 적용: {random_offset}")

        # 범위 체크
        if start >= self._n_timestamps:
            start = self._n_timestamps - 1

        return start

    def reset(self, override: bool = False) -> None:
        """
        커서 리셋

        Args:
            override: True면 새로운 랜덤 시작점 생성 (random_offset=True인 경우)
        """
        if override and self._random_offset:
            logger.info("새로운 랜덤 시작 인덱스 생성")
            self._start_idx = self._calculate_start_idx()

        self._cursor_idx = self._start_idx
        logger.info(f"커서 리셋 완료: cursor_idx={self._cursor_idx}")

    def step(self) -> bool:
        """
        다음 타임스탬프로 이동

        Returns:
            bool: 이동 성공 시 True, 끝에 도달했으면 False
        """
        if self._cursor_idx >= self._n_timestamps - 1:
            logger.debug("데이터 끝에 도달")
            return False

        self._cursor_idx += 1
        logger.debug(f"커서 이동: {self._cursor_idx}")
        return True

    def get_current(self, symbol: str) -> Price:
        """
        특정 심볼의 현재 커서 위치 가격 조회

        Args:
            symbol: 심볼 (예: "BTC/USDT")

        Returns:
            Price: 가격 객체

        Raises:
            KeyError: 심볼이 존재하지 않거나 해당 시점에 데이터가 없는 경우
        """
        current_timestamp = int(self._timestamps[self._cursor_idx])
        snapshot = self._multicandle.get_snapshot(current_timestamp, as_price=True)

        if symbol not in snapshot:
            raise KeyError(f"Symbol {symbol} not found at timestamp {current_timestamp}")

        return snapshot[symbol]

    def get_current_all(self) -> dict[str, Price]:
        """
        현재 커서 위치의 모든 유효한 심볼 가격 조회

        Returns:
            dict[str, Price]: 심볼별 가격 딕셔너리
        """
        current_timestamp = int(self._timestamps[self._cursor_idx])
        return self._multicandle.get_snapshot(current_timestamp, as_price=True)

    def get_current_timestamp(self) -> int:
        """
        현재 커서 위치의 타임스탬프 조회

        Returns:
            int: 타임스탬프 (초 단위)
        """
        return int(self._timestamps[self._cursor_idx])

    def get_symbols(self) -> list[str]:
        """
        관리 중인 모든 심볼 리스트

        Returns:
            list[str]: 심볼 리스트
        """
        return self._multicandle._symbols.copy()

    def get_cursor_idx(self) -> int:
        """
        현재 커서 인덱스 조회

        Returns:
            int: 커서 인덱스
        """
        return self._cursor_idx

    def is_finished(self) -> bool:
        """
        시뮬레이션 종료 여부

        Returns:
            bool: 커서가 마지막 위치에 도달했으면 True
        """
        return self._cursor_idx >= self._n_timestamps - 1

    def get_progress(self) -> float:
        """
        시뮬레이션 진행률 (0.0 ~ 1.0)

        Returns:
            float: 진행률
        """
        if self._n_timestamps <= 1:
            return 1.0
        return self._cursor_idx / (self._n_timestamps - 1)

    def __repr__(self) -> str:
        return (
            f"MarketData(symbols={len(self._multicandle._symbols)}, "
            f"cursor_idx={self._cursor_idx}/{self._n_timestamps}, "
            f"progress={self.get_progress():.2%})"
        )

    def get_candles(
        self,
        symbol: str,
        start_ts: int = None,
        end_ts: int = None,
        limit: int = None
    ):
        """과거 캔들 데이터 조회 (MultiCandle의 고정 timeframe 사용)

        Args:
            symbol: 심볼 (예: "BTC/USDT")
            start_ts: 시작 타임스탬프 (None이면 처음부터)
            end_ts: 종료 타임스탬프 (None이면 현재 커서까지)
            limit: 최대 개수 (None이면 전체)

        Returns:
            pd.DataFrame: 캔들 데이터

        Raises:
            KeyError: 심볼이 존재하지 않음
        """
        import pandas as pd

        # 기본값 설정
        if start_ts is None:
            start_ts = int(self._timestamps[0])
        if end_ts is None:
            # 현재 커서를 포함하려면 다음 타임스탬프 사용 (exclusive range이므로)
            if self._cursor_idx < self._n_timestamps - 1:
                end_ts = int(self._timestamps[self._cursor_idx + 1])
            else:
                # 마지막 커서인 경우, 마지막 타임스탬프 + 1 사용
                end_ts = int(self._timestamps[self._cursor_idx]) + 1

        # MultiCandle에서 Price 리스트 조회
        prices = self._multicandle.get_symbol_range(
            symbol,
            start_ts,
            end_ts,
            as_price=True
        )

        # DataFrame 변환
        df = pd.DataFrame([
            {
                'timestamp': p.t,
                'open': p.o,
                'high': p.h,
                'low': p.l,
                'close': p.c,
                'volume': p.v
            }
            for p in prices
        ])

        # limit 적용
        if limit is not None and len(df) > limit:
            df = df.tail(limit).reset_index(drop=True)

        return df
