"""Tests for SpotTrade module."""

import pytest
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.constants import OrderSide
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_assets.stock_address import StockAddress


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


class TestOrderSide:
    """OrderSide enum 테스트"""

    def test_all_spot_sides_exist(self):
        """모든 OrderSide 값이 존재하는지 확인"""
        assert OrderSide.BUY
        assert OrderSide.SELL

    def test_spot_side_equality(self):
        """OrderSide enum 동등성 비교"""
        side = OrderSide.BUY
        assert side == OrderSide.BUY
        assert side != OrderSide.SELL

    def test_spot_side_values(self):
        """OrderSide enum 값 확인"""
        assert OrderSide.BUY.value == "buy"
        assert OrderSide.SELL.value == "sell"


class TestSpotTradeCreation:
    """SpotTrade 객체 생성 테스트"""

    def test_basic_spot_trade_creation(self):
        """기본 SpotTrade 객체 생성"""
        trade = create_spot_trade(
            trade_id="trade-123",
            side=OrderSide.BUY,
            asset_amount=1.5,
            value_amount=75000.0,
            asset_symbol="BTC",
            value_symbol="USD",
        )

        assert trade.stock_address.base == "btc"
        assert trade.stock_address.quote == "usd"
        assert trade.trade_id == "trade-123"
        assert trade.side == OrderSide.BUY
        assert trade.pair.get_asset() == 1.5
        assert trade.pair.get_value() == 75000.0
        assert trade.timestamp == 1234567890

    def test_spot_trade_with_all_sides(self):
        """모든 OrderSide로 SpotTrade 객체 생성"""
        for side in [OrderSide.BUY, OrderSide.SELL]:
            trade = create_spot_trade(
                trade_id=f"trade-{side.value}",
                side=side,
                asset_amount=1.0,
                value_amount=50000.0,
                asset_symbol="BTC",
                value_symbol="USD",
            )
            assert trade.side == side


class TestSpotTradeImmutability:
    """Trade 불변성 테스트"""

    def test_trade_is_frozen(self):
        """Trade 객체는 frozen이어서 수정 불가능"""
        trade = create_spot_trade(
            trade_id="trade-frozen",
            side=OrderSide.BUY,
            asset_amount=1.0,
            value_amount=50000.0,
        )

        # 모든 필드 수정 시도는 에러를 발생시켜야 함
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            trade.trade_id = "modified"

        with pytest.raises(Exception):
            trade.side = OrderSide.SELL

        with pytest.raises(Exception):
            trade.timestamp = 9999999999


class TestSpotTradeIntegration:
    """Trade와 기존 모듈 통합 테스트"""

    def test_pair_integration(self):
        """Pair를 통한 거래 정보 접근"""
        trade = create_spot_trade(
            trade_id="trade-pair",
            side=OrderSide.BUY,
            asset_amount=2.0,
            value_amount=100000.0,
            asset_symbol="BTC",
            value_symbol="USD",
        )

        # Pair의 기능 활용
        assert trade.pair.get_asset() == 2.0
        assert trade.pair.get_value() == 100000.0
        assert trade.pair.mean_value() == 50000.0

    def test_stock_address_integration(self):
        """StockAddress를 통한 거래 특정"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="upbit",
            tradetype="spot",
            base="eth",
            quote="krw",
            timeframe="1h",
        )

        trade = create_spot_trade(
            trade_id="trade-eth",
            side=OrderSide.BUY,
            asset_amount=10.0,
            value_amount=30000000.0,
            asset_symbol="ETH",
            value_symbol="KRW",
            stock_address=stock_address,
        )

        assert trade.stock_address.exchange == "upbit"
        assert trade.stock_address.base == "eth"
        assert trade.stock_address.quote == "krw"
        assert trade.stock_address.timeframe == "1h"


class TestSpotTradeStringRepresentation:
    """Trade 문자열 표현 테스트"""

    def test_trade_str(self):
        """Trade __str__ 테스트"""
        trade = create_spot_trade(
            trade_id="trade-str",
            side=OrderSide.SELL,
            asset_amount=0.5,
            value_amount=25000.0,
        )

        trade_str = str(trade)
        assert "trade-str" in trade_str
        assert "SELL" in trade_str or "sell" in trade_str.lower()

    def test_trade_repr(self):
        """Trade __repr__ 테스트"""
        trade = create_spot_trade(
            trade_id="trade-repr",
            side=OrderSide.BUY,
            asset_amount=1.0,
            value_amount=50000.0,
        )

        trade_repr = repr(trade)
        assert "SpotTrade" in trade_repr
        assert "trade-repr" in trade_repr


class TestSpotTradeFee:
    """Trade fee 필드 테스트"""

    def test_trade_with_fee(self):
        """Fee 정보를 포함한 Trade 생성"""
        fee = Token("USD", 0.5)
        trade = create_spot_trade(
            trade_id="trade-with-fee",
            side=OrderSide.BUY,
            asset_amount=1.0,
            value_amount=50000.0,
            fee=fee,
        )

        assert trade.fee is not None
        assert trade.fee.symbol == "USD"
        assert trade.fee.amount == 0.5

    def test_trade_without_fee_default(self):
        """Fee를 명시하지 않으면 None (하위 호환성)"""
        trade = create_spot_trade(
            trade_id="trade-no-fee",
            side=OrderSide.SELL,
            asset_amount=0.5,
            value_amount=25000.0,
        )

        assert trade.fee is None

    def test_trade_with_different_currency_fee(self):
        """거래 통화와 다른 통화의 Fee"""
        fee = Token("KRW", 7000.0)
        trade = create_spot_trade(
            trade_id="trade-krw-fee",
            side=OrderSide.BUY,
            asset_amount=0.1,
            value_amount=7000000.0,
            asset_symbol="BTC",
            value_symbol="KRW",
            fee=fee,
        )

        assert trade.fee.symbol == "KRW"
        assert trade.fee.amount == 7000.0

    def test_trade_fee_immutability(self):
        """Fee 포함해도 불변성 유지"""
        fee = Token("USD", 1.0)
        trade = create_spot_trade(
            trade_id="trade-immutable-fee",
            side=OrderSide.BUY,
            asset_amount=1.0,
            value_amount=50000.0,
            fee=fee,
        )

        # fee 필드 수정 시도는 에러
        with pytest.raises(Exception):
            trade.fee = None

    def test_trade_repr_includes_fee(self):
        """__repr__에 fee 포함"""
        fee = Token("USD", 0.25)
        trade = create_spot_trade(
            trade_id="trade-repr-fee",
            side=OrderSide.BUY,
            asset_amount=1.0,
            value_amount=50000.0,
            fee=fee,
        )

        trade_repr = repr(trade)
        assert "fee=" in trade_repr
