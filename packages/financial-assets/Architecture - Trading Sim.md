# Architecture - Trading Sim

financial-assets 패키지의 거시적 방향성을 정하는 문서.

## 단일 마켓 시뮬레이션

전체 마켓 시뮬레이션을 위한 단위 시뮬레이션 인터페이스. 하나의 마켓에서 발생하는 거래를 시뮬레이션하는 기본 빌딩블록 역할을 한다.

### 지정가 거래 처리 흐름

```mermaid
sequenceDiagram
    participant Client as 클라이언트
    participant Wallet as 지갑
    participant API as API/시뮬레이터
    participant OrderBook as 주문장

    Note over Client,OrderBook: 사전 동기화 (API 사용 시)
    Client->>API: 기존 Order 조회
    API->>OrderBook: 거래소에 걸린 Order 동기화

    Note over Client,Wallet: 거래 요청 및 처리
    Client->>Wallet: 잔액/보유량 조회
    Wallet->>Client: 현재 자산 정보
    Client->>Client: 거래 가능 여부 검수
    alt 거래 가능
        Client->>API: limit 거래 요청
        API->>API: API 처리 or 난수 처리
        API->>OrderBook: Order 객체 등록
        OrderBook->>OrderBook: 체결 처리
        OrderBook->>Client: Trade 객체 반환 (체결분)
        Client->>Wallet: Trade 등록
        Wallet->>Wallet: 자산 조정 및 장부 작성
    else 거래 불가
        Client->>Client: 거래 중단
    end
```

### 시장가 거래 처리 흐름

```mermaid
sequenceDiagram
    participant Client as 클라이언트
    participant Wallet as 지갑
    participant API as API/시뮬레이터

    Client->>Wallet: 잔액/보유량 조회
    Wallet->>Client: 현재 자산 정보
    Client->>Client: 거래 가능 여부 검수
    alt 거래 가능
        Client->>API: market 거래 요청
        API->>API: API 처리 or 난수 처리
        API->>Client: Trade 객체 즉시 반환
        Client->>Wallet: Trade 등록
        Wallet->>Wallet: 자산 조정 및 장부 작성
    else 거래 불가
        Client->>Client: 거래 중단
    end
```
