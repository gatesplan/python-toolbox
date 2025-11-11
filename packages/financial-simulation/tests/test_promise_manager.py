"""Tests for PromiseManager"""

import pytest
from financial_simulation.exchange.Core.Portfolio.PromiseManager import PromiseManager


class TestPromiseManager:
    """PromiseManager 테스트"""

    def test_lock_creates_promise(self):
        """Promise 생성 테스트"""
        pm = PromiseManager()
        pm.lock("order_1", "USDT", 1000.0)

        promise = pm.get_promise("order_1")
        assert promise is not None
        assert promise["symbol"] == "USDT"
        assert promise["amount"] == 1000.0

    def test_lock_duplicate_raises_error(self):
        """중복 promise_id 생성 시 에러"""
        pm = PromiseManager()
        pm.lock("order_1", "USDT", 1000.0)

        with pytest.raises(ValueError, match="already exists"):
            pm.lock("order_1", "BTC", 500.0)

    def test_unlock_removes_promise(self):
        """Promise 삭제 테스트"""
        pm = PromiseManager()
        pm.lock("order_1", "USDT", 1000.0)
        pm.unlock("order_1")

        promise = pm.get_promise("order_1")
        assert promise is None

    def test_unlock_nonexistent_raises_error(self):
        """존재하지 않는 promise unlock 시 에러"""
        pm = PromiseManager()

        with pytest.raises(KeyError, match="not found"):
            pm.unlock("order_999")

    def test_get_locked_amount_single_promise(self):
        """단일 promise 수량 집계"""
        pm = PromiseManager()
        pm.lock("order_1", "USDT", 1000.0)

        locked = pm.get_locked_amount("USDT")
        assert locked == 1000.0

    def test_get_locked_amount_multiple_promises(self):
        """여러 promise 수량 집계"""
        pm = PromiseManager()
        pm.lock("order_1", "USDT", 1000.0)
        pm.lock("order_2", "USDT", 500.0)
        pm.lock("order_3", "USDT", 300.0)

        locked = pm.get_locked_amount("USDT")
        assert locked == 1800.0

    def test_get_locked_amount_multiple_symbols(self):
        """여러 화폐 독립적으로 집계"""
        pm = PromiseManager()
        pm.lock("order_1", "USDT", 1000.0)
        pm.lock("order_2", "BTC", 0.5)
        pm.lock("order_3", "USDT", 500.0)

        assert pm.get_locked_amount("USDT") == 1500.0
        assert pm.get_locked_amount("BTC") == 0.5

    def test_get_locked_amount_no_promises(self):
        """Promise 없을 때 0 반환"""
        pm = PromiseManager()

        locked = pm.get_locked_amount("USDT")
        assert locked == 0.0

    def test_get_locked_amount_after_unlock(self):
        """Unlock 후 수량 재계산"""
        pm = PromiseManager()
        pm.lock("order_1", "USDT", 1000.0)
        pm.lock("order_2", "USDT", 500.0)

        pm.unlock("order_1")

        locked = pm.get_locked_amount("USDT")
        assert locked == 500.0

    def test_get_promise_nonexistent(self):
        """존재하지 않는 promise 조회 시 None"""
        pm = PromiseManager()

        promise = pm.get_promise("order_999")
        assert promise is None

    def test_get_all_promises(self):
        """모든 promise 조회"""
        pm = PromiseManager()
        pm.lock("order_1", "USDT", 1000.0)
        pm.lock("order_2", "BTC", 0.5)

        all_promises = pm.get_all_promises()
        assert len(all_promises) == 2
        assert "order_1" in all_promises
        assert "order_2" in all_promises
        assert all_promises["order_1"]["symbol"] == "USDT"
        assert all_promises["order_2"]["symbol"] == "BTC"

    def test_get_all_promises_empty(self):
        """Promise 없을 때 빈 dict 반환"""
        pm = PromiseManager()

        all_promises = pm.get_all_promises()
        assert all_promises == {}
