"""
FixedWindow tests
"""
import pytest
import time
from throttled_api.core.window.FixedWindow import FixedWindow


class TestFixedWindowInitialization:
    """초기화 테스트"""

    def test_init_sets_limit_and_remaining(self):
        """초기값 설정"""
        window = FixedWindow(limit=100, window_seconds=60)
        assert window.limit == 100
        assert window.remaining == 100
        assert window.window_seconds == 60

    def test_remaining_rate_is_1_initially(self):
        """초기 remaining_rate는 1.0"""
        window = FixedWindow(limit=100, window_seconds=60)
        assert window.get_remaining_rate() == 1.0


class TestFixedWindowCanSend:
    """can_send 테스트"""

    def test_can_send_when_enough_remaining(self):
        """남은 용량이 충분하면 True"""
        window = FixedWindow(limit=100, window_seconds=60)
        assert window.can_send(50) is True
        assert window.can_send(100) is True

    def test_cannot_send_when_insufficient_remaining(self):
        """남은 용량이 부족하면 False"""
        window = FixedWindow(limit=100, window_seconds=60)
        window.consume(90)
        assert window.can_send(20) is False

    def test_can_send_after_reset(self):
        """리셋 후 다시 보낼 수 있음"""
        window = FixedWindow(limit=100, window_seconds=1)  # 1초 윈도우
        window.consume(100)
        assert window.can_send(10) is False

        time.sleep(1.1)  # 리셋 대기
        assert window.can_send(10) is True  # can_send가 리셋 체크
        assert window.remaining == 100  # 리셋됨


class TestFixedWindowConsume:
    """consume 테스트"""

    def test_consume_decreases_remaining(self):
        """소비 시 remaining 감소"""
        window = FixedWindow(limit=100, window_seconds=60)
        timestamp = window.consume(30)
        assert window.remaining == 70
        assert isinstance(timestamp, float)

    def test_consume_returns_timestamp(self):
        """소비 시 timestamp 반환"""
        window = FixedWindow(limit=100, window_seconds=60)
        before = time.time()
        timestamp = window.consume(10)
        after = time.time()
        assert before <= timestamp <= after

    def test_consume_multiple_times(self):
        """여러 번 소비"""
        window = FixedWindow(limit=100, window_seconds=60)
        window.consume(20)
        window.consume(30)
        window.consume(10)
        assert window.remaining == 40


class TestFixedWindowRefund:
    """refund 테스트"""

    def test_refund_increases_remaining(self):
        """환불 시 remaining 증가"""
        window = FixedWindow(limit=100, window_seconds=60)
        timestamp = window.consume(30)
        window.refund(timestamp, 30)
        assert window.remaining == 100

    def test_refund_partial_amount(self):
        """일부만 환불"""
        window = FixedWindow(limit=100, window_seconds=60)
        timestamp = window.consume(50)
        window.refund(timestamp, 20)
        assert window.remaining == 70

    def test_refund_ignores_timestamp(self):
        """FixedWindow는 timestamp 무시"""
        window = FixedWindow(limit=100, window_seconds=60)
        timestamp1 = window.consume(30)
        timestamp2 = window.consume(20)
        # 다른 timestamp로 환불해도 동작
        window.refund(timestamp1, 20)
        assert window.remaining == 70


class TestFixedWindowWaitTime:
    """wait_time 테스트"""

    def test_wait_time_is_zero_when_can_send(self):
        """보낼 수 있으면 대기 시간 0"""
        window = FixedWindow(limit=100, window_seconds=60)
        assert window.wait_time() == 0.0

    def test_wait_time_returns_time_until_reset(self):
        """보낼 수 없으면 리셋까지 대기 시간"""
        window = FixedWindow(limit=100, window_seconds=2)
        window.consume(100)
        wait = window.wait_time()
        assert 0 < wait <= 2

    def test_wait_time_decreases_over_time(self):
        """시간이 지나면 대기 시간 감소"""
        window = FixedWindow(limit=100, window_seconds=2)
        window.consume(100)
        wait1 = window.wait_time()
        time.sleep(0.5)
        wait2 = window.wait_time()
        assert wait2 < wait1


class TestFixedWindowReset:
    """리셋 동작 테스트"""

    def test_reset_happens_automatically_on_can_send(self):
        """can_send 호출 시 자동 리셋"""
        window = FixedWindow(limit=100, window_seconds=1)
        window.consume(100)
        assert window.remaining == 0
        time.sleep(1.1)
        window.can_send(10)  # 여기서 리셋 체크
        assert window.remaining == 100

    def test_reset_happens_automatically_on_consume(self):
        """consume 호출 시 자동 리셋"""
        window = FixedWindow(limit=100, window_seconds=1)
        window.consume(100)
        time.sleep(1.1)
        window.consume(10)  # 여기서 리셋 체크
        assert window.remaining == 90  # 리셋 후 10 소비


class TestFixedWindowRemainingRate:
    """remaining_rate 테스트"""

    def test_remaining_rate_decreases_on_consume(self):
        """소비 시 비율 감소"""
        window = FixedWindow(limit=100, window_seconds=60)
        window.consume(50)
        assert window.get_remaining_rate() == 0.5

    def test_remaining_rate_increases_on_refund(self):
        """환불 시 비율 증가"""
        window = FixedWindow(limit=100, window_seconds=60)
        timestamp = window.consume(80)
        window.refund(timestamp, 30)
        assert window.get_remaining_rate() == 0.5
