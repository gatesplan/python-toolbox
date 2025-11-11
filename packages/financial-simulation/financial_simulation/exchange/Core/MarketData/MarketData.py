# 시장 데이터 및 커서 관리

from typing import Optional
import random
from financial_assets.price import Price
from simple_logger import init_logging, logger


class MarketData:
    # 심볼별 캔들 데이터를 보관하고, 현재 시점을 추적하며, 가격 조회 API를 제공

    @init_logging(level="INFO")
    def __init__(
        self,
        data: dict[str, list[Price]],
        availability_threshold: float = 0.8,
        offset: int = 0,
        random_additional_offset: bool = False,
    ) -> None:
        if not data:
            raise ValueError("Data cannot be empty")

        logger.info(
            f"MarketData 초기화: symbols={len(data)}, "
            f"threshold={availability_threshold}, offset={offset}, "
            f"random_offset={random_additional_offset}"
        )

        self._data = data
        self._availability_threshold = availability_threshold
        self._offset = offset
        self._random_additional_offset = random_additional_offset

        # 최대 길이 계산
        self._max_length = max(len(prices) for prices in data.values())
        logger.debug(f"최대 데이터 길이: {self._max_length}")

        # 데이터 정합성 검사
        self._validate_data()

        # 합리적 시작 커서 찾기
        self._base_start_cursor = self._find_valid_start_cursor()
        logger.info(f"기본 시작 커서: {self._base_start_cursor}")

        # 최종 시작 커서 계산 (base + offset + random)
        self._start_cursor = self._calculate_start_cursor()
        self._cursor = self._start_cursor

        logger.info(f"MarketData 초기화 완료: start_cursor={self._start_cursor}")

    def _validate_data(self) -> None:
        # 데이터 정합성 검사: 시간순 정렬 및 마지막 타임스탬프 일치 확인
        last_timestamps = {}

        for symbol, prices in self._data.items():
            if len(prices) == 0:
                continue

            # 시간순 정렬 확인
            for i in range(len(prices) - 1):
                if prices[i].t >= prices[i + 1].t:
                    raise ValueError(
                        f"Symbol {symbol}: data is not sorted in time order at index {i}"
                    )

            # 마지막 타임스탬프 저장
            last_timestamps[symbol] = prices[-1].t

        # 모든 심볼의 마지막 타임스탬프가 같은지 확인
        if len(set(last_timestamps.values())) > 1:
            raise ValueError(
                f"Last timestamps do not match across symbols: {last_timestamps}"
            )

        logger.debug("데이터 정합성 검사 통과")

    def _find_valid_start_cursor(self) -> int:
        # availability_threshold 이상인 첫 번째 인덱스 찾기
        # 각 심볼의 데이터는 뒤 끝이 정렬되어 있으므로 시작 오프셋을 고려
        total_symbols = len(self._data)

        for cursor in range(self._max_length):
            valid_count = 0
            for prices in self._data.values():
                # 각 심볼의 시작 인덱스 = max_length - len(prices)
                start_index = self._max_length - len(prices)
                if cursor >= start_index:
                    valid_count += 1

            availability = valid_count / total_symbols

            if availability >= self._availability_threshold:
                logger.debug(
                    f"합리적 시작점 발견: cursor={cursor}, availability={availability:.2f}"
                )
                return cursor

        raise ValueError(
            f"No valid start cursor found with threshold {self._availability_threshold}"
        )

    def _calculate_start_cursor(self) -> int:
        # 최종 시작 커서 계산 (base + offset + random)
        start = self._base_start_cursor + self._offset

        if self._random_additional_offset:
            remaining_length = self._max_length - start
            max_random_offset = remaining_length // 2
            if max_random_offset > 0:
                random_offset = random.randint(0, max_random_offset)
                start += random_offset
                logger.debug(f"랜덤 오프셋 적용: {random_offset}")

        return start

    def reset(self, override: bool = False) -> None:
        # 커서를 시작 위치로 리셋 (override=True면 새로운 랜덤 시작 커서 생성)
        if override and self._random_additional_offset:
            logger.info("새로운 랜덤 시작 커서 생성")
            self._start_cursor = self._calculate_start_cursor()

        self._cursor = self._start_cursor
        logger.info(f"커서 리셋 완료: cursor={self._cursor}")

    def step(self) -> bool:
        # 다음 틱으로 이동 (모든 심볼 동기화)
        if self._cursor >= self._max_length - 1:
            logger.debug("데이터 끝에 도달")
            return False

        self._cursor += 1
        logger.debug(f"커서 이동: {self._cursor}")
        return True

    def get_current(self, symbol: str) -> Optional[Price]:
        # 특정 심볼의 현재 커서 위치 가격 데이터 조회
        if symbol not in self._data:
            return None

        prices = self._data[symbol]
        # 각 심볼의 시작 인덱스 = max_length - len(prices)
        start_index = self._max_length - len(prices)

        if self._cursor < start_index:
            return None

        # 심볼 내부 인덱스 계산
        symbol_index = self._cursor - start_index
        return prices[symbol_index]

    def get_current_all(self) -> dict[str, Price]:
        # 현재 커서 위치에서 유효한 모든 심볼의 가격 데이터 조회
        result = {}
        for symbol in self._data:
            price = self.get_current(symbol)
            if price is not None:
                result[symbol] = price
        return result

    def get_current_timestamp(self, symbol: str) -> Optional[int]:
        # 특정 심볼의 현재 타임스탬프 조회
        price = self.get_current(symbol)
        return price.t if price is not None else None

    def get_symbols(self) -> list[str]:
        # 관리 중인 모든 심볼 리스트
        return list(self._data.keys())

    def get_cursor(self) -> int:
        # 현재 커서 위치 조회
        return self._cursor

    def get_max_length(self) -> int:
        # 가장 긴 데이터 길이 조회
        return self._max_length

    def is_finished(self) -> bool:
        # 시뮬레이션 종료 여부 (커서가 최대 길이 도달)
        return self._cursor >= self._max_length - 1

    def get_progress(self) -> float:
        # 시뮬레이션 진행률 (0.0 ~ 1.0)
        if self._max_length == 0:
            return 1.0
        return self._cursor / (self._max_length - 1)

    def get_availability(self, cursor_position: Optional[int] = None) -> float:
        # 특정 커서 위치의 데이터 유효성 비율
        position = cursor_position if cursor_position is not None else self._cursor
        total_symbols = len(self._data)

        if total_symbols == 0:
            return 0.0

        valid_count = 0
        for prices in self._data.values():
            # 각 심볼의 시작 인덱스 = max_length - len(prices)
            start_index = self._max_length - len(prices)
            if position >= start_index:
                valid_count += 1

        return valid_count / total_symbols

    def __repr__(self) -> str:
        return (
            f"MarketData(symbols={len(self._data)}, "
            f"cursor={self._cursor}/{self._max_length}, "
            f"progress={self.get_progress():.2%})"
        )
