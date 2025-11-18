"""
throttled-api 메서드 테스트 커버리지 분석
"""

# 이미 테스트한 메서드
tested = {
    'get_account',
    'get_ticker_24hr',
    'create_order',  # MARKET order
}

categories = {
    'General': ['ping', 'get_server_time', 'get_exchange_info'],
    'Market Data (read-only)': [
        'get_order_book', 'get_recent_trades', 'get_historical_trades',
        'get_aggregate_trades', 'get_klines', 'get_ui_klines',
        'get_avg_price', 'get_ticker', 'get_ticker_price',
        'get_orderbook_ticker', 'get_rolling_window_ticker'
    ],
    'Trading (order create)': [
        'create_order', 'test_order', 'create_oco_order',
        'create_oto_order', 'create_otoco_order', 'create_sor_order',
        'test_sor_order'
    ],
    'Trading (order manage)': [
        'get_order', 'cancel_order', 'cancel_open_orders',
        'cancel_replace_order', 'cancel_order_list', 'get_order_list'
    ],
    'Account': [
        'get_account', 'get_open_orders', 'get_all_orders',
        'get_all_order_list', 'get_open_order_list', 'get_my_trades',
        'get_my_allocations', 'get_account_commission',
        'get_rate_limit_order', 'get_my_prevented_matches'
    ],
    'User Data Stream': [
        'create_listen_key', 'keep_alive_listen_key', 'close_listen_key'
    ]
}

print("=" * 80)
print("throttled-api Method Test Coverage")
print("=" * 80)
print()

total_methods = sum(len(methods) for methods in categories.values())
total_tested = len(tested)

for category, methods in categories.items():
    untested = [m for m in methods if m not in tested]
    tested_in_cat = [m for m in methods if m in tested]
    
    print(f"\n[{category}]")
    print(f"  Total: {len(methods)} | Tested: {len(tested_in_cat)} | Untested: {len(untested)}")
    
    if tested_in_cat:
        print(f"  [OK] Tested: {', '.join(tested_in_cat)}")
    
    if untested:
        print(f"  [TODO] Untested:")
        for m in untested:
            print(f"    - {m}")

print()
print("=" * 80)
print(f"Overall Coverage: {total_tested}/{total_methods} ({total_tested*100//total_methods}%)")
print("=" * 80)

# 우선순위별 추천
print()
print("=" * 80)
print("Recommended Test Priority")
print("=" * 80)

priority_high = [
    ('ping', 'General - 가장 기본적인 연결 테스트'),
    ('get_server_time', 'General - 시간 동기화 확인'),
    ('get_order_book', 'Market Data - 호가창 조회 (자주 사용)'),
    ('get_klines', 'Market Data - 캔들 데이터 (자주 사용)'),
    ('get_order', 'Trading - 이미 생성한 주문 조회'),
    ('get_open_orders', 'Account - 미체결 주문 확인'),
    ('get_my_trades', 'Account - 체결 내역 확인'),
]

print("\n[HIGH Priority] - 자주 사용되고 안전한 읽기 전용:")
for method, desc in priority_high:
    print(f"  - {method:30s} : {desc}")

priority_medium = [
    ('get_recent_trades', 'Market Data - 최근 체결 내역'),
    ('get_ticker_price', 'Market Data - 현재가 간단 조회'),
    ('get_orderbook_ticker', 'Market Data - 호가 최우선가'),
    ('test_order', 'Trading - 주문 유효성 검증 (실제 주문X)'),
    ('get_all_orders', 'Account - 전체 주문 내역'),
]

print("\n[MEDIUM Priority] - 필요시 사용:")
for method, desc in priority_medium:
    print(f"  - {method:30s} : {desc}")

priority_low = [
    ('cancel_order', 'Trading - 실제 주문 필요, 신중히 테스트'),
    ('create_oco_order', 'Trading - OCO 주문, 복잡한 시나리오'),
    ('create_listen_key', 'User Data Stream - 웹소켓 연동'),
]

print("\n[LOW Priority] - 특수 케이스 또는 위험:")
for method, desc in priority_low:
    print(f"  - {method:30s} : {desc}")

print()
