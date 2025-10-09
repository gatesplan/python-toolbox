import unittest
from financial_assets.stock_address import StockAddress
from financial_assets.order import Order, OrderStatus, FilledOrder, OrderList


class TestOrder(unittest.TestCase):
    """Order 클래스 테스트"""

    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        self.stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m",
        )

    def test_order_creation(self):
        """Order 생성 테스트"""
        order = Order(
            stock_address=self.stock_address,
            order_id="order_123",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        self.assertEqual(order.order_id, "order_123")
        self.assertEqual(order.side, "buy")
        self.assertEqual(order.price, 50000.0)
        self.assertEqual(order.quantity, 1.0)
        self.assertEqual(order.filled_quantity, 0.0)
        self.assertEqual(order.status, OrderStatus.OPEN)

    def test_is_active(self):
        """is_active() 메서드 테스트"""
        # OPEN 상태
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        self.assertTrue(order.is_active())

        # PARTIALLY_FILLED 상태
        order.status = OrderStatus.PARTIALLY_FILLED
        self.assertTrue(order.is_active())

        # FILLED 상태
        order.status = OrderStatus.FILLED
        self.assertFalse(order.is_active())

    def test_is_completed(self):
        """is_completed() 메서드 테스트"""
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        # OPEN 상태는 완료되지 않음
        self.assertFalse(order.is_completed())

        # 완료 상태들
        for status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
            OrderStatus.FAILED,
        ]:
            order.status = status
            self.assertTrue(order.is_completed())

    def test_remaining_quantity(self):
        """remaining_quantity() 메서드 테스트"""
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=10.0,
            filled_quantity=3.0,
            status=OrderStatus.PARTIALLY_FILLED,
            timestamp=1234567890,
        )

        self.assertEqual(order.remaining_quantity(), 7.0)

        # 전량 체결
        order.filled_quantity = 10.0
        self.assertEqual(order.remaining_quantity(), 0.0)

    def test_update_status(self):
        """update_status() 메서드 테스트"""
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        order.update_status(OrderStatus.FILLED)
        self.assertEqual(order.status, OrderStatus.FILLED)

    def test_update_filled(self):
        """update_filled() 메서드 테스트"""
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=10.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        order.update_filled(5.0, OrderStatus.PARTIALLY_FILLED)
        self.assertEqual(order.filled_quantity, 5.0)
        self.assertEqual(order.status, OrderStatus.PARTIALLY_FILLED)

        order.update_filled(10.0, OrderStatus.FILLED)
        self.assertEqual(order.filled_quantity, 10.0)
        self.assertEqual(order.status, OrderStatus.FILLED)

    def test_create_fill_internal(self):
        """_create_fill() 내부 메서드 테스트"""
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=10.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        # 내부 메서드 호출 (상태 변경 없음)
        filled = order._create_fill(
            fill_id="fill_1",
            price=50000.0,
            quantity=5.0,
            timestamp=1234567900,
            fee=10.0,
        )

        self.assertIsInstance(filled, FilledOrder)
        self.assertEqual(filled.fill_id, "fill_1")
        self.assertEqual(filled.price, 50000.0)
        self.assertEqual(filled.quantity, 5.0)
        self.assertEqual(filled.timestamp, 1234567900)
        self.assertEqual(filled.fee, 10.0)
        self.assertEqual(filled.order, order)

        # 상태가 변경되지 않았는지 확인
        self.assertEqual(order.filled_quantity, 0.0)
        self.assertEqual(order.status, OrderStatus.OPEN)

    def test_fill_process_manual(self):
        """수동 체결 프로세스 테스트 (_create_fill + update_filled)"""
        # 초기 주문: 10개 매수 주문
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=10.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        # 초기 상태 확인
        self.assertEqual(order.remaining_quantity(), 10.0)
        self.assertEqual(order.filled_quantity, 0.0)
        self.assertTrue(order.is_active())

        # 첫 번째 체결: 3개 체결 (수동 처리)
        fill1 = order._create_fill(
            fill_id="fill_1",
            price=50000.0,
            quantity=3.0,
            timestamp=1234567900,
            fee=5.0,
        )
        order.update_filled(3.0, OrderStatus.PARTIALLY_FILLED)

        # 첫 번째 체결 후 상태 확인
        self.assertEqual(fill1.quantity, 3.0)
        self.assertEqual(order.filled_quantity, 3.0)
        self.assertEqual(order.remaining_quantity(), 7.0)
        self.assertEqual(order.status, OrderStatus.PARTIALLY_FILLED)
        self.assertTrue(order.is_active())

        # 두 번째 체결: 4개 체결 (누적 7개)
        fill2 = order._create_fill(
            fill_id="fill_2",
            price=50100.0,
            quantity=4.0,
            timestamp=1234567910,
            fee=7.0,
        )
        order.update_filled(7.0, OrderStatus.PARTIALLY_FILLED)

        # 두 번째 체결 후 상태 확인
        self.assertEqual(fill2.quantity, 4.0)
        self.assertEqual(order.filled_quantity, 7.0)
        self.assertEqual(order.remaining_quantity(), 3.0)
        self.assertEqual(order.status, OrderStatus.PARTIALLY_FILLED)
        self.assertTrue(order.is_active())

        # 세 번째 체결: 나머지 3개 체결 (전량 체결)
        fill3 = order._create_fill(
            fill_id="fill_3",
            price=50200.0,
            quantity=3.0,
            timestamp=1234567920,
            fee=4.0,
        )
        order.update_filled(10.0, OrderStatus.FILLED)

        # 전량 체결 후 상태 확인
        self.assertEqual(fill3.quantity, 3.0)
        self.assertEqual(order.filled_quantity, 10.0)
        self.assertEqual(order.remaining_quantity(), 0.0)
        self.assertEqual(order.status, OrderStatus.FILLED)
        self.assertTrue(order.is_completed())
        self.assertFalse(order.is_active())

        # 생성된 FilledOrder들이 원본 Order를 참조하는지 확인
        self.assertEqual(fill1.order, order)
        self.assertEqual(fill2.order, order)
        self.assertEqual(fill3.order, order)
        self.assertEqual(fill1.order_id, "order_1")
        self.assertEqual(fill2.order_id, "order_1")
        self.assertEqual(fill3.order_id, "order_1")

    def test_process_fill_auto_status_update(self):
        """process_fill() 메서드 테스트 (자동 상태 업데이트)"""
        # 초기 주문: 10개 매수 주문
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=10.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        # 첫 번째 체결: 3개 체결 (자동으로 PARTIALLY_FILLED로 변경)
        fill1 = order.process_fill(
            fill_id="fill_1",
            price=50000.0,
            quantity=3.0,
            timestamp=1234567900,
            fee=5.0,
        )

        # 상태가 자동으로 업데이트되었는지 확인
        self.assertEqual(fill1.quantity, 3.0)
        self.assertEqual(order.filled_quantity, 3.0)
        self.assertEqual(order.remaining_quantity(), 7.0)
        self.assertEqual(order.status, OrderStatus.PARTIALLY_FILLED)
        self.assertTrue(order.is_active())

        # 두 번째 체결: 4개 체결 (여전히 PARTIALLY_FILLED)
        fill2 = order.process_fill(
            fill_id="fill_2",
            price=50100.0,
            quantity=4.0,
            timestamp=1234567910,
            fee=7.0,
        )

        # 상태가 자동으로 업데이트되었는지 확인
        self.assertEqual(fill2.quantity, 4.0)
        self.assertEqual(order.filled_quantity, 7.0)
        self.assertEqual(order.remaining_quantity(), 3.0)
        self.assertEqual(order.status, OrderStatus.PARTIALLY_FILLED)
        self.assertTrue(order.is_active())

        # 세 번째 체결: 나머지 3개 체결 (자동으로 FILLED로 변경)
        fill3 = order.process_fill(
            fill_id="fill_3",
            price=50200.0,
            quantity=3.0,
            timestamp=1234567920,
            fee=4.0,
        )

        # 전량 체결 시 자동으로 FILLED 상태로 변경되었는지 확인
        self.assertEqual(fill3.quantity, 3.0)
        self.assertEqual(order.filled_quantity, 10.0)
        self.assertEqual(order.remaining_quantity(), 0.0)
        self.assertEqual(order.status, OrderStatus.FILLED)
        self.assertTrue(order.is_completed())
        self.assertFalse(order.is_active())

    def test_process_fill_exceeds_remaining_quantity(self):
        """process_fill() 예외 테스트 (남은 수량 초과)"""
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=10.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        # 남은 수량보다 많이 체결 시도
        with self.assertRaises(ValueError) as context:
            order.process_fill(
                fill_id="fill_1",
                price=50000.0,
                quantity=15.0,  # 10개만 주문했는데 15개 체결 시도
                timestamp=1234567900,
                fee=5.0,
            )

        self.assertIn("exceeds remaining quantity", str(context.exception))

    def test_process_fill_with_orderlist_observer(self):
        """process_fill()과 OrderList Observer 통합 테스트"""
        order_list = OrderList()
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=10.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        # OrderList에 추가 (observer 자동 등록)
        order_list.add(order)

        # 초기 상태 확인
        self.assertEqual(len(order_list.get_by_status(OrderStatus.OPEN)), 1)
        self.assertEqual(len(order_list.get_by_status(OrderStatus.PARTIALLY_FILLED)), 0)
        self.assertEqual(len(order_list.get_by_status(OrderStatus.FILLED)), 0)

        # process_fill로 부분 체결 (Observer가 자동으로 리스트 이동)
        order.process_fill(
            fill_id="fill_1",
            price=50000.0,
            quantity=3.0,
            timestamp=1234567900,
            fee=5.0,
        )

        # OPEN → PARTIALLY_FILLED로 자동 이동 확인
        self.assertEqual(len(order_list.get_by_status(OrderStatus.OPEN)), 0)
        self.assertEqual(len(order_list.get_by_status(OrderStatus.PARTIALLY_FILLED)), 1)
        self.assertEqual(len(order_list.get_by_status(OrderStatus.FILLED)), 0)

        # process_fill로 전량 체결 (Observer가 자동으로 리스트 이동)
        order.process_fill(
            fill_id="fill_2",
            price=50100.0,
            quantity=7.0,
            timestamp=1234567910,
            fee=7.0,
        )

        # PARTIALLY_FILLED → FILLED로 자동 이동 확인
        self.assertEqual(len(order_list.get_by_status(OrderStatus.OPEN)), 0)
        self.assertEqual(len(order_list.get_by_status(OrderStatus.PARTIALLY_FILLED)), 0)
        self.assertEqual(len(order_list.get_by_status(OrderStatus.FILLED)), 1)


