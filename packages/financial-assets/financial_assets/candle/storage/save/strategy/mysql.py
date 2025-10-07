import pandas as pd
from sqlalchemy import create_engine, text
from .....stock_address import StockAddress
from .base import BaseSaveStrategy
from simple_logger import init_logging, func_logging


class MySQLSaveStrategy(BaseSaveStrategy):
    """MySQL 데이터 저장 전략"""

    @init_logging
    def __init__(self, config: dict):
        """
        Args:
            config: 환경변수 설정 dict (host, port, dbname, username, password 포함)
        """
        # SQLAlchemy engine 생성
        connection_string = (
            f"mysql+pymysql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['dbname']}"
        )
        self.engine = create_engine(connection_string, pool_recycle=3600, pool_size=5)

    @func_logging
    def save(self, address: StockAddress, df: pd.DataFrame, storage_last_ts: int = None) -> None:
        """
        데이터 저장

        Args:
            address: StockAddress 객체
            df: 저장할 DataFrame
            storage_last_ts: 저장소에 기록된 마지막 타임스탬프
        """
        table_name = address.to_tablename()

        # round(4) 전처리
        df_to_save = self._preprocess(df.copy())

        with self.engine.begin() as connection:
            if storage_last_ts is not None:
                # storage_last_ts 이상 데이터 DELETE
                delete_sql = text(f"DELETE FROM {table_name} WHERE timestamp >= :last_ts")
                connection.execute(delete_sql, {"last_ts": storage_last_ts})

                # df에서 storage_last_ts 이상만 필터링
                df_to_save = df_to_save[df_to_save['timestamp'] >= storage_last_ts]

            # INSERT
            if not df_to_save.empty:
                df_to_save.to_sql(table_name, connection, if_exists='append', index=False)

    @func_logging
    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        데이터 전처리: HLOCV 값을 round(4)

        Args:
            df: DataFrame

        Returns:
            전처리된 DataFrame
        """
        df['high'] = df['high'].round(4)
        df['low'] = df['low'].round(4)
        df['open'] = df['open'].round(4)
        df['close'] = df['close'].round(4)
        return df
