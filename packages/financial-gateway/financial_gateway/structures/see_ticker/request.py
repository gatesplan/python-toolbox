# see_ticker Request structure.

from __future__ import annotations
from dataclasses import dataclass

from financial_assets.stock_address import StockAddress
from financial_gateway.structures.base import BaseRequest


@dataclass
class SeeTickerRequest(BaseRequest):
    # 조회 대상
    address: StockAddress
