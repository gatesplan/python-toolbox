from dataclasses import dataclass
from ..symbol import Symbol


@dataclass
class StockAddress:
    """거래소와 거래쌍 정보 표현 주소 체계"""
    archetype: str
    exchange: str
    tradetype: str
    base: str
    quote: str
    timeframe: str

    def to_filename(self) -> str:
        """하이픈 구분 파일명 형식"""
        return f"{self.archetype}-{self.exchange}-{self.tradetype}-{self.base}-{self.quote}-{self.timeframe}"

    def to_tablename(self) -> str:
        """언더스코어 구분 테이블명 형식"""
        return f"{self.archetype}_{self.exchange}_{self.tradetype}_{self.base}_{self.quote}_{self.timeframe}"

    def to_symbol(self) -> Symbol:
        """거래쌍 심볼 객체 생성 (base/quote)"""
        return Symbol(f"{self.base}/{self.quote}")

    @classmethod
    def from_filename(cls, filename: str) -> "StockAddress":
        """파일명 문자열 파싱하여 StockAddress 생성"""
        parts = filename.replace(".parquet", "").split("-")
        if len(parts) != 6:
            raise ValueError(f"Invalid filename format: {filename}")

        return cls(*tuple(parts))
