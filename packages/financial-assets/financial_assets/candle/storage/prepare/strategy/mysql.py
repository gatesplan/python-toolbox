from sqlalchemy import create_engine, text
from .....stock_address import StockAddress
from .base import BasePrepareStrategy
from simple_logger import init_logging, func_logging


class MySQLPrepareStrategy(BasePrepareStrategy):
    """MySQL 저장소 준비 전략"""

    @init_logging
    def __init__(self, config: dict):
        """
        Args:
            config: 환경변수 설정 dict (host, port, dbname, username, password 포함)
        """
        self.config = config

        # SQLAlchemy engine 생성 (데이터베이스 지정)
        connection_string = (
            f"mysql+pymysql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['dbname']}"
        )
        self.engine = create_engine(connection_string, pool_recycle=3600)

        # 데이터베이스 생성용 engine (데이터베이스 지정 없음)
        connection_string_no_db = (
            f"mysql+pymysql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}"
        )
        self.engine_no_db = create_engine(connection_string_no_db, pool_recycle=3600)

    @func_logging
    def prepare(self, address: StockAddress) -> None:
        """
        데이터베이스 및 테이블 생성

        Args:
            address: StockAddress 객체
        """
        # 1. 데이터베이스 생성 (없으면)
        dbname = self.config['dbname']
        create_db_sql = f"CREATE DATABASE IF NOT EXISTS {dbname}"

        with self.engine_no_db.begin() as connection:
            connection.execute(text(create_db_sql))

        # 2. 테이블 생성 (없으면)
        table_name = address.to_tablename()

        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            timestamp BIGINT NOT NULL,
            high DECIMAL(13, 4) NOT NULL,
            low DECIMAL(13, 4) NOT NULL,
            open DECIMAL(13, 4) NOT NULL,
            close DECIMAL(13, 4) NOT NULL,
            volume DOUBLE NOT NULL,
            PRIMARY KEY (timestamp)
        )
        """

        with self.engine.begin() as connection:
            connection.execute(text(create_table_sql))
