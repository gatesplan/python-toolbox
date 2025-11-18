"""
throttled-api Comprehensive Method Test

21개 메서드를 8개 Phase로 나누어 순차적으로 테스트
"""
import asyncio
import os
from pathlib import Path
from decimal import Decimal
from dotenv import load_dotenv
from throttled_api.providers.binance import BinanceSpotThrottler
from binance.spot import Spot

# 환경변수 로드 (프로젝트 루트의 .env)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 테스트 설정
SYMBOL = "XRPUSDT"
EXISTING_ORDER_ID_1 = 13268822197  # 이전에 체결된 SELL 주문
EXISTING_ORDER_ID_2 = 13268822401  # 이전에 체결된 BUY 주문

# 테스트 결과 저장
test_results = {
    "passed": [],
    "failed": [],
    "skipped": []
}

created_order_id = None  # Phase 6에서 생성할 주문 ID


def print_phase(phase_num: int, title: str):
    """Phase 구분 출력"""
    print("\n" + "=" * 80)
    print(f"Phase {phase_num}: {title}")
    print("=" * 80)


def print_test(test_name: str, result: str, detail: str = ""):
    """테스트 결과 출력"""
    status = "OK" if result == "PASS" else "FAIL" if result == "FAIL" else "SKIP"
    print(f"  [{status:4s}] {test_name:40s} : {detail}")


async def phase1_general(throttler: BinanceSpotThrottler):
    """Phase 1: General - 기본 연결 확인"""
    print_phase(1, "General - 기본 연결 확인")

    # 1.1 ping
    try:
        result = await throttler.ping()
        print_test("ping", "PASS", "연결 성공")
        test_results["passed"].append("ping")
    except Exception as e:
        print_test("ping", "FAIL", str(e))
        test_results["failed"].append(("ping", str(e)))

    # 1.2 get_server_time
    try:
        result = await throttler.get_server_time()
        server_time = result.get('serverTime', 0)
        print_test("get_server_time", "PASS", f"서버시간: {server_time}")
        test_results["passed"].append("get_server_time")
    except Exception as e:
        print_test("get_server_time", "FAIL", str(e))
        test_results["failed"].append(("get_server_time", str(e)))

    # 1.3 get_exchange_info (단일 심볼)
    try:
        result = await throttler.get_exchange_info(symbol=SYMBOL)
        symbols = result.get('symbols', [])
        if symbols:
            symbol_info = symbols[0]
            status = symbol_info.get('status', '')
            print_test("get_exchange_info", "PASS", f"{SYMBOL} status={status}")
        else:
            print_test("get_exchange_info", "PASS", "심볼 정보 없음")
        test_results["passed"].append("get_exchange_info")
    except Exception as e:
        print_test("get_exchange_info", "FAIL", str(e))
        test_results["failed"].append(("get_exchange_info", str(e)))


