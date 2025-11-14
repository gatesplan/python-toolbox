# BaseResponse - 모든 Response 클래스의 기본 클래스

from dataclasses import dataclass


@dataclass
class BaseResponse:
    # 모든 Gateway Response의 공통 기본 클래스

    # 메타데이터
    source_request_id: str = ""        # 원본 Request의 client_request_id
    timestamp: int = 0                 # 응답 생성 시각 (unix timestamp 초단위)
    gateway: str = ""                  # Gateway 식별자 (예: "binance", "upbit", "simulation")

    # 공통 상태 플래그
    is_success: bool = False           # 작업 성공 여부
    error_message: str = ""            # 에러 메시지 (실패 시)

    # 공통 에러 플래그
    is_permission_denied: bool = False     # API 권한 부족, IP 차단, 지역 제한 등
    is_network_error: bool = False         # 네트워크 오류
    is_rate_limit_exceeded: bool = False   # API 호출 제한 초과
    is_system_error: bool = False          # 거래소 내부 시스템 오류
