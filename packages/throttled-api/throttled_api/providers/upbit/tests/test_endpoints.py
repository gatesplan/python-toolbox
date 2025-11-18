"""
Upbit endpoints.py tests
"""
import pytest
from throttled_api.providers.upbit.endpoints import (
    get_endpoint_category,
    is_order_endpoint,
    is_quotation_endpoint,
)


class TestEndpointCategory:
    """엔드포인트 카테고리 조회 테스트"""

    def test_quotation_endpoints(self):
        """QUOTATION 엔드포인트 확인"""
        assert get_endpoint_category("GET", "/v1/market/all") == "QUOTATION"
        assert get_endpoint_category("GET", "/v1/ticker") == "QUOTATION"
        assert get_endpoint_category("GET", "/v1/candles/minutes/1") == "QUOTATION"
        assert get_endpoint_category("GET", "/v1/orderbook") == "QUOTATION"
        assert get_endpoint_category("GET", "/v1/trades/ticks") == "QUOTATION"

    def test_exchange_order_endpoints(self):
        """EXCHANGE_ORDER 엔드포인트 확인"""
        assert get_endpoint_category("POST", "/v1/orders") == "EXCHANGE_ORDER"
        assert get_endpoint_category("DELETE", "/v1/order") == "EXCHANGE_ORDER"

    def test_exchange_non_order_endpoints(self):
        """EXCHANGE_NON_ORDER 엔드포인트 확인"""
        assert get_endpoint_category("GET", "/v1/accounts") == "EXCHANGE_NON_ORDER"
        assert get_endpoint_category("GET", "/v1/order") == "EXCHANGE_NON_ORDER"
        assert get_endpoint_category("GET", "/v1/orders") == "EXCHANGE_NON_ORDER"
        assert get_endpoint_category("GET", "/v1/deposits") == "EXCHANGE_NON_ORDER"
        assert get_endpoint_category("GET", "/v1/withdraws") == "EXCHANGE_NON_ORDER"

    def test_unknown_endpoint(self):
        """알 수 없는 엔드포인트"""
        with pytest.raises(KeyError):
            get_endpoint_category("GET", "/v1/unknown")


class TestEndpointHelpers:
    """헬퍼 함수 테스트"""

    def test_is_order_endpoint(self):
        """주문 엔드포인트 판단"""
        assert is_order_endpoint("POST", "/v1/orders") is True
        assert is_order_endpoint("DELETE", "/v1/order") is True
        assert is_order_endpoint("GET", "/v1/order") is False
        assert is_order_endpoint("GET", "/v1/accounts") is False

    def test_is_quotation_endpoint(self):
        """시세 조회 엔드포인트 판단"""
        assert is_quotation_endpoint("GET", "/v1/ticker") is True
        assert is_quotation_endpoint("GET", "/v1/candles/days") is True
        assert is_quotation_endpoint("POST", "/v1/orders") is False
        assert is_quotation_endpoint("GET", "/v1/accounts") is False
