# BalanceService

계정 정보 조회 Service. 잔고 정보를 조회한다.

_response_parser: ResponseParser
_api_executor: APICallExecutor

__init__(response_parser: ResponseParser, api_executor: APICallExecutor) -> None
    Core 계층 의존성 주입. RequestConverter는 불필요 (간단한 요청).

get_balance(request: BalanceRequest) -> BalanceResponse
    raise BinanceAPIError
    현재 잔고 조회.
    1. APICallExecutor.get_account_info() → API response
    2. ResponseParser.parse_balance_response(response) → BalanceResponse
