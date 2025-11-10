# 캔들 영역 분석

from simple_logger import func_logging


class CandleAnalyzer:

    @staticmethod
    @func_logging(level="DEBUG")
    def classify_zone(price, target_price: float) -> str:
        # 캔들에서 목표 가격이 위치한 영역 분류
        body_bottom = price.bodybottom()
        body_top = price.bodytop()

        if body_bottom <= target_price <= body_top:
            return "body"

        if body_top < target_price <= price.h:
            return "head"

        if price.l <= target_price < body_bottom:
            return "tail"

        return "none"
