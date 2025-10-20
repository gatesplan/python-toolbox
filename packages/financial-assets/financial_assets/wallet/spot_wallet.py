"""Spot trading wallet for managing currencies and assets."""

from __future__ import annotations
from typing import Optional
from ..token import Token
from ..pair import Pair, PairStack
from ..trade import SpotTrade, SpotSide
from ..ledger import SpotLedger


class SpotWallet:
    """
    단일 현물 거래 계정의 자산 및 거래 내역 관리.

    SpotWallet은 화폐 계정(USD, KRW 등)과 자산 포지션(BTC-USD, ETH-USD 등)을
    관리하며, 거래를 처리하고 내역을 자동으로 기록합니다.

    - 화폐 관리: 입금/출금, 잔액 조회
    - 거래 처리: BUY/SELL 거래 시 자산 조정 및 장부 기록
    - 포지션 관리: PairStack을 통한 평단가별 레이어 관리
    - 거래 기록: SpotLedger를 통한 자동 내역 기록

    Attributes:
        _currencies (dict[str, Token]): 화폐 계정 (symbol -> Token)
        _pair_stacks (dict[str, PairStack]): 자산 포지션 (ticker -> PairStack)
        _ledgers (dict[str, SpotLedger]): 거래 내역 (ticker -> SpotLedger)

    Examples:
        >>> from financial_assets.wallet import SpotWallet
        >>> from financial_assets.trade import SpotTrade, SpotSide
        >>> from financial_assets.pair import Pair
        >>> from financial_assets.token import Token
        >>> from financial_assets.stock_address import StockAddress
        >>>
        >>> wallet = SpotWallet()
        >>> wallet.deposit_currency(symbol="USD", amount=100000.0)
        >>>
        >>> # BUY 거래 처리
        >>> stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
        >>> trade = SpotTrade(
        ...     stock_address=stock_address,
        ...     trade_id="t1",
        ...     fill_id="f1",
        ...     side=SpotSide.BUY,
        ...     pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
        ...     timestamp=1234567890
        ... )
        >>> wallet.process_trade(trade)
        >>>
        >>> wallet.get_currency_balance("USD")
        50000.0
        >>> wallet.get_pair_stack("BTC-USD").total_asset_amount()
        1.0
    """

    def __init__(self) -> None:
        """SpotWallet 초기화."""
        self._currencies: dict[str, Token] = {}
        self._pair_stacks: dict[str, PairStack] = {}
        self._ledgers: dict[str, SpotLedger] = {}

    def deposit_currency(self, symbol: str, amount: float) -> None:
        """
        화폐 입금.

        Args:
            symbol: 화폐 심볼 (예: "USD", "KRW")
            amount: 입금 금액

        Examples:
            >>> wallet = SpotWallet()
            >>> wallet.deposit_currency("USD", 10000.0)
            >>> wallet.get_currency_balance("USD")
            10000.0
        """
        if symbol in self._currencies:
            self._currencies[symbol] = self._currencies[symbol] + Token(symbol, amount)
        else:
            self._currencies[symbol] = Token(symbol, amount)

    def withdraw_currency(self, symbol: str, amount: float) -> None:
        """
        화폐 출금.

        Args:
            symbol: 화폐 심볼
            amount: 출금 금액

        Raises:
            ValueError: 잔액이 부족한 경우

        Examples:
            >>> wallet = SpotWallet()
            >>> wallet.deposit_currency("USD", 10000.0)
            >>> wallet.withdraw_currency("USD", 3000.0)
            >>> wallet.get_currency_balance("USD")
            7000.0
        """
        current_balance = self.get_currency_balance(symbol)
        if current_balance < amount:
            raise ValueError(
                f"Insufficient balance for {symbol}: "
                f"requested {amount}, available {current_balance}"
            )

        self._currencies[symbol] = self._currencies[symbol] - Token(symbol, amount)

    def get_currency_balance(self, symbol: str) -> float:
        """
        화폐 잔액 조회.

        Args:
            symbol: 화폐 심볼

        Returns:
            float: 잔액 (없으면 0.0)

        Examples:
            >>> wallet = SpotWallet()
            >>> wallet.get_currency_balance("USD")
            0.0
            >>> wallet.deposit_currency("USD", 1000.0)
            >>> wallet.get_currency_balance("USD")
            1000.0
        """
        if symbol not in self._currencies:
            return 0.0
        return self._currencies[symbol].amount

    def get_pair_stack(self, ticker: str) -> Optional[PairStack]:
        """
        특정 거래쌍의 PairStack 조회.

        Args:
            ticker: 거래쌍 티커 (예: "BTC-USD")

        Returns:
            Optional[PairStack]: PairStack 또는 None (없거나 빈 경우)

        Examples:
            >>> wallet = SpotWallet()
            >>> wallet.get_pair_stack("BTC-USD")
            None
        """
        if ticker not in self._pair_stacks:
            return None
        stack = self._pair_stacks[ticker]
        if stack.is_empty():
            return None
        return stack

    def get_ledger(self, ticker: str) -> Optional[SpotLedger]:
        """
        특정 거래쌍의 거래 내역(Ledger) 조회.

        Args:
            ticker: 거래쌍 티커

        Returns:
            Optional[SpotLedger]: SpotLedger 또는 None (없으면)

        Examples:
            >>> wallet = SpotWallet()
            >>> wallet.get_ledger("BTC-USD")
            None
        """
        return self._ledgers.get(ticker)

    def list_currencies(self) -> list[str]:
        """
        보유 화폐 목록 조회.

        Returns:
            list[str]: 화폐 심볼 리스트

        Examples:
            >>> wallet = SpotWallet()
            >>> wallet.deposit_currency("USD", 1000.0)
            >>> wallet.deposit_currency("KRW", 100000.0)
            >>> sorted(wallet.list_currencies())
            ['KRW', 'USD']
        """
        return list(self._currencies.keys())

    def list_tickers(self) -> list[str]:
        """
        보유 자산 티커 목록 조회.

        Returns:
            list[str]: 티커 리스트

        Examples:
            >>> wallet = SpotWallet()
            >>> wallet.list_tickers()
            []
        """
        # 빈 PairStack은 제외
        return [
            ticker
            for ticker, stack in self._pair_stacks.items()
            if not stack.is_empty()
        ]

    def process_trade(self, trade: SpotTrade) -> None:
        """
        거래 처리 및 자산 조정.

        BUY: quote 화폐 차감, PairStack 추가, Ledger 기록
        SELL: PairStack 분리(FIFO), quote 화폐 증가, Ledger 기록

        Args:
            trade: 처리할 SpotTrade 객체

        Raises:
            ValueError: 잔액 또는 자산 부족 시

        Examples:
            >>> from financial_assets.stock_address import StockAddress
            >>> wallet = SpotWallet()
            >>> wallet.deposit_currency("USD", 100000.0)
            >>>
            >>> stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
            >>> trade = SpotTrade(
            ...     stock_address=stock_address,
            ...     trade_id="t1",
            ...     fill_id="f1",
            ...     side=SpotSide.BUY,
            ...     pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            ...     timestamp=1234567890
            ... )
            >>> wallet.process_trade(trade)
            >>> wallet.get_currency_balance("USD")
            50000.0
        """
        if trade.side == SpotSide.BUY:
            self._process_buy_trade(trade)
        else:  # SpotSide.SELL
            self._process_sell_trade(trade)

    def _process_buy_trade(self, trade: SpotTrade) -> None:
        """
        BUY 거래 처리.

        1. quote 화폐 잔액 확인 및 차감
        2. PairStack에 Pair 추가
        3. SpotLedger에 거래 기록

        Args:
            trade: BUY SpotTrade
        """
        # 1. quote 화폐 차감
        quote_token = trade.pair.get_value_token()
        quote_symbol = quote_token.symbol
        quote_amount = quote_token.amount

        current_balance = self.get_currency_balance(quote_symbol)
        if current_balance < quote_amount:
            raise ValueError(
                f"Insufficient balance for {quote_symbol}: "
                f"requested {quote_amount}, available {current_balance}"
            )

        self.withdraw_currency(quote_symbol, quote_amount)

        # 2. PairStack에 Pair 추가
        ticker = self._get_ticker(trade.pair)
        if ticker not in self._pair_stacks:
            self._pair_stacks[ticker] = PairStack()

        self._pair_stacks[ticker].append(trade.pair)

        # 3. Ledger 기록
        if ticker not in self._ledgers:
            self._ledgers[ticker] = SpotLedger(ticker=ticker)

        self._ledgers[ticker].add_trade(trade)

    def _process_sell_trade(self, trade: SpotTrade) -> None:
        """
        SELL 거래 처리.

        1. PairStack에서 자산 분리 (FIFO)
        2. quote 화폐 증가
        3. SpotLedger에 거래 기록

        Args:
            trade: SELL SpotTrade
        """
        ticker = self._get_ticker(trade.pair)

        # 1. PairStack에서 자산 분리
        if ticker not in self._pair_stacks or self._pair_stacks[ticker].is_empty():
            raise ValueError(
                f"Insufficient assets for {ticker}: no position available"
            )

        asset_amount = trade.pair.get_asset()
        current_asset = self._pair_stacks[ticker].total_asset_amount()

        if current_asset < asset_amount:
            raise ValueError(
                f"Insufficient assets for {ticker}: "
                f"requested {asset_amount}, available {current_asset}"
            )

        # FIFO: split_by_asset_amount로 분리
        self._pair_stacks[ticker].split_by_asset_amount(asset_amount)

        # 2. quote 화폐 증가
        quote_token = trade.pair.get_value_token()
        self.deposit_currency(quote_token.symbol, quote_token.amount)

        # 3. Ledger 기록
        if ticker not in self._ledgers:
            self._ledgers[ticker] = SpotLedger(ticker=ticker)

        self._ledgers[ticker].add_trade(trade)

    def _get_ticker(self, pair: Pair) -> str:
        """
        Pair로부터 ticker 문자열 생성.

        Args:
            pair: Pair 객체

        Returns:
            str: ticker (예: "BTC-USD")
        """
        asset_symbol = pair.get_asset_token().symbol
        value_symbol = pair.get_value_token().symbol
        return f"{asset_symbol}-{value_symbol}"

    def __str__(self) -> str:
        """
        SpotWallet의 읽기 쉬운 문자열 표현.

        Returns:
            str: 화폐 및 자산 정보
        """
        currency_count = len(self._currencies)
        ticker_count = len(self.list_tickers())
        return f"SpotWallet(currencies={currency_count}, tickers={ticker_count})"

    def __repr__(self) -> str:
        """
        SpotWallet의 상세한 문자열 표현.

        Returns:
            str: 상세 정보
        """
        return (
            f"SpotWallet(currencies={list(self._currencies.keys())}, "
            f"tickers={self.list_tickers()})"
        )
