"""
throttled-api Remaining Methods Test (Phase 8-10)

Phase 8: OCO Order (5개)
Phase 9: Additional Market Data (4개)
Phase 10: Order Management Advanced (4개)
"""
import asyncio
import os
from pathlib import Path
from decimal import Decimal
from dotenv import load_dotenv
from throttled_api.providers.binance import BinanceSpotThrottler
from binance.spot import Spot

# 환경변수 로드
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 테스트 설정
SYMBOL = "XRPUSDT"

# 테스트 결과 저장
test_results = {
    "passed": [],
    "failed": [],
    "skipped": []
}

# 테스트 중 생성된 데이터
created_oco_order_list_id = None
created_limit_order_id = None


def print_phase(phase_num: int, title: str):
    """Phase 구분 출력"""
    print("\n" + "=" * 80)
    print(f"Phase {phase_num}: {title}")
    print("=" * 80)


def print_test(test_name: str, result: str, detail: str = ""):
    """테스트 결과 출력"""
    status = "OK" if result == "PASS" else "FAIL" if result == "FAIL" else "SKIP"
    print(f"  [{status:4s}] {test_name:40s} : {detail}")


async def phase8_oco_order(throttler: BinanceSpotThrottler):
    """Phase 8: OCO Order Test"""
    global created_oco_order_list_id
    print_phase(8, "OCO Order - 익절/손절 자동화")

    # 현재가 조회
    try:
        ticker = await throttler.get_ticker_price(symbol=SYMBOL)
        current_price = float(ticker['price'])

        # OCO 파라미터 설정
        quantity = 5.0
        limit_price = round(current_price * 1.38, 4)  # 익절: 현재가 * 1.38
        stop_price = round(current_price * 0.69, 4)   # 손절: 현재가 * 0.69
        stop_limit_price = round(stop_price * 0.99, 4)  # 손절 리밋: 손절가 * 0.99

        print(f"  현재가: {current_price} USDT")
        print(f"  익절가: {limit_price} USDT (체결 안되게)")
        print(f"  손절가: {stop_price} USDT (체결 안되게)")

        # 8.1 create_oco_order
        result = await throttler.create_oco_order(
            symbol=SYMBOL,
            side="SELL",
            quantity=quantity,
            above_type="LIMIT_MAKER",
            below_type="STOP_LOSS_LIMIT",
            price=limit_price,
            belowStopPrice=stop_price,
            belowPrice=stop_limit_price,
            belowTimeInForce="GTC"
        )
        created_oco_order_list_id = result['orderListId']
        print_test("create_oco_order", "PASS", f"orderListId: {created_oco_order_list_id}")
        test_results["passed"].append("create_oco_order")
    except Exception as e:
        print_test("create_oco_order", "FAIL", str(e))
        test_results["failed"].append(("create_oco_order", str(e)))
        return  # OCO 생성 실패 시 나머지 건너뜀

    # 8.2 get_order_list
    try:
        result = await throttler.get_order_list(order_list_id=created_oco_order_list_id)
        list_status = result.get('listOrderStatus', 'N/A')
        orders_count = len(result.get('orders', []))
        print_test("get_order_list", "PASS", f"상태: {list_status}, 주문 {orders_count}개")
        test_results["passed"].append("get_order_list")
    except Exception as e:
        print_test("get_order_list", "FAIL", str(e))
        test_results["failed"].append(("get_order_list", str(e)))

    # 8.3 get_all_order_list
    try:
        result = await throttler.get_all_order_list(limit=10)
        print_test("get_all_order_list", "PASS", f"{len(result)}개 OCO 내역")
        test_results["passed"].append("get_all_order_list")
    except Exception as e:
        print_test("get_all_order_list", "FAIL", str(e))
        test_results["failed"].append(("get_all_order_list", str(e)))

    # 8.4 get_open_order_list
    try:
        result = await throttler.get_open_order_list()
        found = any(o['orderListId'] == created_oco_order_list_id for o in result)
        print_test("get_open_order_list", "PASS", f"{len(result)}개 미체결, OCO {'존재' if found else '없음'}")
        test_results["passed"].append("get_open_order_list")
    except Exception as e:
        print_test("get_open_order_list", "FAIL", str(e))
        test_results["failed"].append(("get_open_order_list", str(e)))

    # 8.5 cancel_order_list
    try:
        await asyncio.sleep(0.5)
        result = await throttler.cancel_order_list(
            symbol=SYMBOL,
            order_list_id=created_oco_order_list_id
        )
        list_status = result.get('listOrderStatus', 'N/A')
        print_test("cancel_order_list", "PASS", f"OCO 취소됨: {list_status}")
        test_results["passed"].append("cancel_order_list")
    except Exception as e:
        print_test("cancel_order_list", "FAIL", str(e))
        test_results["failed"].append(("cancel_order_list", str(e)))


