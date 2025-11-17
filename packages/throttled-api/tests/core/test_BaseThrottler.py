"""
BaseThrottler tests
"""
import pytest
import asyncio
import time
from unittest.mock import Mock
from throttled_api.core.BaseThrottler import BaseThrottler
from throttled_api.core.Pipeline import Pipeline
from throttled_api.core.window.FixedWindow import FixedWindow
from throttled_api.core.window.SlidingWindow import SlidingWindow
from throttled_api.core.events import ThrottleEvent

pytestmark = pytest.mark.anyio(backends=["asyncio"])


class TestBaseThrottlerInitialization:
    """초기화 테스트"""

    def test_init_with_single_pipeline(self):
        """단일 Pipeline로 초기화"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window)
        throttler = BaseThrottler(pipelines=[pipeline])

        assert len(throttler.pipelines) == 1
        assert throttler.pipelines[0] is pipeline

    def test_init_with_multiple_pipelines(self):
        """여러 Pipeline로 초기화"""
        p1 = Pipeline("1m", FixedWindow(100, 60))
        p2 = Pipeline("1h", FixedWindow(1000, 3600))
        p3 = Pipeline("1d", SlidingWindow(10000, 86400))

        throttler = BaseThrottler(pipelines=[p1, p2, p3])

        assert len(throttler.pipelines) == 3


class TestBaseThrottlerCheckAndWait:
    """_check_and_wait 테스트"""

    async def test_passes_when_all_pipelines_allow(self):
        """모든 Pipeline이 허용하면 통과"""
        p1 = Pipeline("1m", FixedWindow(100, 60))
        p2 = Pipeline("1h", FixedWindow(1000, 3600))

        throttler = BaseThrottler(pipelines=[p1, p2])

        start = time.time()
        await throttler._check_and_wait(50)
        elapsed = time.time() - start

        assert elapsed < 0.1  # 즉시 통과
        assert p1.window.remaining == 50
        assert p2.window.remaining == 950

    
    async def test_waits_when_pipeline_blocks(self):
        """Pipeline이 차단하면 대기"""
        p1 = Pipeline("1m", FixedWindow(100, 1))  # 1초 윈도우

        throttler = BaseThrottler(pipelines=[p1])

        # 용량 모두 소비
        await throttler._check_and_wait(100)
        assert p1.window.remaining == 0

        # 다시 시도하면 대기
        start = time.time()
        await throttler._check_and_wait(50)
        elapsed = time.time() - start

        assert elapsed >= 1.0  # 최소 1초 대기
        assert p1.window.remaining == 50  # 리셋 후 50 소비

    
    async def test_waits_for_longest_wait_time(self):
        """가장 긴 대기 시간만큼 대기"""
        p1 = Pipeline("1s", FixedWindow(100, 1))  # 1초
        p2 = Pipeline("2s", FixedWindow(100, 2))  # 2초

        throttler = BaseThrottler(pipelines=[p1, p2])

        await throttler._check_and_wait(100)
        await throttler._check_and_wait(100)  # 둘 다 소진

        start = time.time()
        await throttler._check_and_wait(50)
        elapsed = time.time() - start

        assert elapsed >= 2.0  # p2가 더 길므로 2초 대기

    
    async def test_consume_on_all_pipelines(self):
        """통과 시 모든 Pipeline에 차감"""
        p1 = Pipeline("1m", FixedWindow(100, 60))
        p2 = Pipeline("1h", FixedWindow(1000, 3600))

        throttler = BaseThrottler(pipelines=[p1, p2])

        await throttler._check_and_wait(30)

        assert p1.window.remaining == 70
        assert p2.window.remaining == 970


class TestBaseThrottlerConcurrency:
    """동시성 테스트"""

    
    async def test_concurrent_requests_are_serialized(self):
        """동시 요청이 직렬화됨 (Lock)"""
        p1 = Pipeline("1m", FixedWindow(100, 60))
        throttler = BaseThrottler(pipelines=[p1])

        async def make_request(cost):
            await throttler._check_and_wait(cost)

        # 동시에 여러 요청
        await asyncio.gather(
            make_request(30),
            make_request(20),
            make_request(10),
        )

        assert p1.window.remaining == 40  # 30 + 20 + 10 = 60 소비

    
    async def test_lock_prevents_race_condition(self):
        """Lock이 경쟁 조건 방지"""
        p1 = Pipeline("1m", FixedWindow(100, 60))
        throttler = BaseThrottler(pipelines=[p1])

        # 40개 요청을 동시에 (각 1씩 소비) - soft limiting 회피 (40% < 50%)
        tasks = [throttler._check_and_wait(1) for _ in range(40)]
        await asyncio.gather(*tasks)

        assert p1.window.remaining == 60  # 정확히 40 소비


class TestBaseThrottlerEventPropagation:
    """이벤트 전파 테스트"""

    
    async def test_pipeline_events_propagated_to_throttler_listeners(self):
        """Pipeline 이벤트가 Throttler 리스너로 전파"""
        window = FixedWindow(limit=100, window_seconds=60)
        pipeline = Pipeline(timeframe="1m", window=window, threshold=0.5)

        throttler = BaseThrottler(pipelines=[pipeline])

        listener = Mock()
        throttler.add_event_listener(listener)

        await throttler._check_and_wait(51)

        listener.assert_called_once()
        event = listener.call_args[0][0]
        assert isinstance(event, ThrottleEvent)
        assert event.timeframe == "1m"

    
    async def test_multiple_pipeline_events(self):
        """여러 Pipeline에서 이벤트 발생"""
        p1 = Pipeline("1m", FixedWindow(100, 60), threshold=0.5)
        p2 = Pipeline("1h", FixedWindow(100, 3600), threshold=0.3)

        throttler = BaseThrottler(pipelines=[p1, p2])

        listener = Mock()
        throttler.add_event_listener(listener)

        await throttler._check_and_wait(71)  # 둘 다 임계값 하회

        assert listener.call_count == 2  # 두 이벤트 발행
        events = [call[0][0] for call in listener.call_args_list]
        timeframes = {e.timeframe for e in events}
        assert timeframes == {"1m", "1h"}

    
    async def test_remove_event_listener(self):
        """이벤트 리스너 제거"""
        pipeline = Pipeline("1m", FixedWindow(100, 60), threshold=0.5)
        throttler = BaseThrottler(pipelines=[pipeline])

        listener = Mock()
        throttler.add_event_listener(listener)
        throttler.remove_event_listener(listener)

        await throttler._check_and_wait(51)

        listener.assert_not_called()


class TestBaseThrottlerMultiConstraint:
    """다중 제약 테스트"""

    
    async def test_all_constraints_must_pass(self):
        """모든 제약을 통과해야 함"""
        p1 = Pipeline("10req", FixedWindow(10, 60))   # 분당 10
        p2 = Pipeline("100req", FixedWindow(100, 60))  # 분당 100

        throttler = BaseThrottler(pipelines=[p1, p2])

        # 4개 요청 (soft limiting 회피, 40% < 50%)
        for _ in range(4):
            await throttler._check_and_wait(1)

        assert p1.window.remaining == 6
        assert p2.window.remaining == 96

        # 5번째 요청 (soft limiting 시작 전 마지막)
        await throttler._check_and_wait(1)

        # p1은 50% 도달, p2는 여전히 여유
        assert p1.window.remaining == 5
        assert p2.window.remaining == 95

    
    async def test_mixed_window_strategies(self):
        """Fixed와 Sliding 혼합"""
        p1 = Pipeline("fixed", FixedWindow(100, 2))
        p2 = Pipeline("sliding", SlidingWindow(100, 2))

        throttler = BaseThrottler(pipelines=[p1, p2])

        await throttler._check_and_wait(50)
        await throttler._check_and_wait(50)

        assert p1.window.remaining == 0
        assert p2.window.remaining == 0

        # 2초 대기 후 모두 회복
        await asyncio.sleep(2.1)

        await throttler._check_and_wait(10)
        assert p1.window.remaining == 90   # 리셋
        assert p2.window.remaining == 90   # 만료 회복
