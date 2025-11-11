"""MarketData 테스트"""

import pytest
from financial_assets.price import Price
from .MarketData import MarketData


def make_price(t: int, o: float, h: float, l: float, c: float, v: float) -> Price:
    """테스트용 Price 생성 헬퍼"""
    return Price("binance", "spot", t=t, o=o, h=h, l=l, c=c, v=v)


class TestMarketDataInit:
    """초기화 테스트"""

    def test_init_basic(self):
        """기본 초기화"""
        data = {
            "BTC/USDT": [
                make_price(t=1000, o=50000, h=51000, l=49000, c=50500, v=100),
                make_price(t=2000, o=50500, h=52000, l=50000, c=51000, v=150),
            ],
            "ETH/USDT": [
                make_price(t=1000, o=3000, h=3100, l=2900, c=3050, v=200),
                make_price(t=2000, o=3050, h=3200, l=3000, c=3150, v=250),
            ],
        }
        market = MarketData(data)
        assert market.get_cursor() >= 0
        assert market.get_max_length() == 2
        assert len(market.get_symbols()) == 2

    def test_init_empty_data(self):
        """빈 데이터로 초기화 시 에러"""
        with pytest.raises(ValueError):
            MarketData({})

    def test_init_with_offset(self):
        """offset 적용 초기화"""
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000 + i, h=51000, l=49000, c=50500, v=100) for i in range(10)],
        }
        market = MarketData(data, offset=5)
        # offset만큼 시작점이 이동되어야 함
        assert market.get_cursor() >= 5

    def test_init_variable_length_data(self):
        """심볼별 길이가 다른 데이터 (뒤 끝 정렬)"""
        # 모든 심볼의 마지막 타임스탬프는 9000으로 동일
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(10)],  # 0~9000
            "ETH/USDT": [make_price(t=i * 1000, o=3000, h=3100, l=2900, c=3050, v=200) for i in range(5, 10)],  # 5000~9000
            "XRP/USDT": [make_price(t=i * 1000, o=1, h=1.1, l=0.9, c=1.05, v=1000) for i in range(2, 10)],  # 2000~9000
        }
        market = MarketData(data)
        assert market.get_max_length() == 10

    def test_init_availability_threshold(self):
        """availability_threshold 기반 시작점 찾기 (뒤 끝 정렬)"""
        # BTC: 10개 (0~9000), ETH: 5개 (5000~9000)
        # 커서 0~4: BTC만 (availability=0.5)
        # 커서 5~9: BTC, ETH 둘 다 (availability=1.0)
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(10)],  # 0~9000
            "ETH/USDT": [make_price(t=i * 1000, o=3000, h=3100, l=2900, c=3050, v=200) for i in range(5, 10)],  # 5000~9000
        }
        # threshold 0.5면 1개 이상 유효하면 됨 (2개 중 1개) -> 커서 0부터 가능
        market = MarketData(data, availability_threshold=0.5)
        assert market.get_cursor() >= 0

        # threshold 1.0이면 모든 심볼이 유효해야 함 -> 커서 5부터 가능
        market = MarketData(data, availability_threshold=1.0)
        assert market.get_cursor() >= 5


