import pytest
from financial_gateway.binance_spot.Core.ResponseParser.ResponseParser import ResponseParser


class TestResponseParserOrderCreation:
    """주문 생성 응답 파싱 테스트"""

    def test_parse_successful_order_creation(self):
        """성공적인 주문 생성 응답 파싱"""
        # Binance API 주문 생성 응답 샘플
        binance_response = {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "orderListId": -1,
            "clientOrderId": "testOrderId123",
            "transactTime": 1507725176595,
            "price": "50000.00000000",
            "origQty": "0.10000000",
            "executedQty": "0.00000000",
            "cummulativeQuoteQty": "0.00000000",
            "status": "NEW",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "BUY",
        }

        # Act
        response = ResponseParser.parse_order_response(binance_response)

        # Assert
        assert response.is_success is True
        assert response.order is not None
        assert response.order.order_id == "12345"
        assert response.order.stock_address.base == "BTC"
        assert response.order.stock_address.quote == "USDT"
        assert response.error_message is None

    def test_parse_failed_order_creation_with_exception(self):
        """실패한 주문 생성 응답 파싱 (예외 포함)"""
        # Binance API 에러 응답
        error_exception = Exception("Insufficient balance")

        # Act
        response = ResponseParser.parse_order_error(error_exception)

        # Assert
        assert response.is_success is False
        assert response.order is None
        assert "Insufficient balance" in response.error_message


class TestResponseParserOrderQuery:
    """주문 조회 응답 파싱 테스트"""

    def test_parse_order_status_response(self):
        """주문 상태 조회 응답 파싱"""
        # Binance API 주문 조회 응답
        binance_response = {
            "symbol": "ETHUSDT",
            "orderId": 67890,
            "orderListId": -1,
            "clientOrderId": "testOrderId456",
            "price": "3000.00000000",
            "origQty": "1.50000000",
            "executedQty": "1.00000000",
            "cummulativeQuoteQty": "3000.00000000",
            "status": "PARTIALLY_FILLED",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "SELL",
            "stopPrice": "0.00000000",
            "icebergQty": "0.00000000",
            "time": 1507725176595,
            "updateTime": 1507725176595,
            "isWorking": True,
        }

        # Act
        response = ResponseParser.parse_order_status_response(binance_response)

        # Assert
        assert response.is_success is True
        assert response.current_order is not None
        assert response.current_order.order_id == "67890"
        assert response.current_order.filled_amount == 1.0


class TestResponseParserBalance:
    """잔고 조회 응답 파싱 테스트"""

    def test_parse_account_info_response(self):
        """계정 정보 (잔고) 응답 파싱"""
        # Binance API account 응답
        binance_response = {
            "makerCommission": 15,
            "takerCommission": 15,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": 123456789,
            "accountType": "SPOT",
            "balances": [
                {"asset": "BTC", "free": "0.50000000", "locked": "0.10000000"},
                {"asset": "USDT", "free": "10000.00000000", "locked": "500.00000000"},
                {"asset": "ETH", "free": "2.00000000", "locked": "0.00000000"},
            ],
        }

        # Act
        response = ResponseParser.parse_balance_response(binance_response)

        # Assert
        assert response.is_success is True
        assert response.result is not None
        assert len(response.result) == 3
        # BTC 잔고 확인
        btc_token = response.result["BTC"]
        assert btc_token.symbol == "BTC"
        assert btc_token.amount == 0.6  # free + locked = 0.5 + 0.1


class TestResponseParserMarketData:
    """시장 데이터 응답 파싱 테스트"""

    def test_parse_ticker_response(self):
        """Ticker 응답 파싱"""
        # Binance API ticker 응답
        binance_response = {
            "symbol": "BTCUSDT",
            "priceChange": "1000.00000000",
            "priceChangePercent": "2.00",
            "weightedAvgPrice": "50500.00000000",
            "prevClosePrice": "50000.00000000",
            "lastPrice": "51000.00000000",
            "lastQty": "0.10000000",
            "bidPrice": "50999.00000000",
            "askPrice": "51001.00000000",
            "openPrice": "50000.00000000",
            "highPrice": "52000.00000000",
            "lowPrice": "49000.00000000",
            "volume": "1000.00000000",
            "quoteVolume": "50500000.00000000",
            "openTime": 1499040000000,
            "closeTime": 1499644799999,
            "firstId": 1,
            "lastId": 10000,
            "count": 10000,
        }

        # Act
        response = ResponseParser.parse_ticker_response(binance_response)

        # Assert
        assert response.is_success is True
        assert response.result is not None
        assert "BTCUSDT" in response.result
        ticker_data = response.result["BTCUSDT"]
        assert ticker_data["current"] == 51000.0

    def test_parse_orderbook_response(self):
        """Orderbook 응답 파싱"""
        # Binance API depth 응답
        binance_response = {
            "lastUpdateId": 1027024,
            "bids": [
                ["50000.00000000", "1.00000000"],
                ["49999.00000000", "2.00000000"],
            ],
            "asks": [
                ["50001.00000000", "1.50000000"],
                ["50002.00000000", "3.00000000"],
            ],
        }

        # Act
        response = ResponseParser.parse_orderbook_response(binance_response)

        # Assert
        assert response.is_success is True
        assert response.bids is not None
        assert response.asks is not None
        assert len(response.bids) == 2
        assert len(response.asks) == 2
        assert response.bids[0] == (50000.0, 1.0)
