import pytest
from throttle_pipeline.particles.throttle_config import ThrottleConfig


class TestThrottleConfig:
    """ThrottleConfig dataclass 검증 테스트"""

    def test_create_with_default_values(self):
        """
        기본값으로 ThrottleConfig 생성 검증

        모든 필드에 기본값이 제공되어 인자 없이 생성 가능
        기본값: throttle_threshold=0.5, usage_history_size=100,
               min_usage_samples=10, short_window_threshold=10
        """
        # Given: 기본값 사용

        # When: 인자 없이 ThrottleConfig 생성
        config = ThrottleConfig()

        # Then: 모든 필드가 기본값으로 설정되어야 함
        assert config.throttle_threshold == 0.5
        assert config.usage_history_size == 100
        assert config.min_usage_samples == 10
        assert config.short_window_threshold == 10

    def test_create_with_custom_values(self):
        """
        커스텀 값으로 ThrottleConfig 생성 검증

        사용자 환경에 맞게 모든 값을 커스터마이징 가능
        예: 보수적 전략(threshold=0.6), 메모리 제약(history=50)
        """
        # Given: 커스텀 설정값
        threshold = 0.6
        history_size = 50
        min_samples = 5
        short_threshold = 5

        # When: 커스텀 값으로 ThrottleConfig 생성
        config = ThrottleConfig(
            throttle_threshold=threshold,
            usage_history_size=history_size,
            min_usage_samples=min_samples,
            short_window_threshold=short_threshold
        )

        # Then: 모든 필드가 커스텀 값으로 설정되어야 함
        assert config.throttle_threshold == 0.6
        assert config.usage_history_size == 50
        assert config.min_usage_samples == 5
        assert config.short_window_threshold == 5

    def test_throttle_threshold_range_validation(self):
        """
        throttle_threshold가 0.0~1.0 범위 밖일 때 검증 실패

        사용률은 0.0(0%)~1.0(100%) 범위이므로 임계값도 동일 범위여야 함
        __post_init__에서 범위 검증
        """
        # Given: 범위 밖 threshold 값들

        # When & Then: 1.0 초과 값으로 생성 시 ValueError
        with pytest.raises(ValueError, match="throttle_threshold must be in"):
            ThrottleConfig(throttle_threshold=1.5)

        # When & Then: 0.0 미만 값으로 생성 시 ValueError
        with pytest.raises(ValueError, match="throttle_threshold must be in"):
            ThrottleConfig(throttle_threshold=-0.1)

    def test_throttle_threshold_boundary_values(self):
        """
        throttle_threshold 경계값(0.0, 1.0) 정상 동작 검증

        0.0과 1.0은 유효한 값으로 정상 생성되어야 함
        """
        # Given & When: 경계값으로 ThrottleConfig 생성
        config_zero = ThrottleConfig(throttle_threshold=0.0)
        config_one = ThrottleConfig(throttle_threshold=1.0)

        # Then: 정상 생성되어야 함
        assert config_zero.throttle_threshold == 0.0
        assert config_one.throttle_threshold == 1.0

    def test_min_samples_not_exceed_history_size(self):
        """
        min_usage_samples가 usage_history_size를 초과하면 검증 실패

        평균 계산에 필요한 최소 샘플이 히스토리 크기보다 크면
        평균 계산이 영원히 불가능하므로 에러
        __post_init__에서 관계 검증
        """
        # Given: min_usage_samples > usage_history_size

        # When & Then: 잘못된 관계로 생성 시 ValueError
        with pytest.raises(ValueError, match="min_usage_samples cannot exceed"):
            ThrottleConfig(usage_history_size=50, min_usage_samples=100)

    def test_min_samples_equal_to_history_size_allowed(self):
        """
        min_usage_samples == usage_history_size 허용

        같은 값은 유효 (히스토리가 꽉 차야 평균 제공)
        """
        # Given: min_usage_samples == usage_history_size

        # When: 같은 값으로 ThrottleConfig 생성
        config = ThrottleConfig(usage_history_size=100, min_usage_samples=100)

        # Then: 정상 생성되어야 함
        assert config.usage_history_size == 100
        assert config.min_usage_samples == 100

    def test_positive_values_validation(self):
        """
        usage_history_size, min_usage_samples, short_window_threshold가
        양수여야 함 검증

        0 이하 값은 의미 없으므로 에러
        """
        # Given: 0 이하 값들

        # When & Then: usage_history_size <= 0
        with pytest.raises(ValueError, match="must be positive"):
            ThrottleConfig(usage_history_size=0)

        with pytest.raises(ValueError, match="must be positive"):
            ThrottleConfig(usage_history_size=-10)

        # When & Then: min_usage_samples <= 0
        with pytest.raises(ValueError, match="must be positive"):
            ThrottleConfig(min_usage_samples=0)

        # When & Then: short_window_threshold <= 0
        with pytest.raises(ValueError, match="must be positive"):
            ThrottleConfig(short_window_threshold=0)

    def test_fields_are_typed_correctly(self):
        """
        ThrottleConfig의 각 필드 타입이 올바른지 검증

        throttle_threshold: float
        usage_history_size, min_usage_samples, short_window_threshold: int
        """
        # Given: 기본값으로 생성된 config
        config = ThrottleConfig()

        # When: 각 필드 타입 확인

        # Then: 올바른 타입이어야 함
        assert isinstance(config.throttle_threshold, float)
        assert isinstance(config.usage_history_size, int)
        assert isinstance(config.min_usage_samples, int)
        assert isinstance(config.short_window_threshold, int)

    def test_dataclass_equality(self):
        """
        동일한 값을 가진 두 ThrottleConfig 인스턴스가 같은지 검증

        dataclass는 기본적으로 필드값 기반 비교 지원
        """
        # Given: 동일한 값을 가진 두 인스턴스
        config1 = ThrottleConfig(
            throttle_threshold=0.6,
            usage_history_size=50,
            min_usage_samples=5,
            short_window_threshold=5
        )
        config2 = ThrottleConfig(
            throttle_threshold=0.6,
            usage_history_size=50,
            min_usage_samples=5,
            short_window_threshold=5
        )

        # When: 두 인스턴스 비교

        # Then: 같아야 함
        assert config1 == config2

    def test_dataclass_inequality(self):
        """
        다른 값을 가진 두 ThrottleConfig 인스턴스가 다른지 검증
        """
        # Given: 다른 값을 가진 두 인스턴스
        config1 = ThrottleConfig(throttle_threshold=0.5)
        config2 = ThrottleConfig(throttle_threshold=0.6)

        # When: 두 인스턴스 비교

        # Then: 달라야 함
        assert config1 != config2

    def test_conservative_strategy_config(self):
        """
        보수적 전략 설정 검증

        threshold를 높이면(예: 0.7) 더 일찍 쓰로틀링 시작
        히스토리를 늘리면(예: 200) 더 많은 샘플 기반 평균 계산
        """
        # Given: 보수적 전략 값

        # When: 보수적 설정으로 ThrottleConfig 생성
        config = ThrottleConfig(
            throttle_threshold=0.7,
            usage_history_size=200,
            min_usage_samples=20
        )

        # Then: 설정값이 기본값보다 보수적이어야 함
        assert config.throttle_threshold > 0.5  # 기본값보다 높음
        assert config.usage_history_size > 100  # 기본값보다 많음

    def test_aggressive_strategy_config(self):
        """
        공격적 전략 설정 검증

        threshold를 낮추면(예: 0.3) 쓰로틀링 늦게 시작
        히스토리를 줄이면(예: 50) 메모리 사용 감소
        """
        # Given: 공격적 전략 값

        # When: 공격적 설정으로 ThrottleConfig 생성
        config = ThrottleConfig(
            throttle_threshold=0.3,
            usage_history_size=50,
            min_usage_samples=5,
            short_window_threshold=3
        )

        # Then: 설정값이 기본값보다 공격적이어야 함
        assert config.throttle_threshold < 0.5  # 기본값보다 낮음
        assert config.usage_history_size < 100  # 기본값보다 적음
