"""
Soft Rate Limiting (Equal Distribution) tests
"""
import pytest
import time
import logging
from throttled_api.core.window.FixedWindow import FixedWindow
from throttled_api.core.window.SlidingWindow import SlidingWindow


class TestFixedWindowEqualDistribution:
    """FixedWindow 균등 분배 soft limiting 테스트"""

    def test_equal_distribution_basic(self):
        """기본 균등 분배 계산"""
        window = FixedWindow(limit=6000, window_seconds=60)

        # 20초에 3000 소비 (40초 남음)
        window.consume(3000)
        window.next_reset_time = time.time() + 40

        # delay_per_unit = 40 / 3000 = 0.0133
        # cost=1 -> 0.0133초
        wait1 = window.wait_time(1)
        assert 0.012 < wait1 < 0.015

        # cost=25 -> 0.333초
        wait25 = window.wait_time(25)
        assert 0.32 < wait25 < 0.35

        # cost=100 -> 1.33초 (하지만 max=0.5로 cap됨)
        wait100 = window.wait_time(100)
        assert wait100 == 0.5  # max_soft_delay로 cap

    def test_no_delay_when_cost_is_zero(self):
        """cost=0이면 대기 없음"""
        window = FixedWindow(limit=100, window_seconds=60)
        window.consume(50)

        assert window.wait_time(0) == 0.0

    def test_delay_proportional_to_cost(self):
        """딜레이가 cost에 비례"""
        window = FixedWindow(limit=1000, window_seconds=60)
        window.consume(800)  # 200 남음
        # 20초 남았다고 가정
        window.next_reset_time = time.time() + 20

        # delay_per_unit = 20 / 200 = 0.1
        wait1 = window.wait_time(1)   # 0.1초
        wait2 = window.wait_time(2)   # 0.2초

        # wait2는 wait1의 약 2배
        assert abs(wait2 - wait1 * 2) < 0.01
        assert 0.09 < wait1 < 0.11
        assert 0.19 < wait2 < 0.21

    def test_max_soft_delay_cap(self):
        """max_soft_delay 초과 시 cap됨"""
        window = FixedWindow(limit=100, window_seconds=60, max_soft_delay=0.3)

        # 90 소비 (10 남음)
        window.consume(90)
        window.next_reset_time = time.time() + 50

        # delay_per_unit = 50 / 10 = 5.0
        # cost=1 -> 5초 계산되지만 max=0.3으로 cap
        wait = window.wait_time(1)
        assert wait == 0.3

    def test_custom_max_soft_delay(self):
        """커스텀 max_soft_delay"""
        window = FixedWindow(limit=100, window_seconds=60, max_soft_delay=0.1)

        window.consume(50)
        window.next_reset_time = time.time() + 30

        # delay_per_unit = 30 / 50 = 0.6
        # cost=1 -> 0.6초 계산되지만 0.1로 cap
        wait = window.wait_time(1)
        assert wait == 0.1

    def test_warning_logged_on_exceed(self, caplog):
        """max 초과 시 경고 로깅"""
        caplog.set_level(logging.WARNING)

        window = FixedWindow(limit=100, window_seconds=60, max_soft_delay=0.5)
        window.consume(90)  # 10 남음
        window.next_reset_time = time.time() + 50

        # delay_per_unit = 50 / 10 = 5.0
        # cost=1 -> 5초 계산, max=0.5 초과
        window.wait_time(1)

        assert "Soft Limit Exceeded" in caplog.text
        assert "Consider reducing request rate" in caplog.text

    def test_no_warning_when_below_max(self, caplog):
        """max 이하면 경고 없음"""
        caplog.set_level(logging.WARNING)

        window = FixedWindow(limit=100, window_seconds=60, max_soft_delay=0.5)
        window.consume(80)  # 20 남음
        window.next_reset_time = time.time() + 5

        # delay_per_unit = 5 / 20 = 0.25
        # cost=1 -> 0.25초, max=0.5 이하
        window.wait_time(1)

        assert "Soft Limit Exceeded" not in caplog.text

    def test_hard_limit_when_cost_exceeds_remaining(self):
        """cost > remaining 시 hard limit"""
        window = FixedWindow(limit=100, window_seconds=60)
        window.consume(90)
        window.next_reset_time = time.time() + 50

        # cost=20 > remaining=10 -> hard limit
        wait = window.wait_time(20)
        assert 49 < wait < 51  # 리셋까지 약 50초

    def test_hard_limit_when_over_consumed(self):
        """over-consumed 시 hard limit"""
        window = FixedWindow(limit=100, window_seconds=60)
        window.consume(100)
        window.next_reset_time = time.time() + 40

        wait = window.wait_time(1)
        assert 39 < wait < 41  # 리셋까지 약 40초


