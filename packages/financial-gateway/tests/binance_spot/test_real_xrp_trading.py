"""
XRP 실제 거래 테스트
실제 Binance API를 사용하여 XRP 매수/매도 테스트
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from financial_gateway.binance_spot.API.BinanceSpotGateway.BinanceSpotGateway import BinanceSpotGateway
from financial_gateway.request import (
    CurrentBalanceRequest,
    TickerRequest,
    MarketSellOrderRequest,
    MarketBuyOrderRequest,
)
from financial_assets.stock_address import StockAddress


def print_separator():
    """구분선 출력"""
    print("=" * 80)


async def main():
    """XRP 실제 거래 테스트 메인 함수"""
    # .env 파일 로드
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)

    # API 키 확인
    if not os.getenv("BINANCE_SPOT_API_KEY"):
        print("[ERROR] BINANCE_SPOT_API_KEY 환경변수 필요")
        return

    print_separator()
    print("XRP 실제 거래 테스트 시작")
    print_separator()

    # XRP/USDT 주소
    xrp_usdt = StockAddress(
        archetype="candle",
        exchange="binance",
        tradetype="spot",
        base="XRP",
        quote="USDT",
        timeframe="1m",
    )

    # Gateway 초기화
    gateway = BinanceSpotGateway()

    # 1. 초기 잔고 확인
    print("\n[1] 초기 잔고 확인")
    balance_req = CurrentBalanceRequest()
    balance_resp = await gateway.request_current_balance(balance_req)

    if not balance_resp.is_success:
        print(f"[ERROR] 잔고 조회 실패: {balance_resp.error_message}")
        return

    xrp_balance = balance_resp.result.get("XRP")
    usdt_balance = balance_resp.result.get("USDT")

    print(f"  XRP: {xrp_balance.amount if xrp_balance else 0:.4f}")
    print(f"  USDT: {usdt_balance.amount if usdt_balance else 0:.4f}")

    if not xrp_balance or xrp_balance.amount < 5:
        print("[ERROR] XRP 잔고가 5개 미만입니다")
        return

    # 2. XRP 현재 시세 확인
    print("\n[2] XRP/USDT 시세 확인")
    ticker_req = TickerRequest(address=xrp_usdt)
    ticker_resp = await gateway.request_ticker(ticker_req)

    if not ticker_resp.is_success:
        print(f"[ERROR] 시세 조회 실패: {ticker_resp.error_message}")
        return

    ticker_data = ticker_resp.result["XRPUSDT"]
    current_price = ticker_data["current"]
    print(f"  현재가: {current_price:.4f} USDT")
    print(f"  고가: {ticker_data['high']:.4f} USDT")
    print(f"  저가: {ticker_data['low']:.4f} USDT")

    # 3. XRP 5개 시장가 매도
    print("\n[3] XRP 5개 시장가 매도")
    sell_amount = 5.0
    sell_req = MarketSellOrderRequest(
        address=xrp_usdt,
        volume=sell_amount,
    )

    sell_resp = await gateway.request_market_sell_order(sell_req)

    if not sell_resp.is_success:
        print(f"[ERROR] 매도 실패: {sell_resp.error_message}")
        if sell_resp.is_insufficient_balance:
            print("  원인: 잔고 부족")
        elif sell_resp.is_min_notional_error:
            print("  원인: 최소 주문 금액 미달")
        return

    print(f"  매도 성공!")
    print(f"  주문 ID: {sell_resp.order.order_id}")
    print(f"  체결 수량: {sell_resp.order.filled_amount:.4f} XRP")
    print(f"  상태: {sell_resp.order.status}")

    # 4. 매도 후 잔고 확인
    print("\n[4] 매도 후 잔고 확인")
    await asyncio.sleep(1)  # API 호출 간격
    balance_resp = await gateway.request_current_balance(balance_req)

    xrp_balance_after_sell = balance_resp.result.get("XRP")
    usdt_balance_after_sell = balance_resp.result.get("USDT")

    print(f"  XRP: {xrp_balance_after_sell.amount if xrp_balance_after_sell else 0:.4f}")
    print(f"  USDT: {usdt_balance_after_sell.amount if usdt_balance_after_sell else 0:.4f}")

    usdt_gained = (usdt_balance_after_sell.amount if usdt_balance_after_sell else 0) - \
                  (usdt_balance.amount if usdt_balance else 0)
    print(f"  획득 USDT: {usdt_gained:.4f}")

    # 5. XRP 다시 시장가 매수
    print("\n[5] XRP 다시 시장가 매수")
    buy_amount = sell_amount  # 같은 수량 매수
    buy_req = MarketBuyOrderRequest(
        address=xrp_usdt,
        volume=buy_amount,
    )

    buy_resp = await gateway.request_market_buy_order(buy_req)

    if not buy_resp.is_success:
        print(f"[ERROR] 매수 실패: {buy_resp.error_message}")
        if buy_resp.is_insufficient_balance:
            print("  원인: USDT 잔고 부족")
        elif buy_resp.is_min_notional_error:
            print("  원인: 최소 주문 금액 미달")
        return

    print(f"  매수 성공!")
    print(f"  주문 ID: {buy_resp.order.order_id}")
    print(f"  체결 수량: {buy_resp.order.filled_amount:.4f} XRP")
    print(f"  상태: {buy_resp.order.status}")

    # 6. 최종 잔고 확인
    print("\n[6] 최종 잔고 확인")
    await asyncio.sleep(1)  # API 호출 간격
    balance_resp = await gateway.request_current_balance(balance_req)

    xrp_balance_final = balance_resp.result.get("XRP")
    usdt_balance_final = balance_resp.result.get("USDT")

    print(f"  XRP: {xrp_balance_final.amount if xrp_balance_final else 0:.4f}")
    print(f"  USDT: {usdt_balance_final.amount if usdt_balance_final else 0:.4f}")

    xrp_diff = (xrp_balance_final.amount if xrp_balance_final else 0) - \
               (xrp_balance.amount if xrp_balance else 0)
    usdt_diff = (usdt_balance_final.amount if usdt_balance_final else 0) - \
                (usdt_balance.amount if usdt_balance else 0)

    print(f"\n  XRP 변화: {xrp_diff:+.4f}")
    print(f"  USDT 변화: {usdt_diff:+.4f} (수수료 및 슬리피지)")

    print_separator()
    print("XRP 실제 거래 테스트 완료")
    print_separator()


if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(main(), timeout=10.0))
    except asyncio.TimeoutError:
        print("\n[ERROR] 테스트 타임아웃 (10초)")
        print("로그를 확인하여 원인을 분석하세요")
