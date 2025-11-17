"""
Binance Spot API 엔드포인트별 REQUEST_WEIGHT 정의

공식 문서: https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md
최신 weight 정보는 공식 문서에서 확인 필요
"""
from typing import Dict, Tuple


# (method, endpoint) -> weight
# endpoint는 경로 파라미터를 제외한 base path
SPOT_ENDPOINT_WEIGHTS: Dict[Tuple[str, str], int] = {
    # ========== General endpoints ==========
    ("GET", "/api/v3/ping"): 1,
    ("GET", "/api/v3/time"): 1,
    ("GET", "/api/v3/exchangeInfo"): 20,  # symbol 파라미터 없을 때, 있으면 2

    # ========== Market Data endpoints ==========
    # depth - limit에 따라 weight 다름 (기본값: limit=100 -> weight=5)
    ("GET", "/api/v3/depth"): 5,  # limit별 weight는 get_depth_weight() 참조

    ("GET", "/api/v3/trades"): 25,
    ("GET", "/api/v3/historicalTrades"): 25,
    ("GET", "/api/v3/aggTrades"): 2,
    ("GET", "/api/v3/klines"): 2,
    ("GET", "/api/v3/uiKlines"): 2,
    ("GET", "/api/v3/avgPrice"): 2,

    # ticker - symbol 파라미터에 따라 다름
    ("GET", "/api/v3/ticker/24hr"): 2,  # 단일 symbol, 전체는 80
    ("GET", "/api/v3/ticker/tradingDay"): 4,  # 단일 symbol, 전체는 80
    ("GET", "/api/v3/ticker/price"): 2,  # 단일 symbol, 전체는 4
    ("GET", "/api/v3/ticker/bookTicker"): 2,  # 단일 symbol, 전체는 4
    ("GET", "/api/v3/ticker"): 4,

    # ========== Trading endpoints ==========
    ("POST", "/api/v3/order"): 1,
    ("POST", "/api/v3/order/test"): 1,
    ("GET", "/api/v3/order"): 4,
    ("DELETE", "/api/v3/order"): 1,
    ("DELETE", "/api/v3/openOrders"): 1,
    ("POST", "/api/v3/order/cancelReplace"): 1,

    # Order Lists (OCO, OTO, OTOCO)
    ("POST", "/api/v3/orderList/oco"): 1,
    ("POST", "/api/v3/orderList/oto"): 1,
    ("POST", "/api/v3/orderList/otoco"): 1,
    ("DELETE", "/api/v3/orderList"): 1,
    ("GET", "/api/v3/orderList"): 4,

    # SOR (Smart Order Routing)
    ("POST", "/api/v3/sor/order"): 1,
    ("POST", "/api/v3/sor/order/test"): 1,

    # ========== Account endpoints ==========
    ("GET", "/api/v3/openOrders"): 6,  # 단일 symbol, 전체는 80
    ("GET", "/api/v3/allOrders"): 20,
    ("GET", "/api/v3/allOrderList"): 20,
    ("GET", "/api/v3/openOrderList"): 6,
    ("GET", "/api/v3/myTrades"): 20,
    ("GET", "/api/v3/myAllocations"): 20,
    ("GET", "/api/v3/account"): 20,
    ("GET", "/api/v3/account/commission"): 20,
    ("GET", "/api/v3/rateLimit/order"): 40,
    ("GET", "/api/v3/myPreventedMatches"): 1,

    # ========== User Data Stream endpoints ==========
    ("POST", "/api/v3/userDataStream"): 2,
    ("PUT", "/api/v3/userDataStream"): 2,
    ("DELETE", "/api/v3/userDataStream"): 2,
}


def get_depth_weight(limit: int) -> int:
    """
    /api/v3/depth 엔드포인트의 limit에 따른 weight 계산

    2023년 8월 이후 weight가 약 2배 증가
    https://github.com/binance/binance-spot-api-docs/commit/15c50262ab9f5b5a8d3b072a41bbb96ac4da1016

    Args:
        limit: orderbook depth limit

    Returns:
        weight 값
    """
    if limit <= 100:
        return 5
    elif limit <= 500:
        return 25
    elif limit <= 1000:
        return 50
    elif limit <= 5000:
        return 250
    else:
        return 250  # 5000 초과는 5000으로 제한됨


def get_ticker_24hr_weight(symbols: int = 1) -> int:
    """
    /api/v3/ticker/24hr 엔드포인트의 symbol 개수에 따른 weight 계산

    Args:
        symbols: 조회할 symbol 개수 (파라미터 없으면 전체)

    Returns:
        weight 값
    """
    if symbols == 1:
        return 2
    elif symbols <= 20:
        return 40
    elif symbols <= 100:
        return 40
    else:
        return 80  # 전체 조회


def get_ticker_price_weight(symbols: int = 1) -> int:
    """
    /api/v3/ticker/price 엔드포인트의 symbol 개수에 따른 weight 계산

    Args:
        symbols: 조회할 symbol 개수

    Returns:
        weight 값
    """
    return 2 if symbols == 1 else 4


def get_ticker_book_ticker_weight(symbols: int = 1) -> int:
    """
    /api/v3/ticker/bookTicker 엔드포인트의 symbol 개수에 따른 weight 계산

    Args:
        symbols: 조회할 symbol 개수

    Returns:
        weight 값
    """
    return 2 if symbols == 1 else 4


def get_open_orders_weight(has_symbol: bool) -> int:
    """
    /api/v3/openOrders 엔드포인트의 symbol 파라미터 유무에 따른 weight 계산

    Args:
        has_symbol: symbol 파라미터 존재 여부

    Returns:
        weight 값
    """
    return 6 if has_symbol else 80


def get_exchange_info_weight(has_symbol: bool) -> int:
    """
    /api/v3/exchangeInfo 엔드포인트의 symbol 파라미터 유무에 따른 weight 계산

    Args:
        has_symbol: symbol 파라미터 존재 여부

    Returns:
        weight 값
    """
    return 2 if has_symbol else 20
