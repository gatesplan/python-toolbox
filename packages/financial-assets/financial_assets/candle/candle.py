import time
import pandas as pd
from ..stock_address import StockAddress
from ..price import Price
from .env import EnvManageWorker
from .storage import StorageDirector
from simple_logger import init_logging, func_logging
import warnings


class Candle:
    """
    금융 시계열 데이터(캔들스틱) 저장/로드 인터페이스
    """

    _env_manager: EnvManageWorker = None
    _storage: StorageDirector = None

    @init_logging
    def __init__(self, address: StockAddress, candle_df: pd.DataFrame = None):
        """
        Args:
            address: StockAddress 객체
            candle_df: 캔들 데이터 DataFrame
        """
        self.address = address
        self.candle_df = self._normalize_timestamp(candle_df) if candle_df is not None else None
        self.is_new = True
        self.is_partial = False
        self.storage_last_ts = None

        # 클래스 변수 초기화
        if Candle._env_manager is None:
            Candle._env_manager = EnvManageWorker()

        if Candle._storage is None:
            env_config = Candle._env_manager()
            Candle._storage = StorageDirector(env_config)

    @staticmethod
    @func_logging(log_params=True)
    def load(address: StockAddress, start_ts: int = None, end_ts: int = None) -> 'Candle':
        """
        캔들 데이터 로드

        Args:
            address: StockAddress 객체
            start_ts: 시작 타임스탬프 (이상)
            end_ts: 종료 타임스탬프 (미만)

        Returns:
            로드된 Candle 객체
        """
        # 임시 인스턴스를 만들어 _storage 초기화 보장
        temp = Candle(address)

        # 데이터 로드
        load_worker = Candle._storage.get_load_worker()
        df = load_worker(address, start_ts, end_ts)

        # Candle 객체 생성
        candle = Candle(address, df)
        candle.is_new = False
        candle.is_partial = (start_ts is not None)

        # storage_last_ts 설정
        if df.empty:
            candle.storage_last_ts = 0
        else:
            candle.storage_last_ts = int(df['timestamp'].iloc[-1])

        return candle

    @func_logging
    def save(self) -> None:
        """현재 Candle 객체를 저장"""
        if self.candle_df is None or self.candle_df.empty:
            return

        # is_new=True면 PrepareStrategy 먼저 실행
        if self.is_new:
            prepare_worker = Candle._storage.get_prepare_worker()
            prepare_worker(self.address)

        # SaveStrategy로 데이터 저장
        save_worker = Candle._storage.get_save_worker()
        save_worker(self.address, self.candle_df, self.storage_last_ts)

        # 저장 후 상태 업데이트
        self.is_new = False
        self.storage_last_ts = int(self.candle_df['timestamp'].iloc[-1])

        # 메타데이터 업데이트
        metadata_worker = Candle._storage.get_metadata_worker()
        metadata_worker.set_last_update_ts(self.address, self.storage_last_ts)

    @func_logging
    def update(self, new_df: pd.DataFrame, save_immediately: bool = False) -> None:
        """
        온메모리 병합

        Args:
            new_df: 새로운 데이터 DataFrame
            save_immediately: True면 자동으로 save() 호출
        """
        # timestamp 정규화
        new_df = self._normalize_timestamp(new_df)

        if self.candle_df is None or self.candle_df.empty:
            self.candle_df = new_df.copy()
        else:
            # timestamp 기준으로 병합 (중복 제거)
            combined = pd.concat([self.candle_df, new_df], ignore_index=True)
            combined = combined.drop_duplicates(subset=['timestamp'], keep='last')
            combined = combined.sort_values('timestamp').reset_index(drop=True)
            self.candle_df = combined

        if save_immediately:
            self.save()

    @staticmethod
    def _normalize_timestamp(df: pd.DataFrame) -> pd.DataFrame:
        """
        밀리초 timestamp를 초로 자동 변환

        Args:
            df: 검증할 DataFrame

        Returns:
            timestamp가 초 단위로 정규화된 DataFrame
        """
        if df is None or df.empty:
            return df

        if 'timestamp' not in df.columns:
            return df

        # 밀리초 판단 기준: 10^10 (2286-11-20 17:46:40 UTC)
        TIMESTAMP_SECOND_MAX = 10_000_000_000

        max_ts = df['timestamp'].max()

        if max_ts >= TIMESTAMP_SECOND_MAX:
            # 밀리초 감지 → 초로 변환
            df = df.copy()
            df['timestamp'] = df['timestamp'] // 1000

            warnings.warn(
                f"Detected millisecond timestamps in DataFrame. "
                f"Automatically converted to seconds for consistency. "
                f"Original max: {max_ts}, Converted max: {df['timestamp'].max()}",
                UserWarning
            )

        return df

    @func_logging
    def last_timestamp(self) -> int:
        """
        마지막 타임스탬프 반환

        Returns:
            마지막 타임스탬프
        """
        if self.candle_df is None or len(self.candle_df) == 0:
            return None
        return int(self.candle_df['timestamp'].iloc[-1])

    @func_logging
    def get_price_by_iloc(self, idx: int) -> Price:
        """
        인덱스로 Price 객체 조회

        Args:
            idx: DataFrame 인덱스

        Returns:
            Price 객체
        """
        row = self.candle_df.iloc[idx]
        return Price(
            exchange=self.address.exchange,
            market=f"{self.address.base}/{self.address.quote}",
            t=int(row['timestamp']),
            h=float(row['high']),
            l=float(row['low']),
            o=float(row['open']),
            c=float(row['close']),
            v=float(row['volume'])
        )

    @func_logging
    def get_price_by_timestamp(self, timestamp: int) -> Price:
        """
        타임스탬프로 Price 객체 조회

        Args:
            timestamp: 타임스탬프

        Returns:
            Price 객체 (없으면 None)
        """
        rows = self.candle_df[self.candle_df['timestamp'] == timestamp]
        if len(rows) == 0:
            return None

        row = rows.iloc[0]
        return Price(
            exchange=self.address.exchange,
            market=f"{self.address.base}/{self.address.quote}",
            t=int(row['timestamp']),
            h=float(row['high']),
            l=float(row['low']),
            o=float(row['open']),
            c=float(row['close']),
            v=float(row['volume'])
        )

    @staticmethod
    @func_logging
    def get_last_update_ts(address: StockAddress) -> int | None:
        """
        마지막 업데이트 타임스탬프 조회 (데이터 로드 없이)

        Args:
            address: StockAddress 객체

        Returns:
            마지막 업데이트 타임스탬프 (없으면 None)
        """
        # 임시 인스턴스를 만들어 _storage 초기화 보장
        temp = Candle(address)

        metadata_worker = Candle._storage.get_metadata_worker()
        return metadata_worker.get_last_update_ts(address)

    @staticmethod
    @func_logging
    def get_time_since_last_update(address: StockAddress) -> int | None:
        """
        마지막 업데이트 이후 경과 시간 (초)

        Args:
            address: StockAddress 객체

        Returns:
            경과 시간 (초), 데이터 없으면 None
        """
        last_ts = Candle.get_last_update_ts(address)
        if last_ts is None:
            return None

        current_ts = int(time.time())
        return current_ts - last_ts
