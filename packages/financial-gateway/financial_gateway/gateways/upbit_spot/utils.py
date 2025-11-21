"""Upbit Spot Gateway utilities"""


def get_krw_price_tick_size(price: float) -> float:
    """KRW 마켓의 가격대별 호가 단위 반환

    Args:
        price: 현재 가격 (KRW)

    Returns:
        호가 단위 (KRW)

    Reference:
        https://docs.upbit.com/docs/market-info-trade-price-detail
        2024년 1월 29일 기준
    """
    if price < 10:
        return 0.01
    elif price < 100:
        return 0.1
    elif price < 1_000:
        return 1
    elif price < 10_000:
        return 5
    elif price < 100_000:
        return 10
    elif price < 500_000:
        return 50
    elif price < 1_000_000:
        return 100
    elif price < 2_000_000:
        return 500
    else:
        return 1000


def get_btc_price_tick_size(price: float) -> float:
    """BTC 마켓의 호가 단위 반환

    Args:
        price: 현재 가격 (BTC)

    Returns:
        호가 단위 (BTC)

    Note:
        BTC 마켓은 0.00000001 BTC (1 satoshi) 단위
    """
    return 0.00000001


def get_usdt_price_tick_size(price: float) -> float:
    """USDT 마켓의 호가 단위 반환

    Args:
        price: 현재 가격 (USDT)

    Returns:
        호가 단위 (USDT)

    Note:
        USDT 마켓은 0.0001 USDT 단위
    """
    return 0.0001


# 마켓별 최소 주문금액
MIN_ORDER_VALUES = {
    "KRW": 5000.0,       # 5,000 KRW
    "BTC": 0.00005,      # 0.00005 BTC
    "USDT": 0.5,         # 0.5 USDT
}


# 마켓별 수량 단위 (기본값)
QTY_STEP_SIZES = {
    "KRW": 0.00000001,   # 8자리
    "BTC": 0.00000001,   # 8자리
    "USDT": 0.00000001,  # 8자리
}
