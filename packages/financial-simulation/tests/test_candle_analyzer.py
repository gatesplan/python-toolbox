import pytest
import sys
from pathlib import Path

package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim.Core import CandleAnalyzer
from financial_assets.price import Price


class TestCandleAnalyzer:

    def test_classify_zone_body(self):
        # body 범위 (o=100, c=110)
        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        result = CandleAnalyzer.classify_zone(price, 105.0)
        assert result == "body"

        result = CandleAnalyzer.classify_zone(price, 100.0)
        assert result == "body"

        result = CandleAnalyzer.classify_zone(price, 110.0)
        assert result == "body"

    def test_classify_zone_head(self):
        # head 범위 (bodytop=110, h=120)
        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        result = CandleAnalyzer.classify_zone(price, 115.0)
        assert result == "head"

        result = CandleAnalyzer.classify_zone(price, 120.0)
        assert result == "head"

    def test_classify_zone_tail(self):
        # tail 범위 (l=90, bodybottom=100)
        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        result = CandleAnalyzer.classify_zone(price, 95.0)
        assert result == "tail"

        result = CandleAnalyzer.classify_zone(price, 90.0)
        assert result == "tail"

    def test_classify_zone_none(self):
        # 범위 밖
        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        result = CandleAnalyzer.classify_zone(price, 130.0)
        assert result == "none"

        result = CandleAnalyzer.classify_zone(price, 80.0)
        assert result == "none"

    def test_classify_zone_boundary(self):
        # 경계값 정확한 테스트
        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        # bodybottom 경계
        assert CandleAnalyzer.classify_zone(price, 99.9) == "tail"
        assert CandleAnalyzer.classify_zone(price, 100.0) == "body"

        # bodytop 경계
        assert CandleAnalyzer.classify_zone(price, 110.0) == "body"
        assert CandleAnalyzer.classify_zone(price, 110.1) == "head"