class TestSlidingWindowEqualDistribution:
    """SlidingWindow 균등 분배 soft limiting 테스트"""

    def test_equal_distribution_basic(self):
        """기본 균등 분배 계산"""
        window = SlidingWindow(limit=1000, window_seconds=60, max_soft_delay=2.0)

        # 첫 번째 소비
        ts1 = window.consume(500)
        # 500 남음, 60초 후 회복

        # delay_per_unit = 60 / 500 = 0.12
        wait = window.wait_time(10)
        assert 1.1 < wait < 1.3  # 약 1.2초

    def test_delay_based_on_oldest_expiration(self):
        """가장 오래된 항목 만료 시간 기준"""
        window = SlidingWindow(limit=100, window_seconds=2, max_soft_delay=1.0)

        # 첫 번째 소비
        window.consume(50)
        time.sleep(0.5)

        # 두 번째 소비
        window.consume(30)
        # remaining=20

        # 첫 번째 항목이 1.5초 후 만료
        # delay_per_unit = 1.5 / 20 = 0.075
        wait = window.wait_time(10)
        assert 0.6 < wait < 0.9  # 약 0.75초

    def test_max_soft_delay_cap(self):
        """max_soft_delay 초과 시 cap"""
        window = SlidingWindow(limit=100, window_seconds=60, max_soft_delay=0.3)

        window.consume(90)
        # 10 남음, 60초 후 회복
        # delay_per_unit = 60 / 10 = 6.0

        # cost=1 -> 6초 계산되지만 0.3으로 cap
        wait = window.wait_time(1)
        assert wait == 0.3

    def test_no_delay_when_history_empty(self):
        """히스토리가 비어있으면 대기 없음"""
        window = SlidingWindow(limit=100, window_seconds=60)

        # 아무것도 소비하지 않음
        wait = window.wait_time(10)
        assert wait == 0.0

    def test_warning_logged_on_exceed(self, caplog):
        """max 초과 시 경고 로깅"""
        caplog.set_level(logging.WARNING)

        window = SlidingWindow(limit=100, window_seconds=60, max_soft_delay=0.5)
        window.consume(95)

        # 대기 시간이 max를 크게 초과
        window.wait_time(5)

        assert "Soft Limit Exceeded" in caplog.text
        assert "next_recovery" in caplog.text

    def test_hard_limit_when_cost_exceeds_remaining(self):
        """cost > remaining 시 hard limit"""
        window = SlidingWindow(limit=100, window_seconds=2)
        window.consume(90)
        # remaining=10

        # cost=20 > 10 -> hard limit
        wait = window.wait_time(20)
        assert 1.9 < wait < 2.1  # 가장 오래된 항목 만료까지


class TestEqualDistributionComparison:
    """FixedWindow vs SlidingWindow 균등 분배 비교"""

    def test_both_use_proportional_delay(self):
        """두 전략 모두 cost에 비례한 딜레이"""
        fixed = FixedWindow(limit=100, window_seconds=60)
        sliding = SlidingWindow(limit=100, window_seconds=60)

        # 동일하게 50 소비
        fixed.consume(50)
        sliding.consume(50)

        # Fixed: 60초 남음
        fixed.next_reset_time = time.time() + 60

        # 둘 다 delay_per_unit = 60 / 50 = 1.2
        # cost=5 -> 6초 계산 but max=0.5로 cap
        wait_fixed = fixed.wait_time(5)
        wait_sliding = sliding.wait_time(5)

        # 둘 다 max로 cap됨
        assert wait_fixed == 0.5
        assert wait_sliding == 0.5

    def test_different_time_left_calculation(self):
        """시간 계산 방식은 다름"""
        fixed = FixedWindow(limit=100, window_seconds=10)
        sliding = SlidingWindow(limit=100, window_seconds=10)

        # Fixed: 5초에 50 소비, 5초 남음
        fixed.consume(50)
        fixed.next_reset_time = time.time() + 5

        # Sliding: 방금 50 소비, 10초 후 회복
        sliding.consume(50)

        # Fixed: delay_per_unit = 5 / 50 = 0.1
        wait_fixed = fixed.wait_time(1)
        assert 0.09 < wait_fixed < 0.11

        # Sliding: delay_per_unit = 10 / 50 = 0.2
        wait_sliding = sliding.wait_time(1)
        assert 0.19 < wait_sliding < 0.21

        # Sliding이 더 긴 대기
        assert wait_sliding > wait_fixed
