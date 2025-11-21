"""Financial Gateway Package.

거래소 및 시뮬레이션과의 통합 인터페이스 게이트웨이.
"""

__version__ = "0.0.1"

# Core Services
from .RequestFactory import RequestFactory
from .GatewayService import GatewayService

# Gateway Base Classes
from .gateways.base import BaseGateway, SpotMarketGatewayBase

# Gateway Implementations
from .gateways.binance_spot import BinanceSpotGateway
from .gateways.upbit_spot import UpbitSpotGateway

# financial-assets 객체 re-export
from financial_assets.symbol import Symbol
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_assets.stock_address import StockAddress
from financial_assets.order import SpotOrder
from financial_assets.constants import (
    OrderSide,
    OrderType,
    OrderStatus,
    TimeInForce,
    SelfTradePreventionMode
)

__all__ = [
    # Core Services
    "RequestFactory",
    "GatewayService",
    # Gateways
    "BaseGateway",
    "SpotMarketGatewayBase",
    "BinanceSpotGateway",
    "UpbitSpotGateway",
    # financial-assets objects
    "Symbol",
    "Token",
    "Pair",
    "StockAddress",
    "SpotOrder",
    # Constants
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "TimeInForce",
    "SelfTradePreventionMode",
]
