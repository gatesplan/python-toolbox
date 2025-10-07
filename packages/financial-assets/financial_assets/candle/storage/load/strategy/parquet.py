from pathlib import Path
import pandas as pd
from .....stock_address import StockAddress
from .base import BaseLoadStrategy
from simple_logger import init_logging, func_logging


class ParquetLoadStrategy(BaseLoadStrategy):
    """Parquet 데이터 로드 전략"""

    @init_logging
    def __init__(self, config: dict):
        """
        Args:
            config: 환경변수 설정 dict (basepath 포함)
        """
        self.basepath = Path(config['basepath'])

    @func_logging
    def load(self, address: StockAddress, start_ts: int = None, end_ts: int = None) -> pd.DataFrame:
        """
        데이터 로드

        Args:
            address: StockAddress 객체
            start_ts: 시작 타임스탬프 (무시됨)
            end_ts: 종료 타임스탬프 (무시됨)

        Returns:
            로드된 DataFrame
        """
        filepath = self.basepath / f"{address.to_filename()}.parquet"

        # 파일이 없으면 빈 DataFrame 반환
        if not filepath.exists():
            return pd.DataFrame(columns=['timestamp', 'high', 'low', 'open', 'close', 'volume'])

        # parquet 파일 로드
        df = pd.read_parquet(filepath)

        # metadata에서 unit 읽기
        unit = df.attrs.get('unit', 1)

        # tick → timestamp 역변환
        df = self._tick_to_timestamp(df, unit)

        # start_ts/end_ts는 무시하고 전체 로드
        if start_ts is not None or end_ts is not None:
            import warnings
            warnings.warn("ParquetLoadStrategy does not support start_ts/end_ts filtering. Loading entire dataset.")

        return df

    @func_logging
    def _tick_to_timestamp(self, df: pd.DataFrame, unit: int) -> pd.DataFrame:
        """
        tick을 timestamp로 역변환

        Args:
            df: DataFrame (tick 컬럼 포함)
            unit: tick 변환 단위

        Returns:
            timestamp 컬럼을 가진 DataFrame
        """
        if 'tick' in df.columns:
            df['timestamp'] = df['tick'] * unit
            df = df.drop(columns=['tick'])

            # 컬럼 순서 재정렬: timestamp를 맨 앞으로
            cols = ['timestamp', 'high', 'low', 'open', 'close', 'volume']
            df = df[cols]

        return df
