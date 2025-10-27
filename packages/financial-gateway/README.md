# Financial Gateway

거래소 API 및 시뮬레이션 환경과의 통합 인터페이스를 제공하는 게이트웨이 패키지입니다.

## 개요

거래 전략 실행자와 실제 거래 발생 지점(거래소 API, 시뮬레이션) 사이를 매개하는 인터페이스 어댑터를 제공합니다.

## 주요 기능

- Spot 거래 게이트웨이
- Futures 거래 게이트웨이
- 거래소별 구현 (Binance, Upbit 등)
- 시뮬레이션 환경 통합

## 의존성

- financial-assets: 금융 자산 도메인 객체
- binance-connector: Binance API 클라이언트
- python-upbit-api: Upbit API 클라이언트
