"""
SlidingWindow tests
"""
import pytest
import time
from throttled_api.core.window.SlidingWindow import SlidingWindow


class TestSlidingWindowInitialization:
    """초기화 테스트"""

    def test_init_sets_limit_and_remaining(self):
        """초기값 설정"""
        window = SlidingWindow(limit=100, window_seconds=60)
        assert window.limit == 100
        assert window.remaining == 100
        assert window.window_seconds == 60

    def test_history_is_empty_initially(self):
        """초기 히스토리는 비어있음"""
        window = SlidingWindow(limit=100, window_seconds=60)
        assert len(window.history) == 0


class TestSlidingWindowCanSend:
    """can_send 테스트"""

    def test_can_send_when_enough_remaining(self):
        """남은 용량이 충분하면 True"""
        window = SlidingWindow(limit=100, window_seconds=60)
        assert window.can_send(50) is True
        assert window.can_send(100) is True

    def test_cannot_send_when_insufficient_remaining(self):
        """남은 용량이 부족하면 False"""
        window = SlidingWindow(limit=100, window_seconds=60)
        window.consume(90)
        assert window.can_send(20) is False

    def test_can_send_after_expiration(self):
        """만료 후 다시 보낼 수 있음"""
        window = SlidingWindow(limit=100, window_seconds=1)  # 1초 윈도우
        window.consume(100)
        assert window.can_send(10) is False

        time.sleep(1.1)  # 만료 대기
        assert window.can_send(10) is True  # can_send가 만료 항목 제거
        assert window.remaining == 100  # 회복됨
        assert len(window.history) == 0  # 히스토리 비워짐


class TestSlidingWindowConsume:
    """consume 테스트"""

    def test_consume_decreases_remaining(self):
        """소비 시 remaining 감소"""
        window = SlidingWindow(limit=100, window_seconds=60)
        timestamp = window.consume(30)
        assert window.remaining == 70
        assert isinstance(timestamp, float)

    def test_consume_adds_to_history(self):
        """소비 시 히스토리에 추가"""
        window = SlidingWindow(limit=100, window_seconds=60)
        before = time.time()
        timestamp = window.consume(30)
        after = time.time()

        assert len(window.history) == 1
        ts, cost = window.history[0]
        assert before <= ts <= after
        assert cost == 30

    def test_consume_multiple_times(self):
        """여러 번 소비"""
        window = SlidingWindow(limit=100, window_seconds=60)
        window.consume(20)
        window.consume(30)
        window.consume(10)
        assert window.remaining == 40
        assert len(window.history) == 3


class TestSlidingWindowExpiration:
    """만료 처리 테스트"""

    def test_expired_items_removed_on_can_send(self):
        """can_send 시 만료 항목 제거"""
        window = SlidingWindow(limit=100, window_seconds=1)
        window.consume(30)
        window.consume(20)
        assert len(window.history) == 2
        assert window.remaining == 50

        time.sleep(1.1)
        window.can_send(10)  # 만료 체크
        assert len(window.history) == 0
        assert window.remaining == 100

    def test_partial_expiration(self):
        """일부만 만료"""
        window = SlidingWindow(limit=100, window_seconds=1)
        window.consume(30)
        time.sleep(0.6)
        window.consume(20)  # 0.6초 후
        time.sleep(0.6)     # 총 1.2초 경과, 첫 번째만 만료

        window.can_send(10)
        assert len(window.history) == 1
        assert window.remaining == 80  # 30 회복, 20은 남음

    def test_remaining_recovered_on_expiration(self):
        """만료 시 remaining 회복"""
        window = SlidingWindow(limit=100, window_seconds=1)
        window.consume(40)
        window.consume(30)
        assert window.remaining == 30

        time.sleep(1.1)
        window.can_send(10)
        assert window.remaining == 100


