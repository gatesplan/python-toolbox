import pytest
import sys
from pathlib import Path

package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim.Core import SlippageCalculator
from financial_assets.price import Price
from financial_assets.constants import OrderSide


class TestSlippageCalculator:

    def test_calculate_range_buy(self):
        # BUY는 head 범위 (bodytop ~ h)
        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        range_min, range_max = SlippageCalculator.calculate_range(price, OrderSide.BUY)

        assert range_min == 110.0  # bodytop
        assert range_max == 120.0  # h

    def test_calculate_range_sell(self):
        # SELL은 tail 범위 (l ~ bodybottom)
        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        range_min, range_max = SlippageCalculator.calculate_range(price, OrderSide.SELL)

        assert range_min == 90.0   # l
        assert range_max == 100.0  # bodybottom

    def test_calculate_range_invalid_side(self):
        # Side enum이 아닌 값 전달 시 AttributeError
        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        with pytest.raises(AttributeError):
            SlippageCalculator.calculate_range(price, "INVALID")
