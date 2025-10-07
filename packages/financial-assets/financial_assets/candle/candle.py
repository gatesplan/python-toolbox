import pandas as pd
from ..stock_address import StockAddress
from ..price import Price
from .binstorage.binary_storage import BinaryStorage


class Candle:
    """
    금융 시계열 데이터(캔들스틱) 저장/로드 인터페이스

    엔트리포인트이자 인터페이스 역할
    """

    _storage: BinaryStorage = None

    def __init__(self, address: StockAddress = None, basepath: str = None, candle_df: pd.DataFrame = None):
        """
        Args:
            address: StockAddress 객체
            basepath: 작업 폴더 위치 (None일 경우 './data/financial-assets/candles/')
            candle_df: 캔들 데이터 DataFrame
        """
        # basepath 기본값 설정
        if basepath is None:
            basepath = './data/financial-assets/candles/'

        self.address = address
        self.basepath = basepath
        self.candle_df = candle_df

        # 첫 인스턴스 생성 시 클래스 변수 _storage 자동 생성
        if Candle._storage is None:
            Candle._storage = BinaryStorage(basepath)

    @staticmethod
    def load(address: StockAddress, basepath: str = None) -> 'Candle':
        """
        캔들 데이터 로드

        Args:
            address: StockAddress 객체
            basepath: 작업 폴더 위치 (None일 경우 기본값 사용)

        Returns:
            로드된 Candle 객체
        """
        # 임시 인스턴스를 만들어 _storage 초기화 보장
        temp = Candle(address, basepath)

        # 데이터 로드
        df = Candle._storage.load(address)

        # Candle 객체 생성
        return Candle(address, basepath, df)

    def save(self) -> None:
        """현재 Candle 객체를 저장"""
        Candle._storage.save(self)

    def last_timestamp(self) -> int:
        """
        마지막 타임스탬프 반환

        Returns:
            마지막 타임스탬프
        """
        if self.candle_df is None or len(self.candle_df) == 0:
            return None
        return int(self.candle_df['t'].iloc[-1])

    def get_price_by_iloc(self, idx: int) -> Price:
        """
        인덱스로 Price 객체 조회

        Args:
            idx: DataFrame 인덱스

        Returns:
            Price 객체
        """
        row = self.candle_df.iloc[idx]
        return Price(
            exchange=self.address.exchange,
            market=f"{self.address.base}/{self.address.quote}",
            t=int(row['t']),
            h=float(row['h']),
            l=float(row['l']),
            o=float(row['o']),
            c=float(row['c']),
            v=float(row['v'])
        )

    def get_price_by_timestamp(self, timestamp: int) -> Price:
        """
        타임스탬프로 Price 객체 조회

        Args:
            timestamp: 타임스탬프

        Returns:
            Price 객체 (없으면 None)
        """
        rows = self.candle_df[self.candle_df['t'] == timestamp]
        if len(rows) == 0:
            return None

        row = rows.iloc[0]
        return Price(
            exchange=self.address.exchange,
            market=f"{self.address.base}/{self.address.quote}",
            t=int(row['t']),
            h=float(row['h']),
            l=float(row['l']),
            o=float(row['o']),
            c=float(row['c']),
            v=float(row['v'])
        )
