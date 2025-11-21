from abc import abstractmethod
from .BaseGateway import BaseGateway
from financial_gateway.structures.base import BaseRequest, BaseResponse


class SpotMarketGatewayBase(BaseGateway):
    """Spot 시장 Gateway의 통일된 인터페이스"""

    @abstractmethod
    async def execute(self, request: BaseRequest) -> BaseResponse:
        """Request 처리 후 Response 반환"""
        raise NotImplementedError
