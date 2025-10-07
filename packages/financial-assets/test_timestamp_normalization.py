"""
Timestamp 정규화 테스트
밀리초 timestamp가 자동으로 초로 변환되는지 확인
"""
import unittest
import pandas as pd
import tempfile
import shutil
import warnings
from financial_assets import Candle, StockAddress


class TestTimestampNormalization(unittest.TestCase):
    """Timestamp 정규화 테스트"""

    def setUp(self):
        """테스트 전 설정"""
        self.test_dir = tempfile.mkdtemp()

        self.address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1m"
        )

    def tearDown(self):
        """테스트 후 정리"""
        shutil.rmtree(self.test_dir)
        Candle._storage = None
        Candle._env_manager = None

    def test_millisecond_to_second_conversion_on_init(self):
        """__init__ 시 밀리초 → 초 변환 테스트"""
        # 밀리초 timestamp
        df_ms = pd.DataFrame({
            'timestamp': [1609459200000, 1609459260000, 1609459320000],  # 밀리초
            'high': [100.5, 101.2, 102.8],
            'low': [99.1, 100.0, 101.5],
            'open': [100.0, 100.5, 101.0],
            'close': [100.3, 101.0, 102.5],
            'volume': [1000.0, 1100.0, 1200.0]
        })

        # 경고 발생 확인
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            candle = Candle(address=self.address, candle_df=df_ms)

            # 경고가 발생했는지 확인
            self.assertEqual(len(w), 1)
            self.assertIn("millisecond", str(w[0].message).lower())

        # 초로 변환되었는지 확인
        self.assertEqual(candle.candle_df['timestamp'].iloc[0], 1609459200)
        self.assertEqual(candle.candle_df['timestamp'].iloc[1], 1609459260)
        self.assertEqual(candle.candle_df['timestamp'].iloc[2], 1609459320)

    def test_second_timestamp_unchanged(self):
        """초 단위 timestamp는 변환하지 않음"""
        # 초 단위 timestamp
        df_sec = pd.DataFrame({
            'timestamp': [1609459200, 1609459260, 1609459320],  # 초
            'high': [100.5, 101.2, 102.8],
            'low': [99.1, 100.0, 101.5],
            'open': [100.0, 100.5, 101.0],
            'close': [100.3, 101.0, 102.5],
            'volume': [1000.0, 1100.0, 1200.0]
        })

        # 경고가 발생하지 않아야 함
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            candle = Candle(address=self.address, candle_df=df_sec)

            # 경고가 발생하지 않음
            self.assertEqual(len(w), 0)

        # 값이 그대로 유지됨
        self.assertEqual(candle.candle_df['timestamp'].iloc[0], 1609459200)
        self.assertEqual(candle.candle_df['timestamp'].iloc[1], 1609459260)

    def test_update_with_millisecond_timestamp(self):
        """update 시 밀리초 → 초 변환 테스트"""
        # 초 단위로 시작
        df_sec = pd.DataFrame({
            'timestamp': [1609459200],
            'high': [100.5],
            'low': [99.1],
            'open': [100.0],
            'close': [100.3],
            'volume': [1000.0]
        })

        candle = Candle(address=self.address, candle_df=df_sec)

        # 밀리초 데이터로 업데이트
        df_ms_new = pd.DataFrame({
            'timestamp': [1609459260000, 1609459320000],  # 밀리초
            'high': [101.2, 102.8],
            'low': [100.0, 101.5],
            'open': [100.5, 101.0],
            'close': [101.0, 102.5],
            'volume': [1100.0, 1200.0]
        })

        # 경고 발생 확인
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            candle.update(df_ms_new)

            # 경고가 발생했는지 확인
            self.assertEqual(len(w), 1)
            self.assertIn("millisecond", str(w[0].message).lower())

        # 모든 timestamp가 초 단위로 통일됨
        self.assertEqual(len(candle.candle_df), 3)
        self.assertEqual(candle.candle_df['timestamp'].iloc[0], 1609459200)
        self.assertEqual(candle.candle_df['timestamp'].iloc[1], 1609459260)
        self.assertEqual(candle.candle_df['timestamp'].iloc[2], 1609459320)


if __name__ == '__main__':
    unittest.main()
