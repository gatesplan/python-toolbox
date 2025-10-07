from .timestamp_to_tick_worker import TimestampToTickWorker
from .file_worker import FileWorker


class SaveDirector:
    """Candle 저장 로직을 관장하는 디렉터"""

    def __init__(self):
        self.timestamp_to_tick_worker = TimestampToTickWorker()
        self.file_worker = FileWorker()

    def save(self, candle) -> None:
        """
        Candle 객체를 저장

        Args:
            candle: 저장할 Candle 객체
        """
        # DataFrame 복사 (원본 보존)
        df = candle.candle_df.copy()

        # timestamp를 tick으로 변환
        ticks, unit = self.timestamp_to_tick_worker(df['t'])
        df['t'] = ticks

        # HLOCV 값 소수점 4자리로 round
        for col in ['h', 'l', 'o', 'c', 'v']:
            df[col] = df[col].round(4)

        # unit을 메타데이터에 저장하기 위해 임시로 candle에 저장
        candle.candle_df = df
        candle._unit = unit

        # 파일로 저장
        self.file_worker(candle)
