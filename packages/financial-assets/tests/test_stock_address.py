"""Tests for StockAddress class"""

import pytest
from financial_assets.stock_address import StockAddress
from financial_assets.symbol import Symbol


class TestStockAddressBasic:
    """StockAddress 기본 기능 테스트"""

    def test_initialization(self):
        """StockAddress 초기화"""
        address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1h"
        )
        assert address.archetype == "crypto"
        assert address.exchange == "binance"
        assert address.tradetype == "spot"
        assert address.base == "btc"
        assert address.quote == "usdt"
        assert address.timeframe == "1h"

    def test_to_filename(self):
        """파일명 형식 변환"""
        address = StockAddress(
            archetype="stock",
            exchange="nasdaq",
            tradetype="spot",
            base="aapl",
            quote="usd",
            timeframe="1d"
        )
        assert address.to_filename() == "stock-nasdaq-spot-aapl-usd-1d"

    def test_to_tablename(self):
        """테이블명 형식 변환"""
        address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="futures",
            base="btc",
            quote="usd",
            timeframe="15m"
        )
        assert address.to_tablename() == "crypto_binance_futures_btc_usd_15m"

    def test_from_filename(self):
        """파일명에서 StockAddress 생성"""
        address = StockAddress.from_filename("stock-nyse-spot-tsla-usd-1d")
        assert address.archetype == "stock"
        assert address.exchange == "nyse"
        assert address.tradetype == "spot"
        assert address.base == "tsla"
        assert address.quote == "usd"
        assert address.timeframe == "1d"

    def test_from_filename_with_extension(self):
        """확장자 포함 파일명에서 생성"""
        address = StockAddress.from_filename("crypto-binance-spot-eth-usdt-1h.parquet")
        assert address.base == "eth"
        assert address.quote == "usdt"

    def test_from_filename_invalid_format(self):
        """잘못된 파일명 형식"""
        with pytest.raises(ValueError, match="Invalid filename format"):
            StockAddress.from_filename("invalid-format")


class TestStockAddressToSymbol:
    """StockAddress.to_symbol() 테스트"""

    def test_to_symbol_returns_symbol_object(self):
        """Symbol 객체 반환"""
        address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1h"
        )
        symbol = address.to_symbol()
        assert isinstance(symbol, Symbol)

    def test_to_symbol_correct_base_quote(self):
        """올바른 base/quote 설정"""
        address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="eth",
            quote="btc",
            timeframe="1h"
        )
        symbol = address.to_symbol()
        assert symbol.base == "ETH"
        assert symbol.quote == "BTC"

    def test_to_symbol_uppercase_conversion(self):
        """소문자 → 대문자 변환"""
        address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="matic",
            quote="usdt",
            timeframe="1h"
        )
        symbol = address.to_symbol()
        assert symbol.base == "MATIC"
        assert symbol.quote == "USDT"

    def test_to_symbol_slash_format(self):
        """슬래시 형식 출력"""
        address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1h"
        )
        symbol = address.to_symbol()
        assert symbol.to_slash() == "BTC/USDT"

    def test_to_symbol_dash_format(self):
        """하이픈 형식 출력"""
        address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1h"
        )
        symbol = address.to_symbol()
        assert symbol.to_dash() == "BTC-USDT"

    def test_to_symbol_compact_format(self):
        """compact 형식 출력"""
        address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1h"
        )
        symbol = address.to_symbol()
        assert symbol.to_compact() == "BTCUSDT"

    def test_to_symbol_multiple_calls_same_result(self):
        """여러 번 호출해도 동일한 결과"""
        address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1h"
        )
        symbol1 = address.to_symbol()
        symbol2 = address.to_symbol()
        assert symbol1 == symbol2

    def test_to_symbol_stock_address(self):
        """주식 주소에서 Symbol 생성"""
        address = StockAddress(
            archetype="stock",
            exchange="nasdaq",
            tradetype="spot",
            base="aapl",
            quote="usd",
            timeframe="1d"
        )
        symbol = address.to_symbol()
        assert symbol.to_slash() == "AAPL/USD"


class TestStockAddressIntegration:
    """StockAddress 통합 테스트"""

    def test_roundtrip_filename_to_symbol(self):
        """파일명 → StockAddress → Symbol 변환"""
        address = StockAddress.from_filename("crypto-binance-spot-btc-usdt-1h")
        symbol = address.to_symbol()
        assert symbol.to_slash() == "BTC/USDT"

    def test_symbol_equality_from_different_addresses(self):
        """다른 거래소지만 같은 심볼"""
        address1 = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1h"
        )
        address2 = StockAddress(
            archetype="crypto",
            exchange="coinbase",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1d"
        )
        symbol1 = address1.to_symbol()
        symbol2 = address2.to_symbol()
        assert symbol1 == symbol2  # 거래소/시간프레임 다르지만 심볼은 같음

    def test_symbol_inequality_different_pairs(self):
        """다른 거래쌍은 다른 심볼"""
        address1 = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="btc",
            quote="usdt",
            timeframe="1h"
        )
        address2 = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="eth",
            quote="usdt",
            timeframe="1h"
        )
        symbol1 = address1.to_symbol()
        symbol2 = address2.to_symbol()
        assert symbol1 != symbol2
