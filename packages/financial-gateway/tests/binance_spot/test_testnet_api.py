"""
Binance Testnet API 실제 호출 테스트
실제 API 응답 형식 확인용
"""
import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from binance.spot import Spot

# .env 파일 로드 (packages/financial-gateway/.env)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Testnet API 키가 있을 때만 실행
TESTNET_API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
TESTNET_API_SECRET = os.getenv("BINANCE_TESTNET_API_SECRET")

pytestmark = pytest.mark.skipif(
    not TESTNET_API_KEY or not TESTNET_API_SECRET,
    reason="Testnet API keys not configured"
)


class TestBinanceTestnetAPI:
    """Binance Testnet API 실제 호출 테스트"""

    def setup_method(self):
        """테스트 클라이언트 초기화"""
        import time

        self.client = Spot(
            api_key=TESTNET_API_KEY,
            api_secret=TESTNET_API_SECRET,
            base_url="https://testnet.binance.vision"
        )

        # 서버 시간과 로컬 시간 오프셋 계산
        server_time = self.client.time()
        local_time = int(time.time() * 1000)
        self.time_offset = server_time['serverTime'] - local_time
        print(f"\n[Time Sync] Local: {local_time}, Server: {server_time['serverTime']}, Offset: {self.time_offset}ms")

    def test_get_server_time(self):
        """서버 시간 조회 (Public API)"""
        response = self.client.time()
        print("\n=== Server Time Response ===")
        print(response)

        assert "serverTime" in response
        assert isinstance(response["serverTime"], int)

    def test_get_exchange_info(self):
        """거래소 정보 조회 (Public API)"""
        response = self.client.exchange_info(symbol="BTCUSDT")
        print("\n=== Exchange Info Response ===")
        print(response)

        assert "symbols" in response

    def test_get_ticker_24hr(self):
        """24시간 Ticker 조회 (Public API)"""
        response = self.client.ticker_24hr(symbol="BTCUSDT")
        print("\n=== 24hr Ticker Response ===")
        print(response)

        assert "symbol" in response
        assert "lastPrice" in response
        assert "openPrice" in response
        assert "highPrice" in response
        assert "lowPrice" in response

    def test_get_order_book(self):
        """호가 정보 조회 (Public API)"""
        response = self.client.depth(symbol="BTCUSDT", limit=5)
        print("\n=== Order Book Response ===")
        print(response)

        assert "bids" in response
        assert "asks" in response
        assert isinstance(response["bids"], list)
        if len(response["bids"]) > 0:
            print(f"Bid example: {response['bids'][0]}")
            print(f"Bid type: {type(response['bids'][0])}")

    @pytest.mark.skip(reason="binance-connector 라이브러리가 로컬 timestamp 사용 - PC 시간 동기화 필요")
    def test_get_account_info(self):
        """계정 정보 조회 (Private API)"""
        import time

        # 매번 서버 시간을 직접 조회해서 사용 (가장 정확)
        server_time_response = self.client.time()
        server_timestamp = server_time_response['serverTime']

        print(f"\n[Using Server Time] {server_timestamp}")

        # 서버 타임스탬프로 요청 (조회 직후이므로 최대한 정확)
        response = self.client.account(timestamp=server_timestamp, recvWindow=10000)
        print("\n=== Account Info Response ===")
        print(response)

        assert "balances" in response
        if len(response["balances"]) > 0:
            print(f"Balance example: {response['balances'][0]}")
            print(f"Balance keys: {response['balances'][0].keys()}")

    @pytest.mark.skip(reason="Private API - 실제 주문은 수동 실행 권장")
    def test_create_test_order(self):
        """테스트 주문 생성 (POST /api/v3/order/test)"""
        # Test order (실제 체결 안됨)
        response = self.client.new_order_test(
            symbol="BTCUSDT",
            side="BUY",
            type="LIMIT",
            timeInForce="GTC",
            quantity=0.001,
            price=20000
        )
        print("\n=== Test Order Response ===")
        print(response)


if __name__ == "__main__":
    # 직접 실행 시 (pytest 없이)
    print("Binance Testnet API 응답 확인")
    print("=" * 50)

    if not TESTNET_API_KEY:
        print("[ERROR] BINANCE_TESTNET_API_KEY 환경변수 필요")
        print("Testnet에서 API 키 발급: https://testnet.binance.vision/")
        exit(1)

    test = TestBinanceTestnetAPI()
    test.setup_method()

    print("\n1. Server Time:")
    test.test_get_server_time()

    print("\n2. 24hr Ticker:")
    test.test_get_ticker_24hr()

    print("\n3. Order Book:")
    test.test_get_order_book()

    print("\n[OK] Public API 테스트 완료")
    print("Private API 테스트는 pytest로 실행하세요:")
    print("  pytest tests/binance_spot/test_testnet_api.py::TestBinanceTestnetAPI::test_get_account_info -v -s")
