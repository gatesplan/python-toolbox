import unittest
import pandas as pd
import tempfile
import shutil
import os
from pathlib import Path
from financial_assets import Candle, StockAddress


class TestCandleParquet(unittest.TestCase):
    """Candle Parquet 저장소 테스트"""

    def setUp(self):
        """테스트 전 설정"""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()

        # .env 파일 경로 설정
        self.env_path = Path(self.test_dir) / '.env'

        # 환경변수 설정 (Parquet)
        os.environ['FA_CANDLE_STORAGE_STRTG'] = 'parquet'
        os.environ['FA_CANDLE_STORAGE_PARQUET_BASEPATH'] = self.test_dir

        # 테스트용 StockAddress
        self.address = StockAddress(
            archetype="stock",
            exchange="nyse",
            tradetype="spot",
            base="tsla",
            quote="usd",
            timeframe="1d"
        )

        # 테스트용 DataFrame (새 컬럼명)
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
        # 임시 디렉토리 삭제
        shutil.rmtree(self.test_dir, ignore_errors=True)

        # 클래스 변수 초기화
        Candle._storage = None
        Candle._env_manager = None

        # 환경변수 제거
        if 'FA_CANDLE_STORAGE_STRTG' in os.environ:
            del os.environ['FA_CANDLE_STORAGE_STRTG']
        if 'FA_CANDLE_STORAGE_PARQUET_BASEPATH' in os.environ:
            del os.environ['FA_CANDLE_STORAGE_PARQUET_BASEPATH']

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

        # 파일이 생성되었는지 확인
        expected_filename = self.address.to_filename() + ".parquet"
        expected_path = os.path.join(self.test_dir, expected_filename)
        self.assertTrue(os.path.exists(expected_path))

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

    def test_update_with_duplicate(self):
        """중복 데이터 업데이트 테스트"""
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )

        # 중복된 timestamp를 포함한 데이터
        duplicate_df = pd.DataFrame({
            'timestamp': [1609632000, 1609718400],  # 첫 번째는 중복
            'high': [999.0, 103.5],
            'low': [998.0, 102.0],
            'open': [998.5, 102.5],
            'close': [999.0, 103.0],
            'volume': [999999.0, 1300000.0]
        })

        # 업데이트 (keep='last'이므로 나중 데이터가 유지됨)
        candle.update(duplicate_df)

        # 중복 제거 확인
        self.assertEqual(len(candle.candle_df), 4)

        # 중복 timestamp의 값이 업데이트되었는지 확인
        row = candle.candle_df[candle.candle_df['timestamp'] == 1609632000].iloc[0]
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
        self.assertEqual(price.market, "tsla/usd")
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

    def test_timestamp_to_tick_conversion(self):
        """Timestamp-Tick 변환 테스트"""
        candle = Candle(
            address=self.address,
            candle_df=self.test_df.copy()
        )

        # 저장
        candle.save()

        # 클래스 변수 초기화
        Candle._storage = None
        Candle._env_manager = None

        # 로드
        loaded_candle = Candle.load(self.address)

        # timestamp가 정확히 복원되었는지 확인
        for i in range(len(self.test_df)):
            original_t = int(self.test_df['timestamp'].iloc[i])
            loaded_t = int(loaded_candle.candle_df['timestamp'].iloc[i])
            self.assertEqual(original_t, loaded_t)

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
        # volume은 round 하지 않음
        self.assertEqual(loaded_candle.candle_df['volume'].iloc[0], 1000000.123456)

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
    unittest.main()
