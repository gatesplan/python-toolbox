"""Comprehensive integration test for SpotExchange"""

import pytest
import numpy as np
from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_simulation.tradesim.API.TradeSimulation import TradeSimulation
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType, TimeInForce
from financial_assets.price import Price


def generate_price_data(base_price: float, volatility: float, num_ticks: int, seed: int = 42) -> list[Price]:
    """사인파 + 난수 기반 가격 데이터 생성

    Args:
        base_price: 기준 가격
        volatility: 변동성 (비율)
        num_ticks: 생성할 틱 개수
        seed: 난수 시드

    Returns:
        list[Price]: 생성된 Price 리스트
    """
    np.random.seed(seed)

    prices = []
    for i in range(num_ticks):
        # 사인파 트렌드 (천천히 변화)
        trend = np.sin(i / 100) * base_price * volatility

        # 난수 노이즈
        noise = np.random.randn() * base_price * (volatility / 10)

        # 최종 종가
        close = base_price + trend + noise

        # OHLCV 생성 (close 기준으로 약간의 변동)
        daily_range = close * 0.02  # 일일 변동폭 2%
        high = close + abs(np.random.randn()) * daily_range
        low = close - abs(np.random.randn()) * daily_range
        open_price = close + np.random.randn() * daily_range * 0.5

        # 볼륨 (기준 볼륨 + 랜덤)
        base_volume = base_price * 10  # 기준 볼륨
        volume = base_volume * (0.8 + np.random.rand() * 0.4)  # 80%~120%

        prices.append(Price(
            exchange="binance",
            market=f"TEST{i}",
            t=1000 + i * 60,  # 1분 간격
            o=open_price,
            h=high,
            l=low,
            c=close,
            v=volume
        ))

    return prices


@pytest.fixture
def comprehensive_market_data():
    """3개 종목, 1000틱의 시장 데이터 생성"""
    # BTC/USDT: 40,000~60,000 범위
    btc_prices = generate_price_data(
        base_price=50000.0,
        volatility=0.2,  # 20% 변동성
        num_ticks=1000,
        seed=42
    )

    # ETH/USDT: 2,000~4,000 범위
    eth_prices = generate_price_data(
        base_price=3000.0,
        volatility=0.25,  # 25% 변동성
        num_ticks=1000,
        seed=43
    )

    # SOL/USDT: 100~200 범위
    sol_prices = generate_price_data(
        base_price=150.0,
        volatility=0.3,  # 30% 변동성
        num_ticks=1000,
        seed=44
    )

    data = {
        "BTC/USDT": btc_prices,
        "ETH/USDT": eth_prices,
        "SOL/USDT": sol_prices,
    }

    return MarketData(data=data, availability_threshold=0.8, offset=0)


@pytest.fixture
def comprehensive_exchange(comprehensive_market_data):
    """종합 테스트용 거래소 생성"""
    trade_simulation = TradeSimulation()
    return SpotExchange(
        initial_balance=100000.0,
        market_data=comprehensive_market_data,
        trade_simulation=trade_simulation,
        quote_currency="USDT"
    )


