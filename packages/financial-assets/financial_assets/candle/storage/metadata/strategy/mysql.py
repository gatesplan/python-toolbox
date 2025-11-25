from sqlalchemy import create_engine, text
from .....stock_address import StockAddress
from .base import BaseMetadataStrategy
from simple_logger import init_logging, func_logging


class MySQLMetadataStrategy(BaseMetadataStrategy):
    # MySQL 메타데이터 전략 (테이블 기반)

    METADATA_TABLE = 'fa_candles_metadata'

    @init_logging
    def __init__(self, config: dict):
        # SQLAlchemy engine 생성
        connection_string = (
            f"mysql+pymysql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['dbname']}"
        )
        self.engine = create_engine(connection_string, pool_recycle=3600, pool_size=5)

    @func_logging
    def get_last_update_ts(self, address: StockAddress) -> int | None:
        # 마지막 업데이트 타임스탬프 조회
        address_key = address.to_tablename()

        query = text(
            f"SELECT last_update_ts FROM {self.METADATA_TABLE} "
            f"WHERE address_key = :address_key"
        )

        try:
            with self.engine.connect() as connection:
                result = connection.execute(query, {"address_key": address_key})
                row = result.fetchone()

                if row is None:
                    return None

                return int(row[0])

        except Exception:
            # 테이블이 없거나 오류 발생 시 None 반환
            return None

    @func_logging
    def set_last_update_ts(self, address: StockAddress, timestamp: int) -> None:
        # 마지막 업데이트 타임스탬프 저장
        address_key = address.to_tablename()

        # UPSERT (INSERT ... ON DUPLICATE KEY UPDATE)
        query = text(
            f"INSERT INTO {self.METADATA_TABLE} (address_key, last_update_ts) "
            f"VALUES (:address_key, :timestamp) "
            f"ON DUPLICATE KEY UPDATE last_update_ts = :timestamp"
        )

        with self.engine.begin() as connection:
            connection.execute(query, {"address_key": address_key, "timestamp": timestamp})