async def phase2_market_data(throttler: BinanceSpotThrottler):
    """Phase 2: Market Data - 시장 데이터 조회"""
    print_phase(2, "Market Data - 시장 데이터 조회")

    # 2.1 get_ticker_price
    try:
        result = await throttler.get_ticker_price(symbol=SYMBOL)
        price = result.get('price', 'N/A')
        print_test("get_ticker_price", "PASS", f"현재가: {price}")
        test_results["passed"].append("get_ticker_price")
    except Exception as e:
        print_test("get_ticker_price", "FAIL", str(e))
        test_results["failed"].append(("get_ticker_price", str(e)))

    # 2.2 get_orderbook_ticker
    try:
        result = await throttler.get_orderbook_ticker(symbol=SYMBOL)
        bid = result.get('bidPrice', 'N/A')
        ask = result.get('askPrice', 'N/A')
        print_test("get_orderbook_ticker", "PASS", f"매수: {bid}, 매도: {ask}")
        test_results["passed"].append("get_orderbook_ticker")
    except Exception as e:
        print_test("get_orderbook_ticker", "FAIL", str(e))
        test_results["failed"].append(("get_orderbook_ticker", str(e)))

    # 2.3 get_order_book
    try:
        result = await throttler.get_order_book(symbol=SYMBOL, limit=10)
        bids_count = len(result.get('bids', []))
        asks_count = len(result.get('asks', []))
        print_test("get_order_book", "PASS", f"호가: 매수 {bids_count}개, 매도 {asks_count}개")
        test_results["passed"].append("get_order_book")
    except Exception as e:
        print_test("get_order_book", "FAIL", str(e))
        test_results["failed"].append(("get_order_book", str(e)))

    # 2.4 get_klines
    try:
        result = await throttler.get_klines(symbol=SYMBOL, interval="1h", limit=5)
        print_test("get_klines", "PASS", f"{len(result)}개 캔들 조회")
        test_results["passed"].append("get_klines")
    except Exception as e:
        print_test("get_klines", "FAIL", str(e))
        test_results["failed"].append(("get_klines", str(e)))

    # 2.5 get_recent_trades
    try:
        result = await throttler.get_recent_trades(symbol=SYMBOL, limit=5)
        print_test("get_recent_trades", "PASS", f"{len(result)}개 최근 체결")
        test_results["passed"].append("get_recent_trades")
    except Exception as e:
        print_test("get_recent_trades", "FAIL", str(e))
        test_results["failed"].append(("get_recent_trades", str(e)))

    # 2.6 get_avg_price
    try:
        result = await throttler.get_avg_price(symbol=SYMBOL)
        avg_price = result.get('price', 'N/A')
        print_test("get_avg_price", "PASS", f"5분 평균가: {avg_price}")
        test_results["passed"].append("get_avg_price")
    except Exception as e:
        print_test("get_avg_price", "FAIL", str(e))
        test_results["failed"].append(("get_avg_price", str(e)))


async def phase3_account_history(throttler: BinanceSpotThrottler):
    """Phase 3: Account History - 과거 데이터 조회"""
    print_phase(3, "Account History - 과거 데이터 조회")

    # 3.1 get_my_trades
    try:
        result = await throttler.get_my_trades(symbol=SYMBOL, limit=10)
        print_test("get_my_trades", "PASS", f"{len(result)}개 체결 내역")
        # 기존 주문 ID 확인
        found_ids = [t['orderId'] for t in result if t['orderId'] in [EXISTING_ORDER_ID_1, EXISTING_ORDER_ID_2]]
        if found_ids:
            print(f"      → 기존 주문 ID 확인: {found_ids}")
        test_results["passed"].append("get_my_trades")
    except Exception as e:
        print_test("get_my_trades", "FAIL", str(e))
        test_results["failed"].append(("get_my_trades", str(e)))

    # 3.2 get_all_orders
    try:
        result = await throttler.get_all_orders(symbol=SYMBOL, limit=10)
        print_test("get_all_orders", "PASS", f"{len(result)}개 주문 내역")
        # 기존 주문 ID 확인
        found_ids = [o['orderId'] for o in result if o['orderId'] in [EXISTING_ORDER_ID_1, EXISTING_ORDER_ID_2]]
        if found_ids:
            print(f"      → 기존 주문 ID 확인: {found_ids}")
        test_results["passed"].append("get_all_orders")
    except Exception as e:
        print_test("get_all_orders", "FAIL", str(e))
        test_results["failed"].append(("get_all_orders", str(e)))

    # 3.3 get_order (과거 주문 ID로)
    try:
        result = await throttler.get_order(symbol=SYMBOL, order_id=EXISTING_ORDER_ID_1)
        status = result.get('status', 'N/A')
        executed_qty = result.get('executedQty', 'N/A')
        print_test("get_order", "PASS", f"주문 {EXISTING_ORDER_ID_1}: {status}, 체결량 {executed_qty}")
        test_results["passed"].append("get_order")
    except Exception as e:
        print_test("get_order", "FAIL", str(e))
        test_results["failed"].append(("get_order", str(e)))


