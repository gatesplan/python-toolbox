"""
BaseThrottler implementation
"""
import asyncio
from typing import List, Callable
from simple_logger import logger, func_logging
from .Pipeline import Pipeline
from .events import ThrottleEvent


class BaseThrottler:
    """
    여러 Pipeline 조율 + 이벤트 전달

    여러 Pipeline을 관리하며, 모든 Pipeline이 통과할 때까지 대기.
    asyncio.Lock으로 동시성 제어.
    Pipeline에서 발행된 이벤트를 외부 리스너에게 전달 (옵저버 패턴 Subject).
    """

    def __init__(self, pipelines: List[Pipeline]):
        """
        Args:
            pipelines: Pipeline 리스트
        """
        self.pipelines = pipelines
        self._lock = asyncio.Lock()
        self._event_listeners: List[Callable[[ThrottleEvent], None]] = []

        # 각 Pipeline의 이벤트를 자신에게 전달하도록 설정
        for pipeline in self.pipelines:
            pipeline.add_listener(self._on_pipeline_event)

    async def _check_and_wait(self, cost: int) -> None:
        """
        모든 Pipeline이 통과할 때까지 대기 후 소모량 차감

        Soft rate limiting: 50% 이상 소진 시 점진적 딜레이
        Hard rate limiting: 용량 부족 시 리셋/만료까지 대기

        Args:
            cost: 요청 소모량
        """
        while True:
            # 모든 Pipeline의 대기 시간 계산 (soft + hard limit 모두 포함)
            wait_times = [p.wait_time(cost) for p in self.pipelines]
            max_wait = max(wait_times) if wait_times else 0.0

            # 대기가 필요하면 sleep
            if max_wait > 0:
                logger.debug(f"Rate limit 대기: {max_wait:.3f}초 (cost={cost})")
                await asyncio.sleep(max_wait)
                continue

            # 대기 불필요 → consume 시도
            async with self._lock:
                # 모든 Pipeline이 통과하는지 재확인
                can_send_all = all(p.can_send(cost) for p in self.pipelines)

                if can_send_all:
                    # 모두 통과 → 모든 Pipeline에 차감
                    for pipeline in self.pipelines:
                        pipeline.consume(cost)
                    return
                # can_send 실패 시 다음 루프에서 재계산

    def add_event_listener(self, listener: Callable[[ThrottleEvent], None]) -> None:
        """
        이벤트 리스너 등록

        Args:
            listener: ThrottleEvent를 받는 콜백 함수
        """
        self._event_listeners.append(listener)

    def remove_event_listener(self, listener: Callable[[ThrottleEvent], None]) -> None:
        """
        이벤트 리스너 제거

        Args:
            listener: 제거할 콜백 함수
        """
        if listener in self._event_listeners:
            self._event_listeners.remove(listener)

    def _on_pipeline_event(self, event: ThrottleEvent) -> None:
        """
        Pipeline에서 발행된 이벤트를 외부 리스너에게 전파

        Args:
            event: Pipeline에서 발행된 이벤트
        """
        for listener in self._event_listeners:
            listener(event)