class TestSpotExchangeComprehensive:
    """SpotExchange 종합 통합 테스트"""

    def test_comprehensive_trading_simulation(self, comprehensive_exchange):
        """여러 타임스텝에 걸친 종합 트레이딩 시뮬레이션"""
        exchange = comprehensive_exchange

        # 초기 상태 확인
        initial_balance = exchange.get_balance("USDT")
        assert initial_balance == 100000.0

        # 트레이딩 이력 추적
        portfolio_history = []

        # ===== Step 1: 초기 BTC 매수 (틱 0) =====
        btc_price_initial = exchange.get_current_price("BTC/USDT")
        btc_buy_order_1 = SpotOrder(
            order_id="btc_buy_1",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=btc_price_initial,
            amount=0.5,  # 0.5 BTC 매수
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )

        trades_1 = exchange.place_order(btc_buy_order_1)
        assert len(trades_1) > 0, "BTC 매수 체결 실패"

        # 잔고 확인
        usdt_after_btc_buy = exchange.get_balance("USDT")
        assert usdt_after_btc_buy < initial_balance, "USDT 잔고가 감소해야 함"

        # 포지션 확인
        positions = exchange.get_positions()
        assert len(positions) > 0, "BTC 포지션이 생성되어야 함"

        portfolio_history.append({
            "step": 0,
            "action": "BTC BUY 0.5",
            "usdt_balance": usdt_after_btc_buy,
            "total_value": exchange.get_total_value(),
            "positions": positions.copy()
        })

        # ===== Step 2: 100 틱 진행 =====
        for _ in range(100):
            exchange.step()

        # ===== Step 3: ETH 매수 (틱 100) =====
        eth_price = exchange.get_current_price("ETH/USDT")
        eth_buy_order = SpotOrder(
            order_id="eth_buy_1",
            stock_address=StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=eth_price,
            amount=5.0,  # 5 ETH 매수
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )

        trades_2 = exchange.place_order(eth_buy_order)
        assert len(trades_2) > 0, "ETH 매수 체결 실패"

        positions_after_eth = exchange.get_positions()
        assert len(positions_after_eth) >= 2, "BTC와 ETH 포지션이 있어야 함"

        portfolio_history.append({
            "step": 100,
            "action": "ETH BUY 5.0",
            "usdt_balance": exchange.get_balance("USDT"),
            "total_value": exchange.get_total_value(),
            "positions": positions_after_eth.copy()
        })

        # ===== Step 4: 100 틱 더 진행 =====
        for _ in range(100):
            exchange.step()

        # ===== Step 5: SOL 매수 (틱 200) =====
        sol_price = exchange.get_current_price("SOL/USDT")
        sol_buy_order = SpotOrder(
            order_id="sol_buy_1",
            stock_address=StockAddress("candle", "binance", "spot", "SOL", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=sol_price,
            amount=50.0,  # 50 SOL 매수
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )

        trades_3 = exchange.place_order(sol_buy_order)
        assert len(trades_3) > 0, "SOL 매수 체결 실패"

        positions_after_sol = exchange.get_positions()
        assert len(positions_after_sol) >= 3, "BTC, ETH, SOL 포지션이 있어야 함"

        portfolio_history.append({
            "step": 200,
            "action": "SOL BUY 50.0",
            "usdt_balance": exchange.get_balance("USDT"),
            "total_value": exchange.get_total_value(),
            "positions": positions_after_sol.copy()
        })

        # ===== Step 6: 150 틱 더 진행 =====
        for _ in range(150):
            exchange.step()

        # ===== Step 7: BTC 일부 매도 (틱 350) =====
        btc_price_sell = exchange.get_current_price("BTC/USDT")

        # 보유 BTC 확인
        btc_positions = {k: v for k, v in exchange.get_positions().items() if "BTC" in k}
        if btc_positions:
            btc_ticker = list(btc_positions.keys())[0]
            btc_amount = btc_positions[btc_ticker]

            # BTC 절반 매도
            btc_sell_order = SpotOrder(
                order_id="btc_sell_1",
                stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=btc_price_sell,
                amount=btc_amount * 0.5,
                timestamp=exchange.get_current_timestamp(),
                time_in_force=TimeInForce.IOC
            )

            trades_4 = exchange.place_order(btc_sell_order)
            assert len(trades_4) > 0, "BTC 매도 체결 실패"

            # USDT 잔고 증가 확인
            usdt_after_sell = exchange.get_balance("USDT")

            portfolio_history.append({
                "step": 350,
                "action": f"BTC SELL {btc_amount * 0.5}",
                "usdt_balance": usdt_after_sell,
                "total_value": exchange.get_total_value(),
                "positions": exchange.get_positions().copy()
            })

        # ===== Step 8: 200 틱 더 진행 =====
        for _ in range(200):
            exchange.step()

        # ===== Step 9: ETH 전량 매도 (틱 550) =====
        eth_price_sell = exchange.get_current_price("ETH/USDT")

        eth_positions = {k: v for k, v in exchange.get_positions().items() if "ETH" in k}
        if eth_positions:
            eth_ticker = list(eth_positions.keys())[0]
            eth_amount = eth_positions[eth_ticker]

            eth_sell_order = SpotOrder(
                order_id="eth_sell_1",
                stock_address=StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m"),
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=eth_price_sell,
                amount=eth_amount,
                timestamp=exchange.get_current_timestamp(),
                time_in_force=TimeInForce.IOC
            )

            trades_5 = exchange.place_order(eth_sell_order)
            assert len(trades_5) > 0, "ETH 매도 체결 실패"

            portfolio_history.append({
                "step": 550,
                "action": f"ETH SELL {eth_amount}",
                "usdt_balance": exchange.get_balance("USDT"),
                "total_value": exchange.get_total_value(),
                "positions": exchange.get_positions().copy()
            })

        # ===== Step 10: 100 틱 더 진행 =====
        for _ in range(100):
            exchange.step()

        # ===== 최종 상태 검증 =====
        final_balance = exchange.get_balance("USDT")
        final_positions = exchange.get_positions()
        final_total_value = exchange.get_total_value()
        final_stats = exchange.get_statistics()

        portfolio_history.append({
            "step": 650,
            "action": "FINAL",
            "usdt_balance": final_balance,
            "total_value": final_total_value,
            "positions": final_positions.copy()
        })

        # 검증 1: 총 자산 가치가 양수
        assert final_total_value > 0, "총 자산 가치가 양수여야 함"

        # 검증 2: 거래 내역이 존재
        trade_history = exchange.get_trade_history()
        assert len(trade_history) >= 5, "최소 5개 이상의 거래가 있어야 함"

        # 검증 3: 통계 정보 확인
        assert "total_value" in final_stats
        assert "total_pnl" in final_stats
        assert "total_pnl_ratio" in final_stats

        # 검증 4: 포트폴리오 이력 출력 (디버깅용)
        print("\n===== 포트폴리오 이력 =====")
        for entry in portfolio_history:
            print(f"Step {entry['step']:3d} | {entry['action']:20s} | "
                  f"USDT: {entry['usdt_balance']:12.2f} | "
                  f"Total: {entry['total_value']:12.2f} | "
                  f"Positions: {len(entry['positions'])}")

        print(f"\n초기 자산: {initial_balance:,.2f} USDT")
        print(f"최종 자산: {final_total_value:,.2f} USDT")
        print(f"총 손익: {final_stats['total_pnl']:,.2f} USDT ({final_stats['total_pnl_ratio']:.2f}%)")
        print(f"총 거래 수: {len(trade_history)}")

        # 검증 5: 자산 변화가 있었는지 확인
        assert len(portfolio_history) >= 5, "충분한 포트폴리오 변화가 있어야 함"

        # 검증 6: 다양한 포지션 보유 이력
        max_positions = max(len(entry['positions']) for entry in portfolio_history)
        assert max_positions >= 2, "최소 2개 이상의 포지션을 동시 보유했어야 함"

    def test_multiple_symbols_concurrent_trading(self, comprehensive_exchange):
        """여러 종목 동시 거래 테스트"""
        exchange = comprehensive_exchange

        # 각 종목의 현재 가격 조회
        btc_price = exchange.get_current_price("BTC/USDT")
        eth_price = exchange.get_current_price("ETH/USDT")
        sol_price = exchange.get_current_price("SOL/USDT")

        assert btc_price is not None
        assert eth_price is not None
        assert sol_price is not None

        # 3개 종목 동시 매수
        orders = [
            SpotOrder(
                order_id=f"concurrent_buy_{symbol}",
                stock_address=StockAddress("candle", "binance", "spot", symbol.split("/")[0], "USDT", "1m"),
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=price,
                amount=amount,
                timestamp=exchange.get_current_timestamp(),
                time_in_force=TimeInForce.IOC
            )
            for symbol, price, amount in [
                ("BTC/USDT", btc_price, 0.1),
                ("ETH/USDT", eth_price, 1.0),
                ("SOL/USDT", sol_price, 10.0),
            ]
        ]

        # 모든 주문 실행
        all_trades = []
        for order in orders:
            trades = exchange.place_order(order)
            all_trades.extend(trades)

        # 체결 확인
        assert len(all_trades) >= 3, "최소 3개의 체결이 있어야 함"

        # 포지션 확인
        positions = exchange.get_positions()
        assert len(positions) >= 3, "3개 종목의 포지션이 있어야 함"

        # 각 종목별 포지션 가치 확인
        for ticker in positions.keys():
            position_value = exchange.get_position_value(ticker)
            assert position_value["market_value"] > 0, f"{ticker} 포지션 가치가 양수여야 함"

    def test_long_simulation_stability(self, comprehensive_exchange):
        """긴 시뮬레이션 안정성 테스트"""
        exchange = comprehensive_exchange

        # 초기 매수
        btc_price = exchange.get_current_price("BTC/USDT")
        order = SpotOrder(
            order_id="stability_buy",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=btc_price,
            amount=0.2,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        exchange.place_order(order)

        # 800 틱 진행 (시뮬레이션이 안정적으로 동작하는지 확인)
        step_count = 0
        while not exchange.is_finished() and step_count < 800:
            # 매 100 틱마다 총 자산 가치 확인
            if step_count % 100 == 0:
                total_value = exchange.get_total_value()
                assert total_value > 0, f"Step {step_count}: 총 자산 가치가 양수여야 함"

            result = exchange.step()
            if not result:
                break
            step_count += 1

        # 최종 상태 확인
        final_value = exchange.get_total_value()
        assert final_value > 0, "최종 자산 가치가 양수여야 함"
        assert step_count >= 800, "800 틱 이상 진행해야 함"

    def test_position_pnl_tracking(self, comprehensive_exchange):
        """포지션 손익 추적 테스트"""
        exchange = comprehensive_exchange

        # BTC 매수
        btc_price_buy = exchange.get_current_price("BTC/USDT")
        buy_order = SpotOrder(
            order_id="pnl_buy",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=btc_price_buy,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        exchange.place_order(buy_order)

        # 매수 직후 포지션 정보
        positions_initial = exchange.get_positions()
        assert len(positions_initial) > 0

        ticker = list(positions_initial.keys())[0]
        pnl_history = []

        # 200 틱 진행하면서 손익 추적
        for step in range(200):
            if step % 50 == 0:
                current_price = exchange.get_current_price("BTC/USDT")
                position_value = exchange.get_position_value(ticker)

                pnl_history.append({
                    "step": step,
                    "price": current_price,
                    "book_value": position_value["book_value"],
                    "market_value": position_value["market_value"],
                    "pnl": position_value["pnl"],
                    "pnl_ratio": position_value["pnl_ratio"]
                })

            exchange.step()

        # 손익 이력 출력
        print("\n===== 포지션 손익 추적 =====")
        for entry in pnl_history:
            print(f"Step {entry['step']:3d} | "
                  f"Price: {entry['price']:8.2f} | "
                  f"Book: {entry['book_value']:10.2f} | "
                  f"Market: {entry['market_value']:10.2f} | "
                  f"PnL: {entry['pnl']:+10.2f} ({entry['pnl_ratio']:+6.2f}%)")

        # 검증: 손익이 변화했어야 함
        pnl_values = [entry['pnl'] for entry in pnl_history]
        assert len(set(pnl_values)) > 1, "손익이 변화해야 함"

    def test_asset_allocation_changes(self, comprehensive_exchange):
        """자산 배분 변화 테스트"""
        exchange = comprehensive_exchange

        allocation_history = []

        # 1. 초기 상태 (100% USDT)
        stats = exchange.get_statistics()
        allocation_history.append({
            "stage": "Initial",
            "allocation": stats["allocation"].copy()
        })

        # 2. BTC 매수
        btc_price = exchange.get_current_price("BTC/USDT")
        btc_order = SpotOrder(
            order_id="alloc_btc",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=btc_price,
            amount=0.5,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        exchange.place_order(btc_order)

        stats = exchange.get_statistics()
        allocation_history.append({
            "stage": "After BTC buy",
            "allocation": stats["allocation"].copy()
        })

        # 3. 100 틱 진행 후 ETH 매수
        for _ in range(100):
            exchange.step()

        eth_price = exchange.get_current_price("ETH/USDT")
        eth_order = SpotOrder(
            order_id="alloc_eth",
            stock_address=StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=eth_price,
            amount=3.0,
            timestamp=exchange.get_current_timestamp(),
            time_in_force=TimeInForce.IOC
        )
        exchange.place_order(eth_order)

        stats = exchange.get_statistics()
        allocation_history.append({
            "stage": "After ETH buy",
            "allocation": stats["allocation"].copy()
        })

        # 자산 배분 이력 출력
        print("\n===== 자산 배분 변화 =====")
        for entry in allocation_history:
            print(f"\n{entry['stage']}:")
            for asset, ratio in entry['allocation'].items():
                print(f"  {asset:15s}: {ratio:6.2f}%")

        # 검증: 자산 배분이 변화했어야 함
        assert len(allocation_history) >= 3
        assert len(allocation_history[0]["allocation"]) <= 1  # 초기에는 USDT만
        assert len(allocation_history[-1]["allocation"]) >= 2  # 최종에는 여러 자산
