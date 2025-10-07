from dataclasses import dataclass


@dataclass
class StockAddress:
    """
    금융 자산의 주소(식별자) 정보를 담는 구조체.

    파일 네이밍 규칙: archetype-exchange-tradetype-base-quote-timeframe
    예: stock-nyse-spot-tsla-usd-1d
    """
    archetype: str
    exchange: str
    tradetype: str
    base: str
    quote: str
    timeframe: str

    def to_filename(self) -> str:
        """파일명 형식으로 변환"""
        return f"{self.archetype}-{self.exchange}-{self.tradetype}-{self.base}-{self.quote}-{self.timeframe}"

    @classmethod
    def from_filename(cls, filename: str) -> "StockAddress":
        """파일명에서 StockAddress 객체 생성"""
        parts = filename.replace(".parquet", "").split("-")
        if len(parts) != 6:
            raise ValueError(f"Invalid filename format: {filename}")

        return cls(*tuple(parts))