async def phase9_additional_market_data(throttler: BinanceSpotThrottler):
    """Phase 9: Additional Market Data"""
    print_phase(9, "Additional Market Data - 추가 시장 데이터")

    # 9.1 get_historical_trades
    try:
        result = await throttler.get_historical_trades(symbol=SYMBOL, limit=10)
        print_test("get_historical_trades", "PASS", f"{len(result)}개 과거 거래")
        test_results["passed"].append("get_historical_trades")
    except Exception as e:
        error_msg = str(e)
        if "-2014" in error_msg or "permission" in error_msg.lower():
            print_test("get_historical_trades", "SKIP", "권한 필요 (예상됨)")
            test_results["skipped"].append("get_historical_trades")
        else:
            print_test("get_historical_trades", "FAIL", error_msg)
            test_results["failed"].append(("get_historical_trades", error_msg))

    # 9.2 get_aggregate_trades
    try:
        result = await throttler.get_aggregate_trades(symbol=SYMBOL, limit=10)
        print_test("get_aggregate_trades", "PASS", f"{len(result)}개 압축 거래")
        test_results["passed"].append("get_aggregate_trades")
    except Exception as e:
        print_test("get_aggregate_trades", "FAIL", str(e))
        test_results["failed"].append(("get_aggregate_trades", str(e)))

    # 9.3 get_ui_klines
    try:
        result = await throttler.get_ui_klines(
            symbol=SYMBOL,
            interval="1h",
            limit=5
        )
        print_test("get_ui_klines", "PASS", f"{len(result)}개 UI 캔들")
        test_results["passed"].append("get_ui_klines")
    except Exception as e:
        print_test("get_ui_klines", "FAIL", str(e))
        test_results["failed"].append(("get_ui_klines", str(e)))

    # 9.4 get_rolling_window_ticker
    try:
        result = await throttler.get_rolling_window_ticker(
            symbol=SYMBOL,
            window_size="1h"
        )
        price_change = result.get('priceChange', 'N/A')
        print_test("get_rolling_window_ticker", "PASS", f"1h 변동: {price_change}")
        test_results["passed"].append("get_rolling_window_ticker")
    except Exception as e:
        print_test("get_rolling_window_ticker", "FAIL", str(e))
        test_results["failed"].append(("get_rolling_window_ticker", str(e)))


