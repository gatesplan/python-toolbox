"""CurrentBalanceResponse - 계정 잔고 조회 응답."""

from dataclasses import dataclass, field

from financial_assets.token import Token

from .base_response import BaseResponse


@dataclass
class CurrentBalanceResponse(BaseResponse):
    """계정 잔고 조회 요청에 대한 응답.

    토큰 심볼을 키로, 보유 수량을 값으로 하는 잔고 맵을 제공한다.
    """

    # 결과 데이터
    result: dict[str, Token] = field(default_factory=dict)  # {symbol: Token}
