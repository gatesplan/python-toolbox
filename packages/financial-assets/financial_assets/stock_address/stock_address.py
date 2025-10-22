from dataclasses import dataclass


@dataclass
class StockAddress:
    """거래소와 거래쌍 정보를 표현하는 주소 체계.
    시장 정보를 표준화된 형식으로 캡슐화합니다."""
    archetype: str
    exchange: str
    tradetype: str
    base: str
    quote: str
    timeframe: str

    def to_filename(self) -> str:
        """주소 정보를 하이픈으로 구분된 파일명 형식으로 변환합니다."""
        return f"{self.archetype}-{self.exchange}-{self.tradetype}-{self.base}-{self.quote}-{self.timeframe}"

    def to_tablename(self) -> str:
        """주소 정보를 언더스코어로 구분된 테이블명 형식으로 변환합니다."""
        return f"{self.archetype}_{self.exchange}_{self.tradetype}_{self.base}_{self.quote}_{self.timeframe}"

    @classmethod
    def from_filename(cls, filename: str) -> "StockAddress":
        """하이픈으로 구분된 파일명 문자열을 파싱하여 StockAddress 객체를 생성합니다."""
        parts = filename.replace(".parquet", "").split("-")
        if len(parts) != 6:
            raise ValueError(f"Invalid filename format: {filename}")

        return cls(*tuple(parts))
