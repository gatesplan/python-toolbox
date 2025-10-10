"""
Pair Module

Pair는 자산(asset)과 그 가치(value)를 하나의 쌍으로 표현하는 단위입니다.
거래 대상 자산과 그 교환 가치를 함께 관리하여 일관된 비율을 유지합니다.

PairStack은 같은 ticker의 Pair들을 스택으로 관리하며,
평단가가 유사한 Pair는 자동으로 병합됩니다.
"""

from financial_assets.pair.pair import Pair
from financial_assets.pair.pair_stack import PairStack

__all__ = ["Pair", "PairStack"]
