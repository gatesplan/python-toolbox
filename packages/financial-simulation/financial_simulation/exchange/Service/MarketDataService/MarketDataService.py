# 시장 데이터 조회 서비스

from simple_logger import init_logging, func_logging
from financial_assets.orderbook import Orderbook, OrderbookLevel
from financial_assets.symbol import Symbol
from financial_assets.constants import MarketStatus
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData


class MarketDataService:
    # MarketData 기반 시장 정보 조회 및 변환 서비스

    @init_logging(level="INFO", log_params=True)
    def __init__(self, market_data: MarketData):
        self._market_data = market_data

    @func_logging(level="INFO", log_params=True)
    def generate_orderbook(self, symbol: str, depth: int = 20) -> Orderbook:
        """OHLC 기반 더미 호가창 생성 (Gateway API 호환용).

        Args:
            symbol: 심볼 (예: "BTC/USDT")
            depth: 호가 깊이 (기본값: 20)

        Returns:
            Orderbook: financial-assets Orderbook 객체
        """
        price_data = self._market_data.get_current(symbol)

        if price_data is None:
            return Orderbook(asks=[], bids=[])

        # High-Low 범위로 변동성 추정
        volatility = (price_data.h - price_data.l) / price_data.c if price_data.c > 0 else 0.01
        spread = price_data.c * max(0.001, volatility * 0.1)  # 최소 0.1% 스프레드
        tick_size = spread / depth

        bids = []
        asks = []

        for i in range(depth):
            # Bid: 현재가 아래
            bid_price = price_data.c - spread - (i * tick_size)
            # Ask: 현재가 위
            ask_price = price_data.c + spread + (i * tick_size)

            # 깊이별 수량 (멱함수로 증가)
            size = 1.0 * (1.2 ** i)

            bids.append(OrderbookLevel(price=bid_price, size=size))
            asks.append(OrderbookLevel(price=ask_price, size=size))

        return Orderbook(asks=asks, bids=bids)

    @func_logging(level="INFO", log_params=True)
    def get_available_markets(self) -> list[dict]:
        """마켓 목록 조회 (Gateway API 호환용).

        Returns:
            list[dict]: [{"symbol": Symbol, "status": MarketStatus}, ...]
        """
        symbols = self._market_data.get_symbols()
        markets = []

        for symbol_str in symbols:
            markets.append({
                "symbol": Symbol.from_slash(symbol_str),
                "status": MarketStatus.TRADING  # 시뮬레이션은 항상 TRADING
            })

        return markets
