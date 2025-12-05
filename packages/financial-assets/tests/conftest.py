"""Pytest fixtures for financial-assets tests."""

import pytest
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.constants import OrderSide
from financial_assets.stock_address import StockAddress
from financial_assets.pair import Pair
from financial_assets.token import Token


@pytest.fixture
def stock_address():
    """기본 stock address fixture."""
    return StockAddress(
        archetype="crypto",
        exchange="binance",
        tradetype="spot",
        base="btc",
        quote="usdt",
        timeframe="1d",
    )


@pytest.fixture
def buy_order(stock_address):
    """기본 BUY 주문 fixture."""
    return SpotOrder(
        order_id="order-123",
        stock_address=stock_address,
        side=OrderSide.BUY,
        order_type="limit",
        price=50000.0,
        amount=1.0,
        timestamp=1234567890,
    )


@pytest.fixture
def sell_order(stock_address):
    """기본 SELL 주문 fixture."""
    return SpotOrder(
        order_id="order-456",
        stock_address=stock_address,
        side=OrderSide.SELL,
        order_type="limit",
        price=50000.0,
        amount=1.0,
        timestamp=1234567890,
    )


def create_spot_trade(
    trade_id: str,
    side: OrderSide,
    asset_amount: float,
    value_amount: float,
    asset_symbol: str = "BTC",
    value_symbol: str = "USDT",
    price: float = None,
    timestamp: int = 1234567890,
    stock_address: StockAddress = None,
    fee: Token = None,
) -> SpotTrade:
    """SpotTrade 생성 헬퍼 함수."""
    if stock_address is None:
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base=asset_symbol.lower(),
            quote=value_symbol.lower(),
            timeframe="1d",
        )

    if price is None:
        price = value_amount / asset_amount if asset_amount > 0 else 0.0

    order = SpotOrder(
        order_id=f"order-{trade_id}",
        stock_address=stock_address,
        side=side,
        order_type="limit",
        price=price,
        amount=asset_amount,
        timestamp=timestamp,
    )

    pair = Pair(
        asset=Token(asset_symbol, asset_amount),
        value=Token(value_symbol, value_amount),
    )

    return SpotTrade(
        trade_id=trade_id,
        order=order,
        pair=pair,
        timestamp=timestamp,
        fee=fee,
    )
