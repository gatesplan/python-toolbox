"""Base class for all request objects."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class BaseRequest:
    """모든 Request 클래스가 상속받는 기본 클래스.

    모든 요청에 고유한 추적 ID를 자동으로 부여하여 요청 추적 및 디버깅을 지원한다.
    """

    client_request_id: str = field(default_factory=lambda: BaseRequest._generate_client_request_id(), init=False)

    @staticmethod
    def _generate_client_request_id() -> str:
        """고유한 요청 ID를 생성한다.

        Returns:
            str: yymmddhhmmss-uuid4 형식의 고유 ID

        Example:
            >>> BaseRequest._generate_client_request_id()
            '250127153045-a7b3c4d5-e6f7-8901-2345-6789abcdef01'
        """
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        uuid_part = str(uuid4())
        return f"{timestamp}-{uuid_part}"