class TestFilledOrder(unittest.TestCase):
    """FilledOrder 클래스 테스트"""

    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        self.stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m",
        )
        self.order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=10.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

    def test_filled_order_properties(self):
        """FilledOrder 속성 테스트"""
        filled = FilledOrder(
            order=self.order,
            fill_id="fill_1",
            price=50000.0,
            quantity=5.0,
            timestamp=1234567900,
            fee=10.0,
        )

        # 편의 속성 테스트
        self.assertEqual(filled.order_id, "order_1")
        self.assertEqual(filled.stock_address, self.stock_address)

    def test_filled_order_immutability(self):
        """FilledOrder 불변성 테스트 (frozen=True)"""
        filled = FilledOrder(
            order=self.order,
            fill_id="fill_1",
            price=50000.0,
            quantity=5.0,
            timestamp=1234567900,
            fee=10.0,
        )

        # frozen dataclass이므로 속성 변경 시도 시 에러 발생
        with self.assertRaises(Exception):  # FrozenInstanceError
            filled.price = 60000.0


class TestOrderList(unittest.TestCase):
    """OrderList 클래스 테스트 (Observer 패턴)"""

    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        self.stock_address = StockAddress(
            archetype="crypto",
            exchange="binance",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m",
        )

    def test_add_order(self):
        """Order 추가 테스트"""
        order_list = OrderList()
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        order_list.add(order)
        self.assertEqual(len(order_list), 1)
        self.assertIn("order_1", order_list)
        self.assertEqual(order_list.get("order_1"), order)

    def test_remove_order(self):
        """Order 제거 테스트"""
        order_list = OrderList()
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        order_list.add(order)
        order_list.remove("order_1")
        self.assertEqual(len(order_list), 0)
        self.assertNotIn("order_1", order_list)

    def test_get_by_status(self):
        """상태별 Order 조회 테스트"""
        order_list = OrderList()

        # OPEN 주문 2개
        for i in range(2):
            order = Order(
                stock_address=self.stock_address,
                order_id=f"order_{i}",
                side="buy",
                order_type="limit",
                price=50000.0,
                quantity=1.0,
                filled_quantity=0.0,
                status=OrderStatus.OPEN,
                timestamp=1234567890 + i,
            )
            order_list.add(order)

        # FILLED 주문 1개
        order = Order(
            stock_address=self.stock_address,
            order_id="order_filled",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=1.0,
            status=OrderStatus.FILLED,
            timestamp=1234567892,
        )
        order_list.add(order)

        open_orders = order_list.get_by_status(OrderStatus.OPEN)
        filled_orders = order_list.get_by_status(OrderStatus.FILLED)

        self.assertEqual(len(open_orders), 2)
        self.assertEqual(len(filled_orders), 1)

    def test_observer_pattern(self):
        """Observer 패턴 테스트 (상태 변경 시 자동 이동)"""
        order_list = OrderList()
        order = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )

        order_list.add(order)

        # 초기 상태 확인
        self.assertEqual(len(order_list.get_by_status(OrderStatus.OPEN)), 1)
        self.assertEqual(len(order_list.get_by_status(OrderStatus.FILLED)), 0)

        # 상태 변경 (Observer 패턴으로 자동 이동)
        order.update_status(OrderStatus.FILLED)

        # 상태 변경 후 확인
        self.assertEqual(len(order_list.get_by_status(OrderStatus.OPEN)), 0)
        self.assertEqual(len(order_list.get_by_status(OrderStatus.FILLED)), 1)

    def test_get_active(self):
        """Active 주문 조회 테스트"""
        order_list = OrderList()

        # OPEN 주문
        order1 = Order(
            stock_address=self.stock_address,
            order_id="order_1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        order_list.add(order1)

        # PARTIALLY_FILLED 주문
        order2 = Order(
            stock_address=self.stock_address,
            order_id="order_2",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=10.0,
            filled_quantity=5.0,
            status=OrderStatus.PARTIALLY_FILLED,
            timestamp=1234567891,
        )
        order_list.add(order2)

        # FILLED 주문
        order3 = Order(
            stock_address=self.stock_address,
            order_id="order_3",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=1.0,
            status=OrderStatus.FILLED,
            timestamp=1234567892,
        )
        order_list.add(order3)

        active_orders = order_list.get_active()
        self.assertEqual(len(active_orders), 2)

    def test_get_completed(self):
        """완료된 주문 조회 테스트"""
        order_list = OrderList()

        # 다양한 완료 상태의 주문들
        statuses = [
            OrderStatus.FILLED,
            OrderStatus.CANCELED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
            OrderStatus.FAILED,
        ]

        for i, status in enumerate(statuses):
            order = Order(
                stock_address=self.stock_address,
                order_id=f"order_{i}",
                side="buy",
                order_type="limit",
                price=50000.0,
                quantity=1.0,
                filled_quantity=0.0,
                status=status,
                timestamp=1234567890 + i,
            )
            order_list.add(order)

        # OPEN 주문도 하나 추가
        order = Order(
            stock_address=self.stock_address,
            order_id="order_open",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567899,
        )
        order_list.add(order)

        completed_orders = order_list.get_completed()
        self.assertEqual(len(completed_orders), 5)

    def test_timestamp_sorting(self):
        """시간순 정렬 테스트"""
        order_list = OrderList()

        # 역순으로 추가
        timestamps = [1234567893, 1234567891, 1234567892, 1234567890]
        for i, ts in enumerate(timestamps):
            order = Order(
                stock_address=self.stock_address,
                order_id=f"order_{i}",
                side="buy",
                order_type="limit",
                price=50000.0,
                quantity=1.0,
                filled_quantity=0.0,
                status=OrderStatus.OPEN,
                timestamp=ts,
            )
            order_list.add(order)

        # 시간순 정렬 확인
        open_orders = order_list.get_by_status(OrderStatus.OPEN)
        timestamps_sorted = [order.timestamp for order in open_orders]
        self.assertEqual(timestamps_sorted, sorted(timestamps))


if __name__ == "__main__":
    unittest.main()
