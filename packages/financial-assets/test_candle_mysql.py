import unittest
import pandas as pd
import os
from financial_assets import Candle, StockAddress


class TestCandleMySQL(unittest.TestCase):
    """Candle MySQL 저장소 테스트"""

    @classmethod
    def setUpClass(cls):
        """전체 테스트 전 설정"""
        # MySQL 연결 정보 확인
        cls.mysql_host = os.getenv('TEST_MYSQL_HOST', 'localhost')
        cls.mysql_port = os.getenv('TEST_MYSQL_PORT', '3306')
        cls.mysql_dbname = os.getenv('TEST_MYSQL_DBNAME', 'test_fa_candles')
        cls.mysql_username = os.getenv('TEST_MYSQL_USERNAME', 'root')
        cls.mysql_password = os.getenv('TEST_MYSQL_PASSWORD', '')

        # MySQL 서버 연결 테스트 (데이터베이스 지정 없이)
        try:
            from sqlalchemy import create_engine
            connection_string = (
                f"mysql+pymysql://{cls.mysql_username}:{cls.mysql_password}"
                f"@{cls.mysql_host}:{cls.mysql_port}"
            )
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                pass
            cls.mysql_available = True
            engine.dispose()
        except Exception as e:
            cls.mysql_available = False
            print(f"\n경고: MySQL 서버에 연결할 수 없습니다. 테스트를 스킵합니다: {e}")

    def setUp(self):
        """테스트 전 설정"""
        if not self.mysql_available:
            self.skipTest("MySQL 서버를 사용할 수 없습니다")

        # 환경변수 설정 (MySQL)
        os.environ['FA_CANDLE_STORAGE_STRTG'] = 'mysql'
        os.environ['FA_CANDLE_STORAGE_MYSQL_HOST'] = self.mysql_host
        os.environ['FA_CANDLE_STORAGE_MYSQL_PORT'] = self.mysql_port
        os.environ['FA_CANDLE_STORAGE_MYSQL_DBNAME'] = self.mysql_dbname
        os.environ['FA_CANDLE_STORAGE_MYSQL_USERNAME'] = self.mysql_username
        os.environ['FA_CANDLE_STORAGE_MYSQL_PASSWORD'] = self.mysql_password

        # 테스트용 StockAddress
        self.address = StockAddress(
            archetype="stock",
            exchange="nyse",
            tradetype="spot",
            base="test",
            quote="usd",
            timeframe="1d"
        )

        # 테스트용 DataFrame
        self.test_df = pd.DataFrame({
            'timestamp': [1609459200, 1609545600, 1609632000],  # 2021-01-01, 01-02, 01-03 (초 단위)
            'high': [100.5, 101.2, 102.8],
            'low': [99.1, 100.0, 101.5],
            'open': [100.0, 100.5, 101.0],
            'close': [100.3, 101.0, 102.5],
            'volume': [1000000.0, 1100000.0, 1200000.0]
        })

        # 추가 데이터 (업데이트용)
        self.additional_df = pd.DataFrame({
            'timestamp': [1609718400, 1609804800],  # 01-04, 01-05
            'high': [103.5, 104.2],
            'low': [102.0, 103.0],
            'open': [102.5, 103.5],
            'close': [103.0, 104.0],
            'volume': [1300000.0, 1400000.0]
        })

    def tearDown(self):
        """테스트 후 정리"""
        if not self.mysql_available:
            return

        # 클래스 변수 초기화
        Candle._storage = None
        Candle._env_manager = None

        # 테스트 테이블 삭제
        try:
            from sqlalchemy import create_engine, text
            connection_string = (
                f"mysql+pymysql://{self.mysql_username}:{self.mysql_password}"
                f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_dbname}"
            )
            engine = create_engine(connection_string)
            table_name = self.address.to_tablename()
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            engine.dispose()
        except Exception:
            pass

        # 환경변수 제거
        for key in ['FA_CANDLE_STORAGE_STRTG', 'FA_CANDLE_STORAGE_MYSQL_HOST',
                    'FA_CANDLE_STORAGE_MYSQL_PORT', 'FA_CANDLE_STORAGE_MYSQL_DBNAME',
                    'FA_CANDLE_STORAGE_MYSQL_USERNAME', 'FA_CANDLE_STORAGE_MYSQL_PASSWORD']:
            if key in os.environ:
                del os.environ[key]

    def test_candle_creation(self):
        """Candle 객체 생성 테스트"""
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )

        self.assertIsNotNone(candle)
        self.assertEqual(candle.address, self.address)
        self.assertEqual(len(candle.candle_df), 3)
        self.assertTrue(candle.is_new)
        self.assertFalse(candle.is_partial)

    def test_save_new_candle(self):
        """새로운 Candle 저장 테스트"""
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )
        candle.save()

        # 상태 확인
        self.assertFalse(candle.is_new)
        self.assertEqual(candle.storage_last_ts, 1609632000)

    def test_load_candle(self):
        """Candle 로드 테스트"""
        # 저장
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )
        candle.save()

        # 클래스 변수 초기화
        Candle._storage = None
        Candle._env_manager = None

        # 로드
        loaded_candle = Candle.load(self.address)

        # 데이터 검증
        self.assertIsNotNone(loaded_candle)
        self.assertEqual(len(loaded_candle.candle_df), 3)
        self.assertFalse(loaded_candle.is_new)
        self.assertFalse(loaded_candle.is_partial)
        self.assertEqual(loaded_candle.storage_last_ts, 1609632000)

        # timestamp 값 확인
        pd.testing.assert_series_equal(
            loaded_candle.candle_df['timestamp'].astype(int),
            self.test_df['timestamp'].astype(int),
            check_names=False
        )

    def test_load_with_range(self):
        """범위 지정 로드 테스트 (MySQL 전용)"""
        # 저장
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )
        candle.save()

        # 클래스 변수 초기화
        Candle._storage = None
        Candle._env_manager = None

        # 범위 지정 로드
        loaded_candle = Candle.load(self.address, start_ts=1609545600, end_ts=1609718400)

        # 데이터 검증 (2개만 로드되어야 함)
        self.assertEqual(len(loaded_candle.candle_df), 2)
        self.assertEqual(int(loaded_candle.candle_df['timestamp'].iloc[0]), 1609545600)
        self.assertEqual(int(loaded_candle.candle_df['timestamp'].iloc[-1]), 1609632000)

    def test_load_nonexistent_candle(self):
        """존재하지 않는 Candle 로드 테스트"""
        # 로드
        loaded_candle = Candle.load(self.address)

        # 빈 DataFrame 반환
        self.assertIsNotNone(loaded_candle)
        self.assertTrue(loaded_candle.candle_df.empty)
        self.assertEqual(loaded_candle.storage_last_ts, 0)

    def test_update_candle(self):
        """Candle 업데이트 테스트 (온메모리)"""
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )

        # 업데이트
        candle.update(self.additional_df.copy())

        # 데이터 확인
        self.assertEqual(len(candle.candle_df), 5)
        self.assertEqual(int(candle.candle_df['timestamp'].iloc[-1]), 1609804800)

    def test_update_and_save(self):
        """Candle 업데이트 후 저장 테스트"""
        # 초기 저장
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )
        candle.save()

        # 업데이트 및 저장
        candle.update(self.additional_df.copy(), save_immediately=True)

        # 클래스 변수 초기화
        Candle._storage = None
        Candle._env_manager = None

        # 로드하여 확인
        loaded_candle = Candle.load(self.address)
        self.assertEqual(len(loaded_candle.candle_df), 5)
        self.assertEqual(int(loaded_candle.candle_df['timestamp'].iloc[-1]), 1609804800)

    def test_update_with_overlap(self):
        """겹치는 데이터 업데이트 테스트 (MySQL DELETE + INSERT)"""
        # 초기 저장
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )
        candle.save()

        # 겹치는 데이터로 업데이트
        overlap_df = pd.DataFrame({
            'timestamp': [1609632000, 1609718400],  # 마지막 timestamp와 겹침
            'high': [999.0, 103.5],
            'low': [998.0, 102.0],
            'open': [998.5, 102.5],
            'close': [999.0, 103.0],
            'volume': [999999.0, 1300000.0]
        })

        candle.update(overlap_df, save_immediately=True)

        # 클래스 변수 초기화
        Candle._storage = None
        Candle._env_manager = None

        # 로드하여 확인
        loaded_candle = Candle.load(self.address)
        self.assertEqual(len(loaded_candle.candle_df), 4)

        # 겹친 timestamp의 값이 업데이트되었는지 확인
        row = loaded_candle.candle_df[loaded_candle.candle_df['timestamp'] == 1609632000].iloc[0]
        self.assertEqual(float(row['high']), 999.0)

    def test_last_timestamp(self):
        """마지막 타임스탬프 조회 테스트"""
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )

        last_ts = candle.last_timestamp()
        self.assertEqual(last_ts, 1609632000)

        # 빈 DataFrame
        empty_candle = Candle(address=self.address)
        self.assertIsNone(empty_candle.last_timestamp())

    def test_get_price_by_iloc(self):
        """인덱스로 Price 조회 테스트"""
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )

        price = candle.get_price_by_iloc(0)

        self.assertIsNotNone(price)
        self.assertEqual(price.exchange, "nyse")
        self.assertEqual(price.market, "test/usd")
        self.assertEqual(price.t, 1609459200)
        self.assertEqual(price.h, 100.5)
        self.assertEqual(price.l, 99.1)
        self.assertEqual(price.o, 100.0)
        self.assertEqual(price.c, 100.3)
        self.assertEqual(price.v, 1000000.0)

    def test_get_price_by_timestamp(self):
        """타임스탬프로 Price 조회 테스트"""
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )

        price = candle.get_price_by_timestamp(1609545600)

        self.assertIsNotNone(price)
        self.assertEqual(price.t, 1609545600)
        self.assertEqual(price.h, 101.2)

        # 존재하지 않는 타임스탬프
        price_none = candle.get_price_by_timestamp(9999999999)
        self.assertIsNone(price_none)

    def test_hlocv_rounding(self):
        """HLOCV 소수점 4자리 round 테스트"""
        # 소수점 많은 데이터
        df_with_decimals = pd.DataFrame({
            'timestamp': [1609459200],
            'high': [100.123456],
            'low': [99.987654],
            'open': [100.111111],
            'close': [100.555555],
            'volume': [1000000.123456]
        })

        candle = Candle(
            address=self.address,
            candle_df=df_with_decimals.copy()
        )
        candle.save()

        # 클래스 변수 초기화
        Candle._storage = None
        Candle._env_manager = None

        # 로드
        loaded_candle = Candle.load(self.address)

        # 소수점 4자리로 round 되었는지 확인
        self.assertAlmostEqual(loaded_candle.candle_df['high'].iloc[0], 100.1235, places=4)
        self.assertAlmostEqual(loaded_candle.candle_df['low'].iloc[0], 99.9877, places=4)
        self.assertAlmostEqual(loaded_candle.candle_df['open'].iloc[0], 100.1111, places=4)
        self.assertAlmostEqual(loaded_candle.candle_df['close'].iloc[0], 100.5556, places=4)
        # volume은 round 하지 않음 (DOUBLE 타입)
        self.assertAlmostEqual(loaded_candle.candle_df['volume'].iloc[0], 1000000.123456, places=6)

    def test_partial_save_and_load(self):
        """부분 저장 및 로드 시나리오 테스트"""
        # 1. 초기 데이터 저장
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )
        candle.save()

        # 2. 로드
        Candle._storage = None
        Candle._env_manager = None
        loaded_candle = Candle.load(self.address)

        # 3. 새 데이터 추가 및 저장
        loaded_candle.update(self.additional_df.copy())
        loaded_candle.save()

        # 4. 다시 로드하여 확인
        Candle._storage = None
        Candle._env_manager = None
        final_candle = Candle.load(self.address)

        self.assertEqual(len(final_candle.candle_df), 5)
        self.assertEqual(int(final_candle.candle_df['timestamp'].iloc[0]), 1609459200)
        self.assertEqual(int(final_candle.candle_df['timestamp'].iloc[-1]), 1609804800)


if __name__ == '__main__':
    # MySQL 테스트 실행 전 안내
    print("\n" + "="*70)
    print("MySQL 테스트를 실행합니다.")
    print("다음 환경변수를 설정하여 MySQL 연결 정보를 지정할 수 있습니다:")
    print("  - TEST_MYSQL_HOST (기본값: localhost)")
    print("  - TEST_MYSQL_PORT (기본값: 3306)")
    print("  - TEST_MYSQL_DBNAME (기본값: test_fa_candles)")
    print("  - TEST_MYSQL_USERNAME (기본값: root)")
    print("  - TEST_MYSQL_PASSWORD (기본값: '')")
    print("MySQL 서버가 없으면 테스트가 스킵됩니다.")
    print("="*70 + "\n")

    unittest.main()
