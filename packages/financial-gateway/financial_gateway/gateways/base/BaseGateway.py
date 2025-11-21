from abc import ABC


class BaseGateway(ABC):
    """모든 Gateway의 최상위 추상 클래스"""

    @property
    def gateway_name(self) -> str:
        """Gateway 이름 반환"""
        raise NotImplementedError

    @property
    def is_realworld_gateway(self) -> bool:
        """실거래 Gateway 여부 반환 (True: 실거래, False: 시뮬레이션)"""
        raise NotImplementedError

    def validate_api_credentials(self) -> bool:
        """API 인증 정보 유효성 검증 (선택적 구현)"""
        return True
