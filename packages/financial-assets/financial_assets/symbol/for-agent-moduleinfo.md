# Symbol
거래쌍 심볼을 파싱하고 다양한 형식으로 변환하는 클래스.

_base: str     # 기준 자산 심볼 (대문자)
_quote: str    # 견적 자산 심볼 (대문자)

__init__(symbol: str)
    raise ValueError
    심볼 파싱 및 초기화. "/" 또는 "-" 구분자 지원. compact 형식("BTCUSDT")은 파싱 불가.

base: str
    기준 자산 심볼 반환 (예: "BTC")

quote: str
    견적 자산 심볼 반환 (예: "USDT")

to_slash() -> str
    슬래시 구분 형식 반환. 예: "BTC/USDT"

to_dash() -> str
    하이픈 구분 형식 반환. 예: "BTC-USDT"

to_compact() -> str
    구분자 없는 형식 반환. 예: "BTCUSDT" (출력 전용, 파싱 불가)

---

**지원 입력 형식:**
- "BTC/USDT" (슬래시 구분)
- "BTC-USDT" (하이픈 구분)
- 대소문자 무관 (자동 대문자 변환)
- 공백 자동 제거

**미지원 형식:**
- "BTCUSDT" (compact) - base/quote 경계 파싱 불가

**동등성 및 해시:**
- 같은 base/quote를 가진 Symbol은 동등 (__eq__ 구현)
- dict 키로 사용 가능 (__hash__ 구현)
- 입력 형식과 무관하게 동등성 비교
- str(symbol)은 to_slash() 형식 반환 (__str__ 구현)
- repr(symbol)은 "Symbol(base='BTC', quote='USDT')" 형식 (__repr__ 구현)

**사용 예시:**
```python
# 다양한 형식 파싱
symbol1 = Symbol("BTC/USDT")
symbol2 = Symbol("btc-usdt")  # 대소문자 무관
symbol3 = Symbol(" ETH / BTC ")  # 공백 제거

# 출력 변환
symbol1.to_slash()    # "BTC/USDT"
symbol1.to_dash()     # "BTC-USDT"
symbol1.to_compact()  # "BTCUSDT"

# 속성 접근
symbol1.base   # "BTC"
symbol1.quote  # "USDT"

# dict 키로 사용
prices = {
    Symbol("BTC/USDT"): 50000.0,
    Symbol("ETH-USDT"): 3000.0
}
```
