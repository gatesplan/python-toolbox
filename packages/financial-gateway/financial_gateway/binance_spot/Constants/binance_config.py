# Binance Spot API 설정 상수

class BinanceConfig:
    # API 호출 제한
    REQUEST_TIMEOUT = 10  # seconds
    MAX_RETRIES = 3

    # 주문 설정
    DEFAULT_TIME_IN_FORCE = "GTC"  # Good Till Cancel

    # 시장 데이터 설정
    DEFAULT_KLINE_LIMIT = 500
    DEFAULT_DEPTH_LIMIT = 100

    # 간격 매핑
    INTERVAL_MAP = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
        "1M": "1M",
    }