class TestSlidingWindowRefund:
    """refund 테스트"""

    def test_refund_removes_from_history(self):
        """환불 시 히스토리에서 제거"""
        window = SlidingWindow(limit=100, window_seconds=60)
        timestamp = window.consume(30)
        assert len(window.history) == 1

        window.refund(timestamp, 30)
        assert len(window.history) == 0
        assert window.remaining == 100

    def test_refund_finds_matching_timestamp_and_cost(self):
        """timestamp와 cost 모두 매칭"""
        window = SlidingWindow(limit=100, window_seconds=60)
        ts1 = window.consume(20)
        time.sleep(0.01)
        ts2 = window.consume(30)
        time.sleep(0.01)
        ts3 = window.consume(10)

        window.refund(ts2, 30)  # 두 번째 항목 환불
        assert len(window.history) == 2
        assert window.remaining == 70  # 20 + 10 = 30 소비됨, remaining = 100 - 30 = 70

    def test_refund_searches_in_reverse(self):
        """역순 검색 (최근 것부터)"""
        window = SlidingWindow(limit=100, window_seconds=60)
        # 같은 cost를 여러 번 소비
        ts1 = window.consume(20)
        time.sleep(0.01)
        ts2 = window.consume(20)
        time.sleep(0.01)
        ts3 = window.consume(20)

        # ts2로 환불하면 ts2와 매칭되는 항목 제거
        window.refund(ts2, 20)
        assert len(window.history) == 2
        # 히스토리에 ts1과 ts3만 남음
        timestamps = [ts for ts, _ in window.history]
        assert ts2 not in timestamps

    def test_refund_only_first_match(self):
        """첫 번째 매칭만 제거"""
        window = SlidingWindow(limit=100, window_seconds=60)
        ts = window.consume(20)
        window.consume(20)  # 같은 cost, 다른 timestamp

        window.refund(ts, 20)
        assert len(window.history) == 1  # 하나만 제거


class TestSlidingWindowWaitTime:
    """wait_time 테스트"""

    def test_wait_time_is_zero_when_can_send(self):
        """보낼 수 있으면 대기 시간 0"""
        window = SlidingWindow(limit=100, window_seconds=60)
        assert window.wait_time() == 0.0

    def test_wait_time_returns_time_until_oldest_expires(self):
        """보낼 수 없으면 가장 오래된 항목 만료 시간"""
        window = SlidingWindow(limit=100, window_seconds=2)
        window.consume(100)
        wait = window.wait_time()
        assert 0 < wait <= 2

    def test_wait_time_decreases_over_time(self):
        """시간이 지나면 대기 시간 감소"""
        window = SlidingWindow(limit=100, window_seconds=2)
        window.consume(100)
        wait1 = window.wait_time()
        time.sleep(0.5)
        wait2 = window.wait_time()
        assert wait2 < wait1

    def test_wait_time_considers_partial_recovery(self):
        """부분 회복을 고려한 대기 시간"""
        window = SlidingWindow(limit=100, window_seconds=2)
        window.consume(60)
        time.sleep(0.5)
        window.consume(50)  # 총 110 소비, remaining = -10

        # 첫 번째 60이 만료되면 50 회복 가능
        wait = window.wait_time()
        assert 1.3 < wait < 1.7  # 대략 1.5초 대기


class TestSlidingWindowRemainingRate:
    """remaining_rate 테스트"""

    def test_remaining_rate_decreases_on_consume(self):
        """소비 시 비율 감소"""
        window = SlidingWindow(limit=100, window_seconds=60)
        window.consume(50)
        assert window.get_remaining_rate() == 0.5

    def test_remaining_rate_increases_on_expiration(self):
        """만료 시 비율 증가"""
        window = SlidingWindow(limit=100, window_seconds=1)
        window.consume(80)
        assert window.get_remaining_rate() == 0.2

        time.sleep(1.1)
        window.can_send(10)  # 만료 체크
        assert window.get_remaining_rate() == 1.0
