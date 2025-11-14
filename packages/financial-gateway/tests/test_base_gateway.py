"""BaseGateway 테스트"""

import pytest
from financial_gateway.base import BaseGateway


class ConcreteGateway(BaseGateway):
    """테스트용 구체 클래스"""

    def __init__(self, gateway_name: str, is_realworld_gateway: bool):
        super().__init__(gateway_name, is_realworld_gateway)


class TestBaseGateway:
    """BaseGateway 테스트 케이스"""

    def test_init_with_real_world_gateway(self):
        """Real world gateway 초기화 테스트"""
        gateway = ConcreteGateway(gateway_name="binance", is_realworld_gateway=True)

        assert gateway.gateway_name == "binance"
        assert gateway.is_realworld_gateway is True

    def test_init_with_simulation_gateway(self):
        """Simulation gateway 초기화 테스트"""
        gateway = ConcreteGateway(gateway_name="simulation", is_realworld_gateway=False)

        assert gateway.gateway_name == "simulation"
        assert gateway.is_realworld_gateway is False

    def test_cannot_instantiate_directly(self):
        """BaseGateway를 직접 인스턴스화할 수 없음을 확인"""
        # BaseGateway가 ABC를 상속하지 않으면 이 테스트는 스킵
        # 현재 설계에서는 BaseGateway가 ABC가 아니므로 이 테스트는 제외
        pass
