# SpotLimitFillService
지정가 주문 체결 서비스. 가격 범위에 따라 차등적으로 체결 파라미터를 생성한다.

`execute(order: SpotOrder, price: Price) -> List[TradeParams]`
지정가 주문 체결 파라미터를 생성한다. body 범위는 전량, head/tail 범위는 확률적 체결을 적용한다.


# SpotMarketBuyFillService
시장가 매수 체결 서비스. 항상 체결되며 head 범위에서 슬리피지를 반영한다.

`execute(order: SpotOrder, price: Price) -> List[TradeParams]`
시장가 매수 체결 파라미터를 생성한다. 1~3개로 분할하며 각 조각마다 다른 가격을 샘플링한다.


# SpotMarketSellFillService
시장가 매도 체결 서비스. 항상 체결되며 tail 범위에서 슬리피지를 반영한다.

`execute(order: SpotOrder, price: Price) -> List[TradeParams]`
시장가 매도 체결 파라미터를 생성한다. 1~3개로 분할하며 각 조각마다 다른 가격을 샘플링한다.


# SpotTradeFactoryService
Trade 생성 서비스. TradeParams를 받아 실제 SpotTrade 객체로 변환한다.

`create_trades(order: SpotOrder, params_list: List[TradeParams], timestamp: int) -> List[SpotTrade]`
TradeParams 리스트로부터 SpotTrade 리스트를 생성한다. Trade ID, 수수료, Pair 구성을 담당한다.
