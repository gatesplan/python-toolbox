"""
Upbit API Exceptions
"""


class UnknownEndpointError(Exception):
    """
    알 수 없는 Upbit 엔드포인트

    endpoints.py에 정의되지 않은 엔드포인트 호출 시 발생
    """

    pass


class RateLimitExceededError(Exception):
    """
    Rate limit 초과 (429 Too Many Requests)

    Upbit 서버에서 429 응답을 받았을 때 발생
    """

    pass
