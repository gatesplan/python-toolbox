from enum import Enum


class OrderStatus(Enum):
    """주문 상태를 표준화하는 Enum"""

    # 대기 상태
    PENDING = "pending"  # 주문 생성됨, 거래소 미전송
    SUBMITTED = "submitted"  # 거래소에 전송됨

    # Active 상태
    OPEN = "open"  # 거래소 활성화, 매칭 대기
    PARTIALLY_FILLED = "partially_filled"  # 부분 체결

    # 완료 상태
    FILLED = "filled"  # 전량 체결
    CANCELED = "canceled"  # 취소됨
    REJECTED = "rejected"  # 거래소 거부
    EXPIRED = "expired"  # 시간 만료

    # 오류
    FAILED = "failed"  # 처리 실패
