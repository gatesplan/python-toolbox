import pandas as pd
from sqlalchemy import create_engine, text
from .....stock_address import StockAddress
from .base import BaseLoadStrategy
from simple_logger import init_logging, func_logging


class MySQLLoadStrategy(BaseLoadStrategy):
    """MySQL 데이터 로드 전략"""

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
    def load(self, address: StockAddress, start_ts: int = None, end_ts: int = None) -> pd.DataFrame:
        """
        데이터 로드

        Args:
            address: StockAddress 객체
            start_ts: 시작 타임스탬프 (이상)
            end_ts: 종료 타임스탬프 (미만)

        Returns:
            로드된 DataFrame
        """
        table_name = address.to_tablename()

        # WHERE 절 구성
        where_clauses = []
        params = {}

        if start_ts is not None:
            where_clauses.append("timestamp >= :start_ts")
            params['start_ts'] = start_ts

        if end_ts is not None:
            where_clauses.append("timestamp < :end_ts")
            params['end_ts'] = end_ts

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # SELECT 쿼리
        query = text(f"SELECT timestamp, high, low, open, close, volume FROM {table_name}{where_sql} ORDER BY timestamp")

        try:
            with self.engine.connect() as connection:
                df = pd.read_sql(query, connection, params=params)

            # 데이터가 없으면 빈 DataFrame
            if df.empty:
                return pd.DataFrame(columns=['timestamp', 'high', 'low', 'open', 'close', 'volume'])

            return df

        except Exception as e:
            # 테이블이 없거나 오류 발생 시 빈 DataFrame 반환
            return pd.DataFrame(columns=['timestamp', 'high', 'low', 'open', 'close', 'volume'])
