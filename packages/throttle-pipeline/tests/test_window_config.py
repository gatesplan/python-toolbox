import pytest
from throttle_pipeline.particles.window_config import WindowConfig


class TestWindowConfig:
    """WindowConfig dataclass 검증 테스트"""

    def test_create_fixed_window_config(self):
        """
        Fixed Window 타입의 WindowConfig 정상 생성 검증

        Fixed Window는 Binance처럼 UTC 기준 정각에 리셋되는 방식
        (예: 매분 XX:00초, 매일 00:00 UTC)
        """
        # Given: Fixed Window 설정값
        limit = 1200
        interval_seconds = 60
        window_type = "fixed"

        # When: WindowConfig 생성
        config = WindowConfig(
            limit=limit,
            interval_seconds=interval_seconds,
            window_type=window_type
        )

        # Then: 모든 필드가 정상 할당되어야 함
        assert config.limit == 1200
        assert config.interval_seconds == 60
        assert config.window_type == "fixed"

    def test_create_sliding_window_config(self):
        """
        Sliding Window 타입의 WindowConfig 정상 생성 검증

        Sliding Window는 Upbit처럼 첫 요청 시점부터
        고정된 시간(60초 등) 동안 윈도우가 유지되는 방식
        """
        # Given: Sliding Window 설정값
        limit = 200
        interval_seconds = 60
        window_type = "sliding"

        # When: WindowConfig 생성
        config = WindowConfig(
            limit=limit,
            interval_seconds=interval_seconds,
            window_type=window_type
        )

        # Then: 모든 필드가 정상 할당되어야 함
        assert config.limit == 200
        assert config.interval_seconds == 60
        assert config.window_type == "sliding"

    def test_window_config_fields_are_typed_correctly(self):
        """
        WindowConfig의 각 필드 타입이 올바른지 검증

        limit와 interval_seconds는 int, window_type는 str
        """
        # Given: 유효한 설정값
        config = WindowConfig(
            limit=1000,
            interval_seconds=3600,
            window_type="fixed"
        )

        # When: 각 필드 타입 확인

        # Then: 올바른 타입이어야 함
        assert isinstance(config.limit, int)
        assert isinstance(config.interval_seconds, int)
        assert isinstance(config.window_type, str)

    def test_different_interval_windows(self):
        """
        다양한 시간 윈도우(초/분/시간/일) 설정 검증

        다중 윈도우 관리: 1초, 60초(1분), 3600초(1시간), 86400초(1일) 등
        """
        # Given: 다양한 interval의 WindowConfig 리스트

        # When: 각 윈도우 생성
        second_window = WindowConfig(limit=10, interval_seconds=1, window_type="sliding")
        minute_window = WindowConfig(limit=1200, interval_seconds=60, window_type="fixed")
        hour_window = WindowConfig(limit=100000, interval_seconds=3600, window_type="fixed")
        day_window = WindowConfig(limit=200000, interval_seconds=86400, window_type="fixed")

        # Then: 모든 윈도우가 정상 생성되어야 함
        assert second_window.interval_seconds == 1
        assert minute_window.interval_seconds == 60
        assert hour_window.interval_seconds == 3600
        assert day_window.interval_seconds == 86400

    def test_window_type_validation_valid_types(self):
        """
        window_type 필드가 "fixed" 또는 "sliding"인지 검증

        두 가지 윈도우 타입만 지원:
        - fixed: UTC 기준 정각 리셋 (Binance)
        - sliding: 첫 요청 기준 윈도우 (Upbit)
        """
        # Given: 유효한 window_type 값들
        valid_types = ["fixed", "sliding"]

        # When: 각 타입으로 WindowConfig 생성
        for window_type in valid_types:
            config = WindowConfig(
                limit=100,
                interval_seconds=60,
                window_type=window_type
            )

            # Then: 정상 생성되고 window_type이 올바르게 할당
            assert config.window_type in valid_types

    def test_window_type_invalid_should_be_handled(self):
        """
        window_type이 "fixed"나 "sliding"이 아닐 때 처리 검증

        잘못된 타입(예: "unknown")은 생성 후 검증 단계에서 처리되어야 함
        (dataclass 자체는 문자열을 허용하므로 생성은 가능하지만,
        사용 시점에 WindowTracker 등에서 validation 필요)
        """
        # Given: 잘못된 window_type

        # When: 잘못된 타입으로 WindowConfig 생성
        config = WindowConfig(
            limit=100,
            interval_seconds=60,
            window_type="unknown"
        )

        # Then: 생성은 되지만 유효하지 않은 타입임
        assert config.window_type not in ["fixed", "sliding"]
        # 실제 사용 시 WindowTracker 등에서 검증 필요

    def test_positive_limit_and_interval(self):
        """
        limit과 interval_seconds가 양수인지 검증

        음수나 0은 의미가 없으므로 양수여야 함
        """
        # Given: 양수 값들
        config = WindowConfig(
            limit=1000,
            interval_seconds=60,
            window_type="fixed"
        )

        # When: 값 확인

        # Then: 모두 양수여야 함
        assert config.limit > 0
        assert config.interval_seconds > 0

    def test_dataclass_equality(self):
        """
        동일한 값을 가진 두 WindowConfig 인스턴스가 같은지 검증

        dataclass는 기본적으로 __eq__ 구현되어 있어 필드값 기반 비교 가능
        """
        # Given: 동일한 값을 가진 두 인스턴스
        config1 = WindowConfig(limit=1200, interval_seconds=60, window_type="fixed")
        config2 = WindowConfig(limit=1200, interval_seconds=60, window_type="fixed")

        # When: 두 인스턴스 비교

        # Then: 같아야 함
        assert config1 == config2

    def test_dataclass_inequality(self):
        """
        다른 값을 가진 두 WindowConfig 인스턴스가 다른지 검증
        """
        # Given: 다른 값을 가진 두 인스턴스
        config1 = WindowConfig(limit=1200, interval_seconds=60, window_type="fixed")
        config2 = WindowConfig(limit=200, interval_seconds=60, window_type="sliding")

        # When: 두 인스턴스 비교

        # Then: 달라야 함
        assert config1 != config2
