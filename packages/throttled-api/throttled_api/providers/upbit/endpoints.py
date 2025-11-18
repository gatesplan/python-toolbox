"""
Upbit API 엔드포인트별 카테고리 정의

공식 문서: https://docs.upbit.com/reference
Rate Limit 정책:
- QUOTATION: 초당 10회, 분당 600회 (종목, 캔들, 체결, 티커, 호가별 각각)
- EXCHANGE_ORDER: 초당 8회, 분당 200회 (주문 생성/취소)
- EXCHANGE_NON_ORDER: 초당 30회, 분당 900회 (주문 외 요청)
"""
from typing import Dict, Tuple, Literal

# 엔드포인트 카테고리 타입
EndpointCategory = Literal["QUOTATION", "EXCHANGE_ORDER", "EXCHANGE_NON_ORDER"]

# (method, endpoint) -> category 매핑
UPBIT_ENDPOINT_CATEGORIES: Dict[Tuple[str, str], EndpointCategory] = {
    # ========== QUOTATION API (시세 조회, 인증 불필요) ==========
    # Market 정보
    ("GET", "/v1/market/all"): "QUOTATION",

    # Candles (캔들/차트)
    ("GET", "/v1/candles/minutes/1"): "QUOTATION",
    ("GET", "/v1/candles/minutes/3"): "QUOTATION",
    ("GET", "/v1/candles/minutes/5"): "QUOTATION",
    ("GET", "/v1/candles/minutes/10"): "QUOTATION",
    ("GET", "/v1/candles/minutes/15"): "QUOTATION",
    ("GET", "/v1/candles/minutes/30"): "QUOTATION",
    ("GET", "/v1/candles/minutes/60"): "QUOTATION",
    ("GET", "/v1/candles/minutes/240"): "QUOTATION",
    ("GET", "/v1/candles/days"): "QUOTATION",
    ("GET", "/v1/candles/weeks"): "QUOTATION",
    ("GET", "/v1/candles/months"): "QUOTATION",

    # Ticker (현재가)
    ("GET", "/v1/ticker"): "QUOTATION",

    # Orderbook (호가)
    ("GET", "/v1/orderbook"): "QUOTATION",

    # Trades (체결)
    ("GET", "/v1/trades/ticks"): "QUOTATION",

    # ========== EXCHANGE API - ORDERS (주문, 초당 8회, 분당 200회) ==========
    ("POST", "/v1/orders"): "EXCHANGE_ORDER",      # 주문 생성
    ("DELETE", "/v1/order"): "EXCHANGE_ORDER",     # 주문 취소

    # ========== EXCHANGE API - NON-ORDERS (주문 외, 초당 30회, 분당 900회) ==========
    # Account (계좌)
    ("GET", "/v1/accounts"): "EXCHANGE_NON_ORDER",          # 전체 계좌 조회
    ("GET", "/v1/api_keys"): "EXCHANGE_NON_ORDER",          # API 키 리스트 조회

    # Orders 조회
    ("GET", "/v1/order"): "EXCHANGE_NON_ORDER",             # 개별 주문 조회
    ("GET", "/v1/orders"): "EXCHANGE_NON_ORDER",            # 주문 리스트 조회
    ("GET", "/v1/orders/chance"): "EXCHANGE_NON_ORDER",     # 주문 가능 정보
    ("GET", "/v1/orders/closed"): "EXCHANGE_NON_ORDER",     # 종료된 주문 조회 (신규)
    ("GET", "/v1/orders/open"): "EXCHANGE_NON_ORDER",       # 미체결 주문 조회 (신규)

    # Deposits (입금)
    ("GET", "/v1/deposits"): "EXCHANGE_NON_ORDER",          # 입금 리스트 조회
    ("GET", "/v1/deposit"): "EXCHANGE_NON_ORDER",           # 개별 입금 조회
    ("POST", "/v1/deposits/generate_coin_address"): "EXCHANGE_NON_ORDER",  # 입금 주소 생성
    ("GET", "/v1/deposits/coin_addresses"): "EXCHANGE_NON_ORDER",          # 전체 입금 주소 조회
    ("GET", "/v1/deposits/coin_address"): "EXCHANGE_NON_ORDER",            # 개별 입금 주소 조회
    ("POST", "/v1/deposits/krw"): "EXCHANGE_NON_ORDER",                    # 원화 입금

    # Withdrawals (출금)
    ("GET", "/v1/withdraws"): "EXCHANGE_NON_ORDER",         # 출금 리스트 조회
    ("GET", "/v1/withdraw"): "EXCHANGE_NON_ORDER",          # 개별 출금 조회
    ("GET", "/v1/withdraws/chance"): "EXCHANGE_NON_ORDER",  # 출금 가능 정보
    ("POST", "/v1/withdraws/coin"): "EXCHANGE_NON_ORDER",   # 코인 출금
    ("POST", "/v1/withdraws/krw"): "EXCHANGE_NON_ORDER",    # 원화 출금

    # Status (서비스 정보)
    ("GET", "/v1/status/wallet"): "EXCHANGE_NON_ORDER",     # 입출금 지갑 상태
}


def get_endpoint_category(method: str, endpoint: str) -> EndpointCategory:
    """
    엔드포인트의 카테고리 조회

    Args:
        method: HTTP 메서드 (GET, POST, DELETE 등)
        endpoint: API 엔드포인트 경로

    Returns:
        엔드포인트 카테고리

    Raises:
        KeyError: 알 수 없는 엔드포인트
    """
    key = (method.upper(), endpoint)
    if key not in UPBIT_ENDPOINT_CATEGORIES:
        raise KeyError(f"Unknown endpoint: {method} {endpoint}")
    return UPBIT_ENDPOINT_CATEGORIES[key]


def is_order_endpoint(method: str, endpoint: str) -> bool:
    """
    주문 관련 엔드포인트인지 판단

    Args:
        method: HTTP 메서드
        endpoint: API 엔드포인트 경로

    Returns:
        주문 엔드포인트 여부
    """
    try:
        category = get_endpoint_category(method, endpoint)
        return category == "EXCHANGE_ORDER"
    except KeyError:
        return False


def is_quotation_endpoint(method: str, endpoint: str) -> bool:
    """
    시세 조회 엔드포인트인지 판단

    Args:
        method: HTTP 메서드
        endpoint: API 엔드포인트 경로

    Returns:
        시세 조회 엔드포인트 여부
    """
    try:
        category = get_endpoint_category(method, endpoint)
        return category == "QUOTATION"
    except KeyError:
        return False