class TestMarketDataQuery:
    """데이터 조회 테스트"""

    @pytest.fixture
    def market_data(self):
        """테스트용 MarketData"""
        data = {
            "BTC/USDT": [
                make_price(t=1000, o=50000, h=51000, l=49000, c=50500, v=100),
                make_price(t=2000, o=50500, h=52000, l=50000, c=51000, v=150),
                make_price(t=3000, o=51000, h=53000, l=51000, c=52000, v=200),
            ],
            "ETH/USDT": [
                make_price(t=1000, o=3000, h=3100, l=2900, c=3050, v=200),
                make_price(t=2000, o=3050, h=3200, l=3000, c=3150, v=250),
                make_price(t=3000, o=3150, h=3300, l=3100, c=3250, v=300),
            ],
        }
        return MarketData(data, availability_threshold=0.5, offset=0)

    def test_get_current(self, market_data):
        """특정 심볼의 현재 가격 조회"""
        price = market_data.get_current("BTC/USDT")
        assert price is not None
        assert price.o == 50000

    def test_get_current_invalid_symbol(self, market_data):
        """존재하지 않는 심볼 조회"""
        price = market_data.get_current("INVALID/USDT")
        assert price is None

    def test_get_current_all(self, market_data):
        """모든 심볼의 현재 가격 조회"""
        prices = market_data.get_current_all()
        assert len(prices) == 2
        assert "BTC/USDT" in prices
        assert "ETH/USDT" in prices

    def test_get_current_timestamp(self, market_data):
        """타임스탬프 조회"""
        timestamp = market_data.get_current_timestamp("BTC/USDT")
        assert timestamp == 1000

    def test_get_symbols(self, market_data):
        """심볼 리스트 조회"""
        symbols = market_data.get_symbols()
        assert len(symbols) == 2
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols


class TestMarketDataStep:
    """커서 이동 테스트"""

    def test_step_basic(self):
        """기본 step 동작"""
        data = {
            "BTC/USDT": [
                make_price(t=1000, o=50000, h=51000, l=49000, c=50500, v=100),
                make_price(t=2000, o=50500, h=52000, l=50000, c=51000, v=150),
            ],
        }
        market = MarketData(data, offset=0)
        initial_cursor = market.get_cursor()

        success = market.step()
        assert success is True
        assert market.get_cursor() == initial_cursor + 1

    def test_step_until_end(self):
        """끝까지 step"""
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(3)],
        }
        market = MarketData(data, offset=0)

        # 끝까지 이동
        while market.step():
            pass

        assert market.is_finished() is True
        # 끝에서 step 호출 시 False
        assert market.step() is False

    def test_step_changes_current(self):
        """step 후 current 값 변경 확인"""
        data = {
            "BTC/USDT": [
                make_price(t=1000, o=50000, h=51000, l=49000, c=50500, v=100),
                make_price(t=2000, o=50500, h=52000, l=50000, c=51000, v=150),
            ],
        }
        market = MarketData(data, offset=0)

        first_price = market.get_current("BTC/USDT")
        market.step()
        second_price = market.get_current("BTC/USDT")

        assert first_price.t != second_price.t
        assert second_price.t == 2000


class TestMarketDataReset:
    """리셋 테스트"""

    def test_reset_basic(self):
        """기본 reset"""
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(5)],
        }
        market = MarketData(data, offset=0)
        initial_cursor = market.get_cursor()

        # 몇 번 이동
        market.step()
        market.step()
        assert market.get_cursor() != initial_cursor

        # 리셋
        market.reset()
        assert market.get_cursor() == initial_cursor

    def test_reset_without_override(self):
        """override=False 리셋 (같은 시작점)"""
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(10)],
        }
        market = MarketData(data, random_additional_offset=True)
        first_start = market.get_cursor()

        market.step()
        market.step()
        market.reset(override=False)

        assert market.get_cursor() == first_start

    def test_reset_with_override(self):
        """override=True 리셋 (새로운 랜덤 시작점)"""
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(100)],
        }
        market = MarketData(data, random_additional_offset=True, offset=0)
        first_start = market.get_cursor()

        # override=True로 여러 번 리셋
        cursors = [first_start]
        for _ in range(10):
            market.reset(override=True)
            cursors.append(market.get_cursor())

        # 최소한 한 번은 달라야 함 (확률적으로)
        assert len(set(cursors)) > 1

    def test_reset_without_random_offset(self):
        """random_additional_offset=False일 때 override=True는 무의미"""
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(10)],
        }
        market = MarketData(data, random_additional_offset=False, offset=0)
        first_start = market.get_cursor()

        # override=True여도 random_additional_offset=False면 같은 시작점
        market.reset(override=True)
        assert market.get_cursor() == first_start


