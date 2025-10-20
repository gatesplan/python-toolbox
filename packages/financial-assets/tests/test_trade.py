"""Tests for SpotTrade module."""

import pytest
from financial_assets.trade import SpotTrade, SpotSide
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_assets.stock_address import StockAddress


class TestSpotSide:
    """SpotSide enum 테스트"""

    def test_all_spot_sides_exist(self):
        """모든 SpotSide 값이 존재하는지 확인"""
        assert SpotSide.BUY
        assert SpotSide.SELL

    def test_spot_side_equality(self):
        """SpotSide enum 동등성 비교"""
        side = SpotSide.BUY
        assert side == SpotSide.BUY
        assert side != SpotSide.SELL

    def test_spot_side_values(self):
        """SpotSide enum 값 확인"""
        assert SpotSide.BUY.value == "buy"
        assert SpotSide.SELL.value == "sell"


class TestSpotTradeCreation:
    """SpotTrade 객체 생성 테스트"""

    def test_basic_spot_trade_creation(self):
        """기본 SpotTrade 객체 생성"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 1.5), value=Token("USD", 75000.0))

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-123",
            fill_id="fill-456",
            side=SpotSide.BUY,
            pair=pair,
            timestamp=1234567890,
        )

        assert trade.stock_address == stock_address
        assert trade.trade_id == "trade-123"
        assert trade.fill_id == "fill-456"
        assert trade.side == SpotSide.BUY
        assert trade.pair == pair
        assert trade.timestamp == 1234567890

    def test_spot_trade_with_all_sides(self):
        """모든 SpotSide로 SpotTrade 객체 생성"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 1.0), value=Token("USD", 50000.0))

        for side in [SpotSide.BUY, SpotSide.SELL]:
            trade = SpotTrade(
                stock_address=stock_address,
                trade_id=f"trade-{side.value}",
                fill_id=f"fill-{side.value}",
                side=side,
                pair=pair,
                timestamp=1234567890,
            )
            assert trade.side == side


class TestSpotTradeImmutability:
    """Trade 불변성 테스트"""

    def test_trade_is_frozen(self):
        """Trade 객체는 frozen이어서 수정 불가능"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 1.0), value=Token("USD", 50000.0))

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-frozen",
            fill_id="fill-frozen",
            side=SpotSide.BUY,
            pair=pair,
            timestamp=1234567890,
        )

        # 모든 필드 수정 시도는 에러를 발생시켜야 함
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            trade.trade_id = "modified"

        with pytest.raises(Exception):
            trade.side = SpotSide.SELL

        with pytest.raises(Exception):
            trade.timestamp = 9999999999


class TestSpotTradeIntegration:
    """Trade와 기존 모듈 통합 테스트"""

    def test_pair_integration(self):
        """Pair를 통한 거래 정보 접근"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 2.0), value=Token("USD", 100000.0))

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-pair",
            fill_id="fill-pair",
            side=SpotSide.BUY,
            pair=pair,
            timestamp=1234567890,
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

        pair = Pair(asset=Token("ETH", 10.0), value=Token("KRW", 30000000.0))

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-eth",
            fill_id="fill-eth",
            side=SpotSide.BUY,
            pair=pair,
            timestamp=1234567890,
        )

        assert trade.stock_address.exchange == "upbit"
        assert trade.stock_address.base == "eth"
        assert trade.stock_address.quote == "krw"
        assert trade.stock_address.timeframe == "1h"


class TestSpotTradeStringRepresentation:
    """Trade 문자열 표현 테스트"""

    def test_trade_str(self):
        """Trade __str__ 테스트"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 0.5), value=Token("USD", 25000.0))

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-str",
            fill_id="fill-str",
            side=SpotSide.SELL,
            pair=pair,
            timestamp=1234567890,
        )

        trade_str = str(trade)
        assert "trade-str" in trade_str
        assert "SELL" in trade_str or "sell" in trade_str.lower()

    def test_trade_repr(self):
        """Trade __repr__ 테스트"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 1.0), value=Token("USD", 50000.0))

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-repr",
            fill_id="fill-repr",
            side=SpotSide.BUY,
            pair=pair,
            timestamp=1234567890,
        )

        trade_repr = repr(trade)
        assert "SpotTrade" in trade_repr
        assert "trade-repr" in trade_repr
        assert "fill-repr" in trade_repr


class TestSpotTradeFee:
    """Trade fee 필드 테스트"""

    def test_trade_with_fee(self):
        """Fee 정보를 포함한 Trade 생성"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 1.0), value=Token("USD", 50000.0))
        fee = Token("USD", 0.5)

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-with-fee",
            fill_id="fill-with-fee",
            side=SpotSide.BUY,
            pair=pair,
            timestamp=1234567890,
            fee=fee,
        )

        assert trade.fee is not None
        assert trade.fee.symbol == "USD"
        assert trade.fee.amount == 0.5

    def test_trade_without_fee_default(self):
        """Fee를 명시하지 않으면 None (하위 호환성)"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 0.5), value=Token("USD", 25000.0))

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-no-fee",
            fill_id="fill-no-fee",
            side=SpotSide.SELL,
            pair=pair,
            timestamp=1234567890,
            # fee 파라미터 생략
        )

        assert trade.fee is None

    def test_trade_with_different_currency_fee(self):
        """거래 통화와 다른 통화의 Fee"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="upbit",
            tradetype="spot",
            base="btc",
            quote="krw",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 0.1), value=Token("KRW", 7000000.0))
        fee = Token("KRW", 7000.0)

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-krw-fee",
            fill_id="fill-krw-fee",
            side=SpotSide.BUY,
            pair=pair,
            timestamp=1234567890,
            fee=fee,
        )

        assert trade.fee.symbol == "KRW"
        assert trade.fee.amount == 7000.0

    def test_trade_fee_immutability(self):
        """Fee 포함해도 불변성 유지"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 1.0), value=Token("USD", 50000.0))
        fee = Token("USD", 1.0)

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-immutable-fee",
            fill_id="fill-immutable-fee",
            side=SpotSide.BUY,
            pair=pair,
            timestamp=1234567890,
            fee=fee,
        )

        # fee 필드 수정 시도는 에러
        with pytest.raises(Exception):
            trade.fee = None

    def test_trade_repr_includes_fee(self):
        """__repr__에 fee 포함"""
        stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usd",
            timeframe="1d",
        )

        pair = Pair(asset=Token("BTC", 1.0), value=Token("USD", 50000.0))
        fee = Token("USD", 0.25)

        trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-repr-fee",
            fill_id="fill-repr-fee",
            side=SpotSide.BUY,
            pair=pair,
            timestamp=1234567890,
            fee=fee,
        )

        trade_repr = repr(trade)
        assert "fee=" in trade_repr
