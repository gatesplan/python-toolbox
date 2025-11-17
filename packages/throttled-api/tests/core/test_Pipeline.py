"""
Pipeline tests
"""
import pytest
import time
from unittest.mock import Mock
from throttled_api.core.Pipeline import Pipeline
from throttled_api.core.window.FixedWindow import FixedWindow
from throttled_api.core.window.SlidingWindow import SlidingWindow
from throttled_api.core.events import ThrottleEvent


class TestPipelineInitialization:
    """초기화 테스트"""

    def test_init_with_fixed_window(self):
        """FixedWindow로 초기화"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window)
        assert pipeline.timeframe == "1m"
        assert pipeline.window is window

    def test_init_with_sliding_window(self):
        """SlidingWindow로 초기화"""
        window = SlidingWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1h", window=window)
        assert pipeline.timeframe == "1h"
        assert pipeline.window is window

    def test_init_with_threshold(self):
        """임계값 설정"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window, threshold=0.3)
        assert pipeline.threshold == 0.3

    def test_init_default_threshold_is_none(self):
        """기본 임계값은 None (이벤트 발행 안 함)"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window)
        assert pipeline.threshold is None


class TestPipelineDelegation:
    """Window 위임 테스트"""

    def test_can_send_delegates_to_window(self):
        """can_send가 Window에 위임"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window)
        assert pipeline.can_send(50) is True
        window.consume(90)
        assert pipeline.can_send(20) is False

    def test_consume_delegates_to_window(self):
        """consume이 Window에 위임"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window)
        timestamp = pipeline.consume(30)
        assert window.remaining == 70
        assert isinstance(timestamp, float)

    def test_refund_delegates_to_window(self):
        """refund가 Window에 위임"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window)
        timestamp = pipeline.consume(30)
        pipeline.refund(timestamp, 30)
        assert window.remaining == 100

    def test_wait_time_delegates_to_window(self):
        """wait_time이 Window에 위임"""
        window = FixedWindow(limit=100, window_seconds=2)
        pipeline = Pipeline(timeframe="1m", window=window)
        window.consume(100)
        wait = pipeline.wait_time()
        assert 0 < wait <= 2


class TestPipelineEventEmission:
    """이벤트 발행 테스트"""

    def test_event_emitted_when_threshold_crossed(self):
        """임계값 하회 시 이벤트 발행"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window, threshold=0.5)

        listener = Mock()
        pipeline.add_listener(listener)

        # 50% 이상 소비하면 이벤트 발행
        pipeline.consume(51)

        listener.assert_called_once()
        event = listener.call_args[0][0]
        assert isinstance(event, ThrottleEvent)
        assert event.timeframe == "1m"
        assert event.remaining_rate < 0.5
        assert event.remaining_cap == 49

    def test_event_not_emitted_when_above_threshold(self):
        """임계값 위에 있으면 이벤트 발행 안 함"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window, threshold=0.5)

        listener = Mock()
        pipeline.add_listener(listener)

        pipeline.consume(40)  # 60% 남음 (0.6 > 0.5)

        listener.assert_not_called()

    def test_event_not_emitted_when_threshold_is_none(self):
        """임계값이 None이면 이벤트 발행 안 함"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window, threshold=None)

        listener = Mock()
        pipeline.add_listener(listener)

        pipeline.consume(99)  # 거의 다 소비

        listener.assert_not_called()

    def test_event_emitted_only_once_per_threshold_cross(self):
        """임계값 교차 시 한 번만 발행 (연속 발행 방지)"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window, threshold=0.5)

        listener = Mock()
        pipeline.add_listener(listener)

        pipeline.consume(51)  # 첫 번째 교차
        pipeline.consume(10)  # 여전히 임계값 아래
        pipeline.consume(10)  # 여전히 임계값 아래

        assert listener.call_count == 1  # 한 번만 호출

    def test_event_emitted_again_after_recovery(self):
        """회복 후 다시 하회하면 재발행"""
        window = FixedWindow(limit=100, window_seconds=1)
        pipeline = Pipeline(timeframe="1m", window=window, threshold=0.5)

        listener = Mock()
        pipeline.add_listener(listener)

        pipeline.consume(51)  # 첫 번째 교차
        assert listener.call_count == 1

        time.sleep(1.1)  # 리셋 대기
        pipeline.can_send(10)  # 리셋 트리거

        pipeline.consume(51)  # 두 번째 교차
        assert listener.call_count == 2


class TestPipelineMultipleListeners:
    """다중 리스너 테스트"""

    def test_multiple_listeners_called(self):
        """여러 리스너 모두 호출"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window, threshold=0.5)

        listener1 = Mock()
        listener2 = Mock()
        listener3 = Mock()

        pipeline.add_listener(listener1)
        pipeline.add_listener(listener2)
        pipeline.add_listener(listener3)

        pipeline.consume(51)

        listener1.assert_called_once()
        listener2.assert_called_once()
        listener3.assert_called_once()

    def test_remove_listener(self):
        """리스너 제거"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window, threshold=0.5)

        listener = Mock()
        pipeline.add_listener(listener)
        pipeline.remove_listener(listener)

        pipeline.consume(51)

        listener.assert_not_called()


class TestPipelineWithSlidingWindow:
    """SlidingWindow와 함께 테스트"""

    def test_works_with_sliding_window(self):
        """SlidingWindow와 함께 동작"""
        window = SlidingWindow(limit=100, window_seconds=1)
        pipeline = Pipeline(timeframe="1s", window=window, threshold=0.3)

        listener = Mock()
        pipeline.add_listener(listener)

        pipeline.consume(71)  # 29% 남음 (< 0.3)

        listener.assert_called_once()
        event = listener.call_args[0][0]
        assert event.timeframe == "1s"
        assert abs(event.remaining_rate - 0.29) < 0.01

    def test_event_after_expiration_recovery(self):
        """만료 회복 후 다시 하회 시 이벤트"""
        window = SlidingWindow(limit=100, window_seconds=1)
        pipeline = Pipeline(timeframe="1s", window=window, threshold=0.5)

        listener = Mock()
        pipeline.add_listener(listener)

        pipeline.consume(60)
        assert listener.call_count == 1

        time.sleep(1.1)  # 만료 대기
        pipeline.can_send(10)  # 회복

        pipeline.consume(60)
        assert listener.call_count == 2
