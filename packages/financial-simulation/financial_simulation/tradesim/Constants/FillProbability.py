# 체결 확률 상수

class FillProbability:
    # Body 영역 체결 확률
    BODY_FULL = 1.0

    # Wick 영역 체결 확률 (GTC, GTD, IOC)
    WICK_FAIL = 0.3
    WICK_FULL = 0.3
    WICK_PARTIAL = 0.4

    # Wick 영역 FOK 체결 확률 (전량 체결이 더 어려움)
    WICK_FOK_FAIL = 0.6  # 실패 확률 높음
    WICK_FOK_FULL = 0.4  # 전량 체결만 가능
