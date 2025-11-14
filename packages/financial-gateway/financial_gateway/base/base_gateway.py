# 모든 Gateway의 최상위 추상 클래스

from simple_logger import init_logging


class BaseGateway:
    # gateway_name 속성과 is_realworld_gateway 플래그를 제공

    @init_logging(level="INFO", log_params=True)
    def __init__(self, gateway_name: str, is_realworld_gateway: bool):
        self.gateway_name = gateway_name
        self.is_realworld_gateway = is_realworld_gateway
