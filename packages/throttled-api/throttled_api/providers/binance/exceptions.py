"""
Binance provider exceptions
"""


class BinanceThrottlerError(Exception):
    """Binance Throttler 기본 예외"""
    pass


class UnknownEndpointError(BinanceThrottlerError):
    """
    알 수 없는 엔드포인트 예외

    endpoints.py에 weight가 정의되지 않은 엔드포인트 사용 시 발생
    """

    def __init__(self, method: str, endpoint: str):
        self.method = method
        self.endpoint = endpoint
        super().__init__(
            f"Unknown endpoint: {method} {endpoint}\n"
            f"This endpoint is not configured in endpoints.py.\n"
            f"Please add the endpoint weight or set allow_unknown_endpoints=True.\n"
            f"Refer to: https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md"
        )
