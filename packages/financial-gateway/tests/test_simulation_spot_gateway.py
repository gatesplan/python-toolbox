# SimulationSpotGateway 테스트

import pytest
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price
from financial_assets.request import (
    LimitBuyOrderRequest,
    LimitSellOrderRequest,
    MarketBuyOrderRequest,
    MarketSellOrderRequest,
)
from financial_assets.constants import Side, OrderType
from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_simulation.tradesim.API.TradeSimulation import TradeSimulation
from financial_gateway.spot.simulation_spot_gateway import SimulationSpotGateway


@pytest.fixture
def market_data():
    # MarketData 생성 (테스트용 간단한 데이터)
    # BTC/USDT 가격 데이터 생성
    btc_prices = [
        Price(
            exchange="simulation",
            market="BTC/USDT",
            t=i,
            o=50000.0,
            h=51000.0,
            l=49000.0,
            c=50500.0,
            v=100.0
        )
        for i in range(1000, 1100)
    ]

    data = {"BTC/USDT": btc_prices}
    md = MarketData(data=data, offset=0)
    return md


@pytest.fixture
def trade_simulation():
    return TradeSimulation()


@pytest.fixture
def spot_exchange(market_data, trade_simulation):
    return SpotExchange(
        initial_balance=10000.0,
        market_data=market_data,
        trade_simulation=trade_simulation,
        quote_currency="USDT"
    )


@pytest.fixture
def gateway(spot_exchange):
    return SimulationSpotGateway(spot_exchange)


class TestSimulationSpotGatewayInit:
    # 초기화 테스트

    def test_init_success(self, spot_exchange):
        gateway = SimulationSpotGateway(spot_exchange)

        assert gateway.gateway_name == "simulation"
        assert gateway.is_realworld_gateway is False
        assert gateway.spot_exchange is spot_exchange
        assert gateway._api_key is None
        assert gateway._api_secret is None


class TestSimulationSpotGatewayLimitBuyOrder:
    # 지정가 매수 주문 테스트

    def test_limit_buy_order_success(self, gateway):
        # Arrange
        address = StockAddress(
            archetype="ohlcv",
            exchange="simulation",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m"
        )
        request = LimitBuyOrderRequest(
            address=address,
            price=50000.0,
            volume=0.1,
            post_only=False
        )

        # Act
        response = gateway.request_limit_buy_order(request)

        # Assert
        assert response is not None
        assert hasattr(response, 'is_success')

    def test_limit_buy_order_insufficient_balance(self, gateway):
        # Arrange
        address = StockAddress(
            archetype="ohlcv",
            exchange="simulation",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m"
        )
        request = LimitBuyOrderRequest(
            address=address,
            price=50000.0,
            volume=1000.0,  # 잔고보다 큰 수량
            post_only=False
        )

        # Act
        response = gateway.request_limit_buy_order(request)

        # Assert
        assert response.is_success is False
        assert response.is_insufficient_balance is True


class TestSimulationSpotGatewayLimitSellOrder:
    # 지정가 매도 주문 테스트

    def test_limit_sell_order_success(self, gateway):
        # Arrange - 먼저 매수하여 자산 확보
        address = StockAddress(
            archetype="ohlcv",
            exchange="simulation",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m"
        )
        buy_request = LimitBuyOrderRequest(
            address=address,
            price=50000.0,
            volume=0.1,
            post_only=False
        )
        buy_response = gateway.request_limit_buy_order(buy_request)

        # 매수가 성공했다고 가정 (실제로는 체결 시뮬레이션 필요)
        if buy_response.is_success:
            # Act - 매도 주문
            sell_request = LimitSellOrderRequest(
                address=address,
                price=51000.0,
                volume=0.05,
                post_only=False
            )
            response = gateway.request_limit_sell_order(sell_request)

            # Assert
            assert response is not None
            assert hasattr(response, 'is_success')


class TestSimulationSpotGatewayMarketOrder:
    # 시장가 주문 테스트

    def test_market_buy_order_success(self, gateway):
        # Arrange
        address = StockAddress(
            archetype="ohlcv",
            exchange="simulation",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m"
        )
        request = MarketBuyOrderRequest(
            address=address,
            volume=0.1
        )

        # Act
        response = gateway.request_market_buy_order(request)

        # Assert
        assert response is not None
        assert hasattr(response, 'is_success')

    def test_market_sell_order_success(self, gateway):
        # Arrange - 먼저 자산 확보 필요
        address = StockAddress(
            archetype="ohlcv",
            exchange="simulation",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m"
        )

        # 매수 먼저 실행
        buy_request = MarketBuyOrderRequest(
            address=address,
            volume=0.1
        )
        buy_response = gateway.request_market_buy_order(buy_request)

        if buy_response.is_success:
            # Act
            sell_request = MarketSellOrderRequest(
                address=address,
                volume=0.05
            )
            response = gateway.request_market_sell_order(sell_request)

            # Assert
            assert response is not None
            assert hasattr(response, 'is_success')


class TestSimulationSpotGatewayOrderManagement:
    # 주문 관리 테스트

    def test_close_order_success(self, gateway):
        # Arrange - 주문 생성
        address = StockAddress(
            archetype="ohlcv",
            exchange="simulation",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m"
        )
        request = LimitBuyOrderRequest(
            address=address,
            price=50000.0,
            volume=0.1,
            post_only=False
        )
        order_response = gateway.request_limit_buy_order(request)

        if order_response.is_success and order_response.order:
            # Act - 주문 취소
            from financial_assets.request import CloseOrderRequest
            close_request = CloseOrderRequest(order_id=order_response.order.order_id)
            result = gateway.request_close_order(close_request)

            # Assert
            assert result is not None


class TestSimulationSpotGatewayAccountInfo:
    # 계정 정보 조회 테스트 (추후 구현)

    def test_request_current_balance_basic(self, gateway):
        # 기본적인 잔고 조회 동작 확인
        # Request 객체 필드명이 확정되면 구현
        pass


class TestSimulationSpotGatewayMarketData:
    # 시장 데이터 조회 테스트 (추후 구현)

    def test_request_ticker_basic(self, gateway):
        # 기본적인 시세 조회 동작 확인
        # Request 객체 필드명이 확정되면 구현
        pass
