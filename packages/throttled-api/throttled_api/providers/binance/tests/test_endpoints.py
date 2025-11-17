"""
Endpoints weight tests
"""
import pytest
from throttled_api.providers.binance import endpoints


class TestEndpointWeights:
    """기본 엔드포인트 weight 테스트"""

    def test_ping_weight(self):
        """ping 엔드포인트 weight"""
        weight = endpoints.SPOT_ENDPOINT_WEIGHTS[("GET", "/api/v3/ping")]
        assert weight == 1

    def test_time_weight(self):
        """time 엔드포인트 weight"""
        weight = endpoints.SPOT_ENDPOINT_WEIGHTS[("GET", "/api/v3/time")]
        assert weight == 1

    def test_exchange_info_weight(self):
        """exchangeInfo 기본 weight (전체 조회)"""
        weight = endpoints.SPOT_ENDPOINT_WEIGHTS[("GET", "/api/v3/exchangeInfo")]
        assert weight == 20

    def test_depth_weight(self):
        """depth 기본 weight"""
        weight = endpoints.SPOT_ENDPOINT_WEIGHTS[("GET", "/api/v3/depth")]
        assert weight == 5

    def test_order_post_weight(self):
        """신규 주문 weight"""
        weight = endpoints.SPOT_ENDPOINT_WEIGHTS[("POST", "/api/v3/order")]
        assert weight == 1

    def test_account_weight(self):
        """계정 정보 weight"""
        weight = endpoints.SPOT_ENDPOINT_WEIGHTS[("GET", "/api/v3/account")]
        assert weight == 20


class TestDepthWeight:
    """depth 엔드포인트 limit별 weight 테스트"""

    def test_depth_limit_5(self):
        """limit=5"""
        assert endpoints.get_depth_weight(5) == 5

    def test_depth_limit_100(self):
        """limit=100"""
        assert endpoints.get_depth_weight(100) == 5

    def test_depth_limit_500(self):
        """limit=500"""
        assert endpoints.get_depth_weight(500) == 25

    def test_depth_limit_1000(self):
        """limit=1000"""
        assert endpoints.get_depth_weight(1000) == 50

    def test_depth_limit_5000(self):
        """limit=5000"""
        assert endpoints.get_depth_weight(5000) == 250

    def test_depth_limit_over(self):
        """limit > 5000"""
        assert endpoints.get_depth_weight(10000) == 250


class TestTicker24hrWeight:
    """ticker/24hr 엔드포인트 weight 테스트"""

    def test_single_symbol(self):
        """단일 symbol"""
        assert endpoints.get_ticker_24hr_weight(1) == 2

    def test_multiple_symbols_20(self):
        """20개 symbol"""
        assert endpoints.get_ticker_24hr_weight(20) == 40

    def test_all_symbols(self):
        """전체 symbol (symbol 파라미터 없음, 100 이상으로 간주)"""
        assert endpoints.get_ticker_24hr_weight(200) == 80


class TestTickerPriceWeight:
    """ticker/price 엔드포인트 weight 테스트"""

    def test_single_symbol(self):
        """단일 symbol"""
        assert endpoints.get_ticker_price_weight(1) == 2

    def test_all_symbols(self):
        """전체 symbol"""
        assert endpoints.get_ticker_price_weight(100) == 4


class TestTickerBookTickerWeight:
    """ticker/bookTicker 엔드포인트 weight 테스트"""

    def test_single_symbol(self):
        """단일 symbol"""
        assert endpoints.get_ticker_book_ticker_weight(1) == 2

    def test_all_symbols(self):
        """전체 symbol"""
        assert endpoints.get_ticker_book_ticker_weight(100) == 4


class TestOpenOrdersWeight:
    """openOrders 엔드포인트 weight 테스트"""

    def test_with_symbol(self):
        """symbol 파라미터 있음"""
        assert endpoints.get_open_orders_weight(True) == 6

    def test_without_symbol(self):
        """symbol 파라미터 없음 (전체 조회)"""
        assert endpoints.get_open_orders_weight(False) == 80


class TestExchangeInfoWeight:
    """exchangeInfo 엔드포인트 weight 테스트"""

    def test_with_symbol(self):
        """symbol 파라미터 있음"""
        assert endpoints.get_exchange_info_weight(True) == 2

    def test_without_symbol(self):
        """symbol 파라미터 없음 (전체 조회)"""
        assert endpoints.get_exchange_info_weight(False) == 20
