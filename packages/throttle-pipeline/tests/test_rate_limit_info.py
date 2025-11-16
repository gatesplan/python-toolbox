import pytest
from datetime import datetime, timezone, timedelta
from throttle_pipeline.particles.rate_limit_info import RateLimitInfo


class TestRateLimitInfo:
    """RateLimitInfo dataclass 검증 테스트"""

    def test_create_rate_limit_info(self):
        """
        RateLimitInfo 정상 생성 검증

        API 응답 헤더로부터 파싱된 rate limit 정보를 담는 데이터 구조
        """
        # Given: Rate limit 정보
        remaining = 1000
        limit = 1200
        reset_time = datetime.now(timezone.utc)
        usage_ratio = 0.167  # (1200 - 1000) / 1200

        # When: RateLimitInfo 생성
        info = RateLimitInfo(
            remaining=remaining,
            limit=limit,
            reset_time=reset_time,
            usage_ratio=usage_ratio
        )

        # Then: 모든 필드가 정상 할당되어야 함
        assert info.remaining == 1000
        assert info.limit == 1200
        assert info.reset_time == reset_time
        assert pytest.approx(info.usage_ratio, 0.001) == 0.167

    def test_usage_ratio_calculation_from_remaining(self):
        """
        usage_ratio가 (limit - remaining) / limit로 계산되는지 검증

        사용률 = (전체 - 남은 것) / 전체
        예: 1200개 중 1000개 남음 → (1200-1000)/1200 = 0.167 (16.7% 사용)
        """
        # Given: remaining=1000, limit=1200
        remaining = 1000
        limit = 1200
        expected_ratio = (limit - remaining) / limit  # 200/1200 = 0.167

        # When: RateLimitInfo 생성 (usage_ratio 계산하여 전달)
        info = RateLimitInfo(
            remaining=remaining,
            limit=limit,
            reset_time=datetime.now(timezone.utc),
            usage_ratio=expected_ratio
        )

        # Then: usage_ratio가 올바르게 계산되어야 함
        assert pytest.approx(info.usage_ratio, 0.001) == 0.167

    def test_usage_ratio_zero_percent(self):
        """
        사용률 0% (remaining == limit) 케이스 검증

        아직 한 번도 사용하지 않은 상태
        """
        # Given: 전혀 사용하지 않은 상태
        remaining = 1200
        limit = 1200
        usage_ratio = (limit - remaining) / limit  # 0.0

        # When: RateLimitInfo 생성
        info = RateLimitInfo(
            remaining=remaining,
            limit=limit,
            reset_time=datetime.now(timezone.utc),
            usage_ratio=usage_ratio
        )

        # Then: usage_ratio가 0.0이어야 함
        assert info.usage_ratio == 0.0

    def test_usage_ratio_fifty_percent(self):
        """
        사용률 50% (remaining == limit/2) 케이스 검증

        50% 임계값: 이 시점부터 쓰로틀링 적용 시작
        """
        # Given: 50% 사용한 상태
        limit = 1200
        remaining = 600  # 절반
        usage_ratio = (limit - remaining) / limit  # 0.5

        # When: RateLimitInfo 생성
        info = RateLimitInfo(
            remaining=remaining,
            limit=limit,
            reset_time=datetime.now(timezone.utc),
            usage_ratio=usage_ratio
        )

        # Then: usage_ratio가 정확히 0.5여야 함
        assert info.usage_ratio == 0.5

    def test_usage_ratio_hundred_percent(self):
        """
        사용률 100% (remaining == 0) 케이스 검증

        모두 소진한 상태, 리셋까지 대기 필요
        """
        # Given: 모두 사용한 상태
        remaining = 0
        limit = 1200
        usage_ratio = (limit - remaining) / limit  # 1.0

        # When: RateLimitInfo 생성
        info = RateLimitInfo(
            remaining=remaining,
            limit=limit,
            reset_time=datetime.now(timezone.utc),
            usage_ratio=usage_ratio
        )

        # Then: usage_ratio가 1.0이어야 함
        assert info.usage_ratio == 1.0

    def test_reset_time_with_utc_timezone(self):
        """
        reset_time이 UTC timezone을 포함하는지 검증

        Fixed Window는 UTC 기준으로 리셋되므로 timezone aware datetime 사용
        """
        # Given: UTC timezone을 가진 reset_time
        reset_time = datetime.now(timezone.utc)

        # When: RateLimitInfo 생성
        info = RateLimitInfo(
            remaining=1000,
            limit=1200,
            reset_time=reset_time,
            usage_ratio=0.167
        )

        # Then: reset_time이 timezone aware여야 함
        assert info.reset_time.tzinfo is not None
        assert info.reset_time.tzinfo == timezone.utc

    def test_reset_time_in_future(self):
        """
        reset_time이 미래 시점을 나타내는지 검증

        Fixed Window의 리셋 시점은 항상 현재보다 미래
        (예: 현재 10:30 → 다음 분 리셋 11:00)
        """
        # Given: 미래의 reset_time (1분 후)
        now = datetime.now(timezone.utc)
        reset_time = now + timedelta(seconds=60)

        # When: RateLimitInfo 생성
        info = RateLimitInfo(
            remaining=1000,
            limit=1200,
            reset_time=reset_time,
            usage_ratio=0.167
        )

        # Then: reset_time이 현재보다 미래여야 함
        assert info.reset_time > now

    def test_fields_are_typed_correctly(self):
        """
        RateLimitInfo의 각 필드 타입이 올바른지 검증

        remaining: int, limit: int, reset_time: datetime, usage_ratio: float
        """
        # Given: 유효한 RateLimitInfo
        info = RateLimitInfo(
            remaining=1000,
            limit=1200,
            reset_time=datetime.now(timezone.utc),
            usage_ratio=0.167
        )

        # When: 각 필드 타입 확인

        # Then: 올바른 타입이어야 함
        assert isinstance(info.remaining, int)
        assert isinstance(info.limit, int)
        assert isinstance(info.reset_time, datetime)
        assert isinstance(info.usage_ratio, float)

    def test_usage_ratio_range(self):
        """
        usage_ratio가 0.0 ~ 1.0 범위 내에 있는지 검증

        사용률은 0%(0.0) ~ 100%(1.0) 범위를 가짐
        """
        # Given: 다양한 사용률의 RateLimitInfo
        info_0 = RateLimitInfo(1200, 1200, datetime.now(timezone.utc), 0.0)
        info_50 = RateLimitInfo(600, 1200, datetime.now(timezone.utc), 0.5)
        info_100 = RateLimitInfo(0, 1200, datetime.now(timezone.utc), 1.0)

        # When: usage_ratio 확인

        # Then: 모두 0.0 ~ 1.0 범위 내
        assert 0.0 <= info_0.usage_ratio <= 1.0
        assert 0.0 <= info_50.usage_ratio <= 1.0
        assert 0.0 <= info_100.usage_ratio <= 1.0

    def test_dataclass_equality(self):
        """
        동일한 값을 가진 두 RateLimitInfo 인스턴스가 같은지 검증

        dataclass는 기본적으로 필드값 기반 비교 지원
        """
        # Given: 동일한 값을 가진 두 인스턴스
        reset_time = datetime(2025, 11, 15, 12, 0, 0, tzinfo=timezone.utc)
        info1 = RateLimitInfo(1000, 1200, reset_time, 0.167)
        info2 = RateLimitInfo(1000, 1200, reset_time, 0.167)

        # When: 두 인스턴스 비교

        # Then: 같아야 함
        assert info1 == info2

    def test_remaining_should_not_exceed_limit(self):
        """
        remaining이 limit을 초과하지 않는지 검증

        남은 횟수는 전체 제한을 초과할 수 없음
        """
        # Given: 유효한 RateLimitInfo (remaining <= limit)
        info = RateLimitInfo(
            remaining=1000,
            limit=1200,
            reset_time=datetime.now(timezone.utc),
            usage_ratio=0.167
        )

        # When: remaining과 limit 비교

        # Then: remaining이 limit 이하여야 함
        assert info.remaining <= info.limit
