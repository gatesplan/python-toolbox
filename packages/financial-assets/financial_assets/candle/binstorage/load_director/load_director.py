import pandas as pd
from .tick_to_timestamp_worker import TickToTimestampWorker
from .file_worker import FileWorker


class LoadDirector:
    """Candle 로드 로직을 관장하는 디렉터"""

    def __init__(self, basepath: str):
        """
        Args:
            basepath: 파일이 저장된 기본 경로
        """
        self.tick_to_timestamp_worker = TickToTimestampWorker()
        self.file_worker = FileWorker(basepath)

    def load(self, address) -> pd.DataFrame:
        """
        파일에서 Candle DataFrame 로드

        Args:
            address: StockAddress 객체

        Returns:
            로드된 DataFrame (timestamp로 복원됨)
        """
        # 파일에서 DataFrame과 unit 로드
        df, unit = self.file_worker(address)

        # tick을 timestamp로 복원
        df['t'] = self.tick_to_timestamp_worker(df['t'], unit)

        return df
