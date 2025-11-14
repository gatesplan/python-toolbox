"""UpbitSpotGateway 테스트"""

import os
import pytest
from financial_gateway.spot import UpbitSpotGateway


class TestUpbitSpotGateway:
    """UpbitSpotGateway 테스트 케이스"""

    def test_init_without_api_keys_raises_error(self):
        """API 키가 없으면 EnvironmentError 발생"""
        # 환경변수가 없는 상태에서 초기화 시도
        # 기존 환경변수 백업
        backup_key = os.environ.get("UPBIT_SPOT_API_KEY")
        backup_secret = os.environ.get("UPBIT_SPOT_API_SECRET")

        # 환경변수 제거
        if "UPBIT_SPOT_API_KEY" in os.environ:
            del os.environ["UPBIT_SPOT_API_KEY"]
        if "UPBIT_SPOT_API_SECRET" in os.environ:
            del os.environ["UPBIT_SPOT_API_SECRET"]

        try:
            with pytest.raises(EnvironmentError, match="UPBIT_SPOT_API_KEY"):
                UpbitSpotGateway()
        finally:
            # 환경변수 복원
            if backup_key:
                os.environ["UPBIT_SPOT_API_KEY"] = backup_key
            if backup_secret:
                os.environ["UPBIT_SPOT_API_SECRET"] = backup_secret

    def test_init_with_valid_api_keys(self):
        """유효한 API 키로 초기화 성공"""
        # 환경변수 설정
        os.environ["UPBIT_SPOT_API_KEY"] = "test_upbit_key"
        os.environ["UPBIT_SPOT_API_SECRET"] = "test_upbit_secret"

        try:
            gateway = UpbitSpotGateway()

            assert gateway.gateway_name == "upbit"
            assert gateway.is_realworld_gateway is True
            assert gateway._api_key == "test_upbit_key"
            assert gateway._api_secret == "test_upbit_secret"
        finally:
            # 환경변수 정리
            del os.environ["UPBIT_SPOT_API_KEY"]
            del os.environ["UPBIT_SPOT_API_SECRET"]

    def test_init_with_empty_api_key_raises_error(self):
        """빈 문자열 API Key는 EnvironmentError 발생"""
        os.environ["UPBIT_SPOT_API_KEY"] = ""
        os.environ["UPBIT_SPOT_API_SECRET"] = "test_upbit_secret"

        try:
            with pytest.raises(EnvironmentError, match="UPBIT_SPOT_API_KEY.*비어있습니다"):
                UpbitSpotGateway()
        finally:
            del os.environ["UPBIT_SPOT_API_KEY"]
            del os.environ["UPBIT_SPOT_API_SECRET"]

    def test_init_with_empty_api_secret_raises_error(self):
        """빈 문자열 API Secret은 EnvironmentError 발생"""
        os.environ["UPBIT_SPOT_API_KEY"] = "test_upbit_key"
        os.environ["UPBIT_SPOT_API_SECRET"] = ""

        try:
            with pytest.raises(EnvironmentError, match="UPBIT_SPOT_API_SECRET.*비어있습니다"):
                UpbitSpotGateway()
        finally:
            del os.environ["UPBIT_SPOT_API_KEY"]
            del os.environ["UPBIT_SPOT_API_SECRET"]

    def test_request_limit_buy_order_not_implemented(self):
        """지정가 매수 주문은 아직 구현되지 않음"""
        os.environ["UPBIT_SPOT_API_KEY"] = "test_upbit_key"
        os.environ["UPBIT_SPOT_API_SECRET"] = "test_upbit_secret"

        try:
            gateway = UpbitSpotGateway()

            with pytest.raises(NotImplementedError, match="request_limit_buy_order"):
                gateway.request_limit_buy_order(None)
        finally:
            del os.environ["UPBIT_SPOT_API_KEY"]
            del os.environ["UPBIT_SPOT_API_SECRET"]

    def test_stop_orders_not_supported(self):
        """Upbit은 stop 주문을 지원하지 않음"""
        os.environ["UPBIT_SPOT_API_KEY"] = "test_upbit_key"
        os.environ["UPBIT_SPOT_API_SECRET"] = "test_upbit_secret"

        try:
            gateway = UpbitSpotGateway()

            # stop-limit 주문
            with pytest.raises(NotImplementedError, match="stop-limit.*지원하지 않습니다"):
                gateway.request_stop_limit_buy_order(None)

            with pytest.raises(NotImplementedError, match="stop-limit.*지원하지 않습니다"):
                gateway.request_stop_limit_sell_order(None)

            # stop-market 주문
            with pytest.raises(NotImplementedError, match="stop-market.*지원하지 않습니다"):
                gateway.request_stop_market_buy_order(None)

            with pytest.raises(NotImplementedError, match="stop-market.*지원하지 않습니다"):
                gateway.request_stop_market_sell_order(None)
        finally:
            del os.environ["UPBIT_SPOT_API_KEY"]
            del os.environ["UPBIT_SPOT_API_SECRET"]

    def test_modify_order_not_supported(self):
        """Upbit은 주문 수정을 지원하지 않음"""
        os.environ["UPBIT_SPOT_API_KEY"] = "test_upbit_key"
        os.environ["UPBIT_SPOT_API_SECRET"] = "test_upbit_secret"

        try:
            gateway = UpbitSpotGateway()

            with pytest.raises(NotImplementedError, match="주문 수정.*지원하지 않습니다"):
                gateway.request_modify_order(None)
        finally:
            del os.environ["UPBIT_SPOT_API_KEY"]
            del os.environ["UPBIT_SPOT_API_SECRET"]
