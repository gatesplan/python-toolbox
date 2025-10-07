import unittest
import pandas as pd
import tempfile
import shutil
import os
from financial_assets import Candle, StockAddress


class TestCandle(unittest.TestCase):
    """Candle 객체 테스트"""

    def setUp(self):
        """테스트 전 설정"""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()

        # 테스트용 StockAddress
        self.address = StockAddress(
            archetype="stock",
            exchange="nyse",
            tradetype="spot",
            base="tsla",
            quote="usd",
            timeframe="1d"
        )

        # 테스트용 DataFrame
        self.test_df = pd.DataFrame({
            't': [1609459200000, 1609545600000, 1609632000000],  # 2021-01-01, 01-02, 01-03
            'h': [100.5, 101.2, 102.8],
            'l': [99.1, 100.0, 101.5],
            'o': [100.0, 100.5, 101.0],
            'c': [100.3, 101.0, 102.5],
            'v': [1000000.0, 1100000.0, 1200000.0]
        })

    def tearDown(self):
        """테스트 후 정리"""
        # 임시 디렉토리 삭제
        shutil.rmtree(self.test_dir)
        # 클래스 변수 초기화
        Candle._storage = None

    def test_candle_creation(self):
        """Candle 객체 생성 테스트"""
        candle = Candle(
            address=self.address,
            basepath=self.test_dir,
            candle_df=self.test_df.copy()
        )

        self.assertIsNotNone(candle)
        self.assertEqual(candle.address, self.address)
        self.assertEqual(candle.basepath, self.test_dir)
        self.assertEqual(len(candle.candle_df), 3)

    def test_save_and_load(self):
        """저장 및 로드 테스트"""
        # Candle 객체 생성 및 저장
        candle = Candle(
            address=self.address,
            basepath=self.test_dir,
            candle_df=self.test_df.copy()
        )
        candle.save()

        # 파일이 생성되었는지 확인
        expected_filename = self.address.to_filename() + ".parquet"
        expected_path = os.path.join(self.test_dir, expected_filename)
        self.assertTrue(os.path.exists(expected_path))

        # 클래스 변수 초기화
        Candle._storage = None

        # 로드
        loaded_candle = Candle.load(self.address, self.test_dir)

        # 데이터 검증
        self.assertIsNotNone(loaded_candle)
        self.assertEqual(len(loaded_candle.candle_df), 3)

        # timestamp 값 확인
        pd.testing.assert_series_equal(
            loaded_candle.candle_df['t'].astype(int),
            self.test_df['t'].astype(int),
            check_names=False
        )

    def test_last_timestamp(self):
        """마지막 타임스탬프 조회 테스트"""
        candle = Candle(
            address=self.address,
            basepath=self.test_dir,
            candle_df=self.test_df.copy()
        )

        last_ts = candle.last_timestamp()
        self.assertEqual(last_ts, 1609632000000)

    def test_get_price_by_iloc(self):
        """인덱스로 Price 조회 테스트"""
        candle = Candle(
            address=self.address,
            basepath=self.test_dir,
            candle_df=self.test_df.copy()
        )

        price = candle.get_price_by_iloc(0)

        self.assertIsNotNone(price)
        self.assertEqual(price.exchange, "nyse")
        self.assertEqual(price.market, "tsla/usd")
        self.assertEqual(price.t, 1609459200000)
        self.assertEqual(price.h, 100.5)
        self.assertEqual(price.l, 99.1)
        self.assertEqual(price.o, 100.0)
        self.assertEqual(price.c, 100.3)
        self.assertEqual(price.v, 1000000.0)

    def test_get_price_by_timestamp(self):
        """타임스탬프로 Price 조회 테스트"""
        candle = Candle(
            address=self.address,
            basepath=self.test_dir,
            candle_df=self.test_df.copy()
        )

        price = candle.get_price_by_timestamp(1609545600000)

        self.assertIsNotNone(price)
        self.assertEqual(price.t, 1609545600000)
        self.assertEqual(price.h, 101.2)

        # 존재하지 않는 타임스탬프
        price_none = candle.get_price_by_timestamp(9999999999999)
        self.assertIsNone(price_none)

    def test_timestamp_to_tick_conversion(self):
        """Timestamp-Tick 변환 테스트"""
        candle = Candle(
            address=self.address,
            basepath=self.test_dir,
            candle_df=self.test_df.copy()
        )

        # 저장
        candle.save()

        # 클래스 변수 초기화
        Candle._storage = None

        # 로드
        loaded_candle = Candle.load(self.address, self.test_dir)

        # timestamp가 정확히 복원되었는지 확인
        for i in range(len(self.test_df)):
            original_t = int(self.test_df['t'].iloc[i])
            loaded_t = int(loaded_candle.candle_df['t'].iloc[i])
            self.assertEqual(original_t, loaded_t)

    def test_hlocv_rounding(self):
        """HLOCV 소수점 4자리 round 테스트"""
        # 소수점 많은 데이터
        df_with_decimals = pd.DataFrame({
            't': [1609459200000],
            'h': [100.123456],
            'l': [99.987654],
            'o': [100.111111],
            'c': [100.555555],
            'v': [1000000.123456]
        })

        candle = Candle(
            address=self.address,
            basepath=self.test_dir,
            candle_df=df_with_decimals.copy()
        )
        candle.save()

        # 클래스 변수 초기화
        Candle._storage = None

        # 로드
        loaded_candle = Candle.load(self.address, self.test_dir)

        # 소수점 4자리로 round 되었는지 확인
        self.assertAlmostEqual(loaded_candle.candle_df['h'].iloc[0], 100.1235, places=4)
        self.assertAlmostEqual(loaded_candle.candle_df['l'].iloc[0], 99.9877, places=4)
        self.assertAlmostEqual(loaded_candle.candle_df['o'].iloc[0], 100.1111, places=4)
        self.assertAlmostEqual(loaded_candle.candle_df['c'].iloc[0], 100.5556, places=4)
        self.assertAlmostEqual(loaded_candle.candle_df['v'].iloc[0], 1000000.1235, places=4)

    def test_default_basepath(self):
        """기본 basepath 테스트"""
        candle = Candle(address=self.address)
        self.assertEqual(candle.basepath, './data/financial-assets/candles/')


if __name__ == '__main__':
    unittest.main()
