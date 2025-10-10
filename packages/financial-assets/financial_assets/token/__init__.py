"""
Token Module

Token은 거래 가능한 자산을 표현하는 가장 기본적인 단위입니다.
특정 심볼(symbol)과 수량(amount)을 가지며, 역할 중립적으로 설계됩니다.
"""

from financial_assets.token.token import Token

__all__ = ["Token"]