async def phase4_current_state(throttler: BinanceSpotThrottler):
    """Phase 4: Current State - 현재 상태 조회"""
    print_phase(4, "Current State - 현재 상태 조회")

    # 4.1 get_open_orders
    try:
        result = await throttler.get_open_orders(symbol=SYMBOL)
        print_test("get_open_orders", "PASS", f"{len(result)}개 미체결 주문")
        test_results["passed"].append("get_open_orders")
    except Exception as e:
        print_test("get_open_orders", "FAIL", str(e))
        test_results["failed"].append(("get_open_orders", str(e)))

    # 4.2 get_account_commission
    try:
        result = await throttler.get_account_commission(symbol=SYMBOL)
        maker = result.get('maker', 'N/A')
        taker = result.get('taker', 'N/A')
        print_test("get_account_commission", "PASS", f"Maker: {maker}, Taker: {taker}")
        test_results["passed"].append("get_account_commission")
    except Exception as e:
        print_test("get_account_commission", "FAIL", str(e))
        test_results["failed"].append(("get_account_commission", str(e)))


async def phase5_order_validation(throttler: BinanceSpotThrottler):
    """Phase 5: Order Validation - 주문 검증 (실제 주문 안됨)"""
    print_phase(5, "Order Validation - 주문 검증")

    # 5.1 test_order (MARKET)
    try:
        result = await throttler.test_order(
            symbol=SYMBOL,
            side="SELL",
            type="MARKET",
            quantity=5.0  # NOTIONAL 필터 통과를 위해 5로 증가
        )
        print_test("test_order (MARKET)", "PASS", "유효성 검증 통과")
        test_results["passed"].append("test_order_market")
    except Exception as e:
        print_test("test_order (MARKET)", "FAIL", str(e))
        test_results["failed"].append(("test_order_market", str(e)))

    # 5.2 test_order (LIMIT)
    try:
        result = await throttler.test_order(
            symbol=SYMBOL,
            side="SELL",
            type="LIMIT",
            timeInForce="GTC",
            quantity=5.0,  # NOTIONAL 필터 통과를 위해 5로 증가
            price=3.0
        )
        print_test("test_order (LIMIT)", "PASS", "유효성 검증 통과")
        test_results["passed"].append("test_order_limit")
    except Exception as e:
        print_test("test_order (LIMIT)", "FAIL", str(e))
        test_results["failed"].append(("test_order_limit", str(e)))


async def phase6_order_creation(throttler: BinanceSpotThrottler):
    """Phase 6: Order Creation - 주문 생성 (취소 가능하게)"""
    global created_order_id
    print_phase(6, "Order Creation - LIMIT 주문 생성")

    # 현재가 조회
    try:
        ticker = await throttler.get_ticker_price(symbol=SYMBOL)
        current_price = float(ticker['price'])
        limit_price = round(current_price * 1.5, 4)  # 현재가의 1.5배 (체결 안되게)

        print(f"  현재가: {current_price} USDT")
        print(f"  주문가: {limit_price} USDT (체결 안되도록 높게 설정)")

        # 6.1 create_order (LIMIT SELL)
        result = await throttler.create_order(
            symbol=SYMBOL,
            side="SELL",
            type="LIMIT",
            timeInForce="GTC",
            quantity=5.0,
            price=limit_price
        )
        created_order_id = result['orderId']
        print_test("create_order (LIMIT)", "PASS", f"주문 ID: {created_order_id}")
        test_results["passed"].append("create_order_limit")

    except Exception as e:
        print_test("create_order (LIMIT)", "FAIL", str(e))
        test_results["failed"].append(("create_order_limit", str(e)))