async def phase10_order_management_advanced(throttler: BinanceSpotThrottler):
    """Phase 10: Order Management Advanced"""
    global created_limit_order_id
    print_phase(10, "Order Management Advanced - 고급 주문 관리")

    # 10.1 get_rate_limit_order
    try:
        result = await throttler.get_rate_limit_order()
        print_test("get_rate_limit_order", "PASS", f"{len(result)}개 레이트 리밋 정보")
        for limit_info in result[:3]:  # 처음 3개만 출력
            interval = limit_info.get('rateLimitType', 'N/A')
            count = limit_info.get('count', 'N/A')
            print(f"      → {interval}: {count}")
        test_results["passed"].append("get_rate_limit_order")
    except Exception as e:
        print_test("get_rate_limit_order", "FAIL", str(e))
        test_results["failed"].append(("get_rate_limit_order", str(e)))

    # 10.2 cancel_replace_order (복잡한 테스트)
    try:
        # 먼저 LIMIT 주문 생성
        ticker = await throttler.get_ticker_price(symbol=SYMBOL)
        current_price = float(ticker['price'])
        original_price = round(current_price * 1.5, 4)

        order = await throttler.create_order(
            symbol=SYMBOL,
            side="SELL",
            type="LIMIT",
            timeInForce="GTC",
            quantity=5.0,
            price=original_price
        )
        created_limit_order_id = order['orderId']

        # 주문 변경 (가격 상향)
        await asyncio.sleep(0.5)
        new_price = round(current_price * 1.6, 4)

        result = await throttler.cancel_replace_order(
            symbol=SYMBOL,
            cancel_replace_mode="STOP_ON_FAILURE",
            side="SELL",
            type="LIMIT",
            timeInForce="GTC",
            cancelOrderId=created_limit_order_id,
            quantity=5.0,
            price=new_price
        )

        cancel_result = result.get('cancelResult', 'N/A')
        new_order_id = result.get('newOrderResponse', {}).get('orderId', 'N/A')

        print_test("cancel_replace_order", "PASS", f"기존 취소: {cancel_result}, 신규 ID: {new_order_id}")
        test_results["passed"].append("cancel_replace_order")

        # 새 주문 취소
        if new_order_id != 'N/A':
            await asyncio.sleep(0.5)
            await throttler.cancel_order(symbol=SYMBOL, order_id=new_order_id)

    except Exception as e:
        print_test("cancel_replace_order", "FAIL", str(e))
        test_results["failed"].append(("cancel_replace_order", str(e)))

        # 실패 시 생성된 주문이 있으면 취소 시도
        if created_limit_order_id:
            try:
                await throttler.cancel_order(symbol=SYMBOL, order_id=created_limit_order_id)
            except:
                pass

    # 10.3 get_my_prevented_matches
    try:
        result = await throttler.get_my_prevented_matches(symbol=SYMBOL, limit=10)
        print_test("get_my_prevented_matches", "PASS", f"{len(result)}개 방지된 매칭")
        test_results["passed"].append("get_my_prevented_matches")
    except Exception as e:
        print_test("get_my_prevented_matches", "FAIL", str(e))
        test_results["failed"].append(("get_my_prevented_matches", str(e)))

    # 10.4 get_my_allocations
    try:
        result = await throttler.get_my_allocations(symbol=SYMBOL, limit=10)
        print_test("get_my_allocations", "PASS", f"{len(result)}개 SOR 할당")
        test_results["passed"].append("get_my_allocations")
    except Exception as e:
        print_test("get_my_allocations", "FAIL", str(e))
        test_results["failed"].append(("get_my_allocations", str(e)))


async def main():
    """메인 테스트 실행"""
    print("=" * 80)
    print("throttled-api Remaining Methods Test (Phase 8-10)")
    print("=" * 80)
    print(f"테스트 심볼: {SYMBOL}")
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
    await phase8_oco_order(throttler)
    await phase9_additional_market_data(throttler)
    await phase10_order_management_advanced(throttler)

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
            print(f"  - {test_name}: {error[:100]}")

    if test_results['skipped']:
        print("\n[건너뛴 테스트]")
        for test_name in test_results['skipped']:
            print(f"  - {test_name}")

    print("\n" + "=" * 80)
    total = len(test_results['passed']) + len(test_results['failed']) + len(test_results['skipped'])
    success_rate = len(test_results['passed']) * 100 // total if total > 0 else 0
    print(f"성공률: {success_rate}% ({len(test_results['passed'])}/{total})")
    print("=" * 80)

    print("\n" + "=" * 80)
    print("전체 테스트 커버리지")
    print("=" * 80)
    print(f"이전 테스트: 24개")
    print(f"이번 테스트: {len(test_results['passed'])}개")
    print(f"총 테스트 완료: {24 + len(test_results['passed'])}/40")
    print(f"전체 커버리지: {(24 + len(test_results['passed'])) * 100 // 40}%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
