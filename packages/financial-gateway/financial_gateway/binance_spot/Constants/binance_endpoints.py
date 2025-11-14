# Binance Spot API 엔드포인트 상수

class BinanceEndpoints:
    # Base URL
    BASE_URL = "https://api.binance.com"

    # 주문 관리
    ORDER = "/api/v3/order"

    # 계정 정보
    ACCOUNT = "/api/v3/account"
    MY_TRADES = "/api/v3/myTrades"

    # 시장 데이터 (Public)
    TICKER_24HR = "/api/v3/ticker/24hr"
    DEPTH = "/api/v3/depth"
    KLINES = "/api/v3/klines"
    EXCHANGE_INFO = "/api/v3/exchangeInfo"
    TIME = "/api/v3/time"
