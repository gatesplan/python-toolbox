import pandas as pd
from .save_director.save_director import SaveDirector
from .load_director.load_director import LoadDirector


class BinaryStorage:
    """
    저장 및 로드 로직을 담당하는 인터페이스
    의존성 역전을 통해 구현체를 주입받아 사용
    """

    def __init__(self, basepath: str):
        """
        Args:
            basepath: 파일이 저장될 기본 경로
        """
        self.save_director = SaveDirector()
        self.load_director = LoadDirector(basepath)

    def save(self, candle) -> None:
        """
        Candle 객체 저장

        Args:
            candle: 저장할 Candle 객체
        """
        self.save_director.save(candle)

    def load(self, address) -> pd.DataFrame:
        """
        StockAddress로 DataFrame 로드

        Args:
            address: StockAddress 객체

        Returns:
            로드된 DataFrame
        """
        return self.load_director.load(address)
