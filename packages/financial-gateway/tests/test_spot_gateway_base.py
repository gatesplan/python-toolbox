"""SpotMarketGatewayBase 테스트"""

import os
import pytest
from financial_gateway.spot import SpotMarketGatewayBase


class ConcreteSpotGateway(SpotMarketGatewayBase):
    """테스트용 구체 클래스 (모든 추상 메서드 구현)"""

    def request_limit_buy_order(self, request):
        return {}

    def request_limit_sell_order(self, request):
        return {}

    def request_market_buy_order(self, request):
        return {}

    def request_market_sell_order(self, request):
        return {}

    def request_stop_limit_buy_order(self, request):
        return {}

    def request_stop_limit_sell_order(self, request):
        return {}

    def request_stop_market_buy_order(self, request):
        return {}

    def request_stop_market_sell_order(self, request):
        return {}

    def request_close_order(self, request):
        return {}

    def request_modify_order(self, request):
        return {}

    def request_order_current_state(self, request):
        return {}

    def request_order_list(self, request):
        return {}

    def request_trade_info(self, request):
        return {}

    def request_recent_trades(self, request):
        return {}

    def request_current_balance(self, request):
        return {}

    def request_price_data(self, request):
        return {}

    def request_orderbook(self, request):
        return {}

    def request_ticker(self, request):
        return {}

    def request_available_markets(self, request):
        return {}

    def request_fee_info(self, request):
        return {}

    def request_server_status(self, request):
        return {}


class TestSpotMarketGatewayBase:
    """SpotMarketGatewayBase 테스트 케이스"""

    def test_init_simulation_gateway_without_provider(self):
        """Simulation gateway는 provider 없이 초기화 가능"""
        gateway = ConcreteSpotGateway(
            gateway_name="simulation",
            is_realworld_gateway=False
        )

        assert gateway.gateway_name == "simulation"
        assert gateway.is_realworld_gateway is False
        assert gateway._api_key is None
        assert gateway._api_secret is None

    def test_init_real_world_gateway_without_provider_raises_error(self):
        """Real world gateway는 provider 필수"""
        with pytest.raises(ValueError, match="provider"):
            ConcreteSpotGateway(
                gateway_name="binance",
                is_realworld_gateway=True
                # provider 누락
            )

    def test_init_real_world_gateway_validates_api_keys(self):
        """Real world gateway는 API 키 검증 수행"""
        # 환경변수 설정
        os.environ["TEST_SPOT_API_KEY"] = "test_key"
        os.environ["TEST_SPOT_API_SECRET"] = "test_secret"

        try:
            gateway = ConcreteSpotGateway(
                gateway_name="test",
                is_realworld_gateway=True,
                provider="TEST"
            )

            assert gateway.gateway_name == "test"
            assert gateway.is_realworld_gateway is True
            assert gateway._api_key == "test_key"
            assert gateway._api_secret == "test_secret"
        finally:
            # 환경변수 정리
            del os.environ["TEST_SPOT_API_KEY"]
            del os.environ["TEST_SPOT_API_SECRET"]

    def test_init_real_world_gateway_missing_api_key_raises_error(self):
        """API Key가 없으면 EnvironmentError 발생"""
        # API_SECRET만 설정 (API_KEY 누락)
        os.environ["TEST_SPOT_API_SECRET"] = "test_secret"

        try:
            with pytest.raises(EnvironmentError, match="TEST_SPOT_API_KEY"):
                ConcreteSpotGateway(
                    gateway_name="test",
                    is_realworld_gateway=True,
                    provider="TEST"
                )
        finally:
            del os.environ["TEST_SPOT_API_SECRET"]

    def test_init_real_world_gateway_missing_api_secret_raises_error(self):
        """API Secret이 없으면 EnvironmentError 발생"""
        # API_KEY만 설정 (API_SECRET 누락)
        os.environ["TEST_SPOT_API_KEY"] = "test_key"

        try:
            with pytest.raises(EnvironmentError, match="TEST_SPOT_API_SECRET"):
                ConcreteSpotGateway(
                    gateway_name="test",
                    is_realworld_gateway=True,
                    provider="TEST"
                )
        finally:
            del os.environ["TEST_SPOT_API_KEY"]

    def test_init_real_world_gateway_empty_api_key_raises_error(self):
        """빈 문자열 API Key는 EnvironmentError 발생"""
        os.environ["TEST_SPOT_API_KEY"] = ""
        os.environ["TEST_SPOT_API_SECRET"] = "test_secret"

        try:
            with pytest.raises(EnvironmentError, match="TEST_SPOT_API_KEY.*비어있습니다"):
                ConcreteSpotGateway(
                    gateway_name="test",
                    is_realworld_gateway=True,
                    provider="TEST"
                )
        finally:
            del os.environ["TEST_SPOT_API_KEY"]
            del os.environ["TEST_SPOT_API_SECRET"]
