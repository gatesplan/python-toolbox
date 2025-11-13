"""거래쌍 심볼 표준화 클래스"""


class Symbol:
    """거래쌍 심볼 파싱 및 형식 변환"""

    def __init__(self, symbol: str):
        # "BTC/USDT" 또는 "BTC-USDT" 형식만 지원
        self._base, self._quote = self._parse(symbol)

    def _parse(self, symbol: str) -> tuple[str, str]:
        # 심볼 문자열을 base, quote로 분리
        if "/" in symbol:
            parts = symbol.split("/")
        elif "-" in symbol:
            parts = symbol.split("-")
        else:
            raise ValueError(
                f"Invalid symbol format: '{symbol}'. "
                "Expected format: 'BASE/QUOTE' or 'BASE-QUOTE'"
            )

        if len(parts) != 2:
            raise ValueError(
                f"Invalid symbol format: '{symbol}'. "
                f"Expected exactly 2 parts, got {len(parts)}"
            )

        base = parts[0].upper().strip()
        quote = parts[1].upper().strip()

        if not base or not quote:
            raise ValueError(
                f"Invalid symbol format: '{symbol}'. "
                "Base and quote cannot be empty"
            )

        return base, quote

    @property
    def base(self) -> str:
        """기준 자산 심볼"""
        return self._base

    @property
    def quote(self) -> str:
        """견적 자산 심볼"""
        return self._quote

    def to_slash(self) -> str:
        """슬래시 형식 (BTC/USDT)"""
        return f"{self._base}/{self._quote}"

    def to_dash(self) -> str:
        """하이픈 형식 (BTC-USDT)"""
        return f"{self._base}-{self._quote}"

    def to_compact(self) -> str:
        """구분자 없는 형식 (BTCUSDT) - 출력 전용"""
        return f"{self._base}{self._quote}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Symbol):
            return False
        return self._base == other._base and self._quote == other._quote

    def __hash__(self) -> int:
        return hash((self._base, self._quote))

    def __str__(self) -> str:
        return self.to_slash()

    def __repr__(self) -> str:
        return f"Symbol(base={self._base!r}, quote={self._quote!r})"