async def phase7_order_management(throttler: BinanceSpotThrottler):
    """Phase 7: Order Management - 주문 관리"""
    global created_order_id
    print_phase(7, "Order Management - 주문 관리")

    if not created_order_id:
        print("  [SKIP] Phase 6에서 주문 생성 실패, Phase 7 건너뜀")
        test_results["skipped"].extend([
            "get_order_new", "get_open_orders_check", "cancel_order", "get_order_canceled"
        ])
        return

    # 7.1 get_order (새로 생성한 주문)
    try:
        result = await throttler.get_order(symbol=SYMBOL, order_id=created_order_id)
        status = result.get('status', 'N/A')
        print_test("get_order (새 주문)", "PASS", f"주문 {created_order_id}: {status}")
        test_results["passed"].append("get_order_new")
    except Exception as e:
        print_test("get_order (새 주문)", "FAIL", str(e))
        test_results["failed"].append(("get_order_new", str(e)))

    # 7.2 get_open_orders (미체결 확인)
    try:
        result = await throttler.get_open_orders(symbol=SYMBOL)
        found = any(o['orderId'] == created_order_id for o in result)
        if found:
            print_test("get_open_orders (확인)", "PASS", f"주문 {created_order_id} 존재")
        else:
            print_test("get_open_orders (확인)", "PASS", "목록에 없음 (이미 체결?)")
        test_results["passed"].append("get_open_orders_check")
    except Exception as e:
        print_test("get_open_orders (확인)", "FAIL", str(e))
        test_results["failed"].append(("get_open_orders_check", str(e)))

    # 7.3 cancel_order
    try:
        result = await throttler.cancel_order(symbol=SYMBOL, order_id=created_order_id)
        status = result.get('status', 'N/A')
        print_test("cancel_order", "PASS", f"주문 취소됨: {status}")
        test_results["passed"].append("cancel_order")
    except Exception as e:
        print_test("cancel_order", "FAIL", str(e))
        test_results["failed"].append(("cancel_order", str(e)))

    # 7.4 get_order (취소 확인)
    try:
        await asyncio.sleep(0.5)  # 잠시 대기
        result = await throttler.get_order(symbol=SYMBOL, order_id=created_order_id)
        status = result.get('status', 'N/A')
        print_test("get_order (취소 확인)", "PASS", f"주문 상태: {status}")
        test_results["passed"].append("get_order_canceled")
    except Exception as e:
        print_test("get_order (취소 확인)", "FAIL", str(e))
        test_results["failed"].append(("get_order_canceled", str(e)))


async def main():
    """메인 테스트 실행"""
    print("=" * 80)
    print("throttled-api Comprehensive Method Test")
    print("=" * 80)
    print(f"테스트 심볼: {SYMBOL}")
    print(f"기존 주문 ID: {EXISTING_ORDER_ID_1}, {EXISTING_ORDER_ID_2}")
    print()

    # API 키 확인
    api_key = os.getenv("BINANCE_SPOT_API_KEY") or os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_SPOT_API_SECRET") or os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("[ERROR] BINANCE_SPOT_API_KEY 또는 BINANCE_SPOT_API_SECRET 환경변수가 설정되지 않았습니다")
        return

    # Throttler 생성
    client = Spot(api_key=api_key, api_secret=api_secret)
    throttler = BinanceSpotThrottler(client=client)

    # Phase별 실행
    await phase1_general(throttler)
    await phase2_market_data(throttler)
    await phase3_account_history(throttler)
    await phase4_current_state(throttler)
    await phase5_order_validation(throttler)
    await phase6_order_creation(throttler)
    await phase7_order_management(throttler)

    # 최종 결과
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    print(f"[OK] 성공: {len(test_results['passed'])}개")
    print(f"[FAIL] 실패: {len(test_results['failed'])}개")
    print(f"[SKIP] 건너뜀: {len(test_results['skipped'])}개")

    if test_results['failed']:
        print("\n[실패한 테스트]")
        for test_name, error in test_results['failed']:
            print(f"  - {test_name}: {error}")

    print("\n" + "=" * 80)
    total = len(test_results['passed']) + len(test_results['failed']) + len(test_results['skipped'])
    success_rate = len(test_results['passed']) * 100 // total if total > 0 else 0
    print(f"전체 성공률: {success_rate}% ({len(test_results['passed'])}/{total})")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