class TestMarketDataState:
    """상태 조회 테스트"""

    def test_is_finished(self):
        """종료 여부 확인"""
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(3)],
        }
        market = MarketData(data, offset=0)

        assert market.is_finished() is False

        # 끝까지 이동
        while market.step():
            pass

        assert market.is_finished() is True

    def test_get_progress(self):
        """진행률 확인"""
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(10)],
        }
        market = MarketData(data, offset=0)

        # 시작
        progress = market.get_progress()
        assert 0.0 <= progress <= 1.0

        # 중간
        for _ in range(5):
            market.step()
        mid_progress = market.get_progress()
        assert mid_progress > progress

        # 끝
        while market.step():
            pass
        final_progress = market.get_progress()
        assert final_progress == 1.0

    def test_get_availability(self):
        """데이터 유효성 비율 확인 (뒤 끝 정렬)"""
        # BTC: 10개 (0~9000), ETH: 5개 (5000~9000)
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(10)],  # 0~9000
            "ETH/USDT": [make_price(t=i * 1000, o=3000, h=3100, l=2900, c=3050, v=200) for i in range(5, 10)],  # 5000~9000
        }
        market = MarketData(data, offset=0)

        # 현재 위치 유효성
        availability = market.get_availability()
        assert 0.0 <= availability <= 1.0

        # 특정 위치 유효성
        availability_at_0 = market.get_availability(0)
        availability_at_9 = market.get_availability(9)

        # 커서 0: BTC만 있음 (ETH 시작 인덱스는 5) -> 0.5
        assert availability_at_0 == 0.5
        # 커서 9: BTC, ETH 둘 다 있음 -> 1.0
        assert availability_at_9 == 1.0


class TestMarketDataVariableLength:
    """가변 길이 데이터 테스트"""

    def test_variable_length_get_current(self):
        """길이가 다른 데이터에서 get_current (뒤 끝 정렬)"""
        # BTC: 10개 (0~9000), ETH: 5개 (5000~9000)
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(10)],  # 0~9000
            "ETH/USDT": [make_price(t=i * 1000, o=3000, h=3100, l=2900, c=3050, v=200) for i in range(5, 10)],  # 5000~9000
        }
        market = MarketData(data, offset=0)

        # 끝까지 이동
        while not market.is_finished():
            btc = market.get_current("BTC/USDT")
            eth = market.get_current("ETH/USDT")

            cursor = market.get_cursor()

            # BTC는 항상 있어야 함 (커서 0~9)
            assert btc is not None

            # ETH는 커서 5부터 있음 (시작 인덱스 = 10 - 5 = 5)
            if cursor < 5:
                assert eth is None
            else:
                assert eth is not None

            market.step()

    def test_variable_length_get_current_all(self):
        """길이가 다른 데이터에서 get_current_all (뒤 끝 정렬)"""
        # BTC: 10개 (0~9000), ETH: 5개 (5000~9000)
        # availability_threshold=0.5로 설정하여 커서 0부터 시작
        data = {
            "BTC/USDT": [make_price(t=i * 1000, o=50000, h=51000, l=49000, c=50500, v=100) for i in range(10)],  # 0~9000
            "ETH/USDT": [make_price(t=i * 1000, o=3000, h=3100, l=2900, c=3050, v=200) for i in range(5, 10)],  # 5000~9000
        }
        market = MarketData(data, availability_threshold=0.5, offset=0)

        # 초반 (커서 0): BTC만 있음
        prices = market.get_current_all()
        assert len(prices) == 1
        assert "BTC/USDT" in prices

        # 중반으로 이동 (커서 5): BTC, ETH 둘 다 있음
        for _ in range(5):
            market.step()

        prices = market.get_current_all()
        assert len(prices) == 2
        assert "BTC/USDT" in prices
        assert "ETH/USDT" in prices
