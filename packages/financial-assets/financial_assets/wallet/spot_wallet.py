"""Spot trading wallet for managing currencies and assets."""

from __future__ import annotations
from typing import Optional
from ..token import Token
from ..pair import Pair, PairStack
from ..trade import SpotTrade, SpotSide
from ..ledger import SpotLedger
from simple_logger import init_logging, logger


class SpotWallet:
    """현물 거래 지갑.
    화폐 계정, 자산 포지션, 거래 내역을 관리하고 BUY/SELL 거래를 처리합니다.
    """

    @init_logging(level="INFO")
    def __init__(self) -> None:
        """SpotWallet 초기화."""
        self._currencies: dict[str, Token] = {}
        self._pair_stacks: dict[str, PairStack] = {}
        self._ledgers: dict[str, SpotLedger] = {}

    def deposit_currency(self, symbol: str, amount: float) -> None:
        """화폐 입금."""
        logger.info(f"화폐 입금: symbol={symbol}, amount={amount}")
        if symbol in self._currencies:
            self._currencies[symbol] = self._currencies[symbol] + Token(symbol, amount)
        else:
            self._currencies[symbol] = Token(symbol, amount)
        logger.info(f"입금 완료: symbol={symbol}, new_balance={self._currencies[symbol].amount}")

    def withdraw_currency(self, symbol: str, amount: float) -> None:
        """화폐 출금."""
        logger.info(f"화폐 출금 요청: symbol={symbol}, amount={amount}")
        current_balance = self.get_currency_balance(symbol)
        if current_balance < amount:
            self._raise_insufficient_balance(symbol, amount, current_balance)

        self._currencies[symbol] = self._currencies[symbol] - Token(symbol, amount)
        logger.info(f"출금 완료: symbol={symbol}, new_balance={self._currencies[symbol].amount}")

    def get_currency_balance(self, symbol: str) -> float:
        """화폐 잔액 조회."""
        if symbol not in self._currencies:
            return 0.0
        return self._currencies[symbol].amount

    def get_pair_stack(self, ticker: str) -> Optional[PairStack]:
        """특정 거래쌍의 PairStack 조회."""
        if ticker not in self._pair_stacks:
            return None
        stack = self._pair_stacks[ticker]
        if stack.is_empty():
            return None
        return stack

    def get_ledger(self, ticker: str) -> Optional[SpotLedger]:
        """특정 거래쌍의 장부 조회."""
        return self._ledgers.get(ticker)

    def list_currencies(self) -> list[str]:
        """보유 화폐 목록 조회."""
        return list(self._currencies.keys())

    def list_tickers(self) -> list[str]:
        """보유 자산 티커 목록 조회."""
        # 빈 PairStack은 제외
        return [
            ticker
            for ticker, stack in self._pair_stacks.items()
            if not stack.is_empty()
        ]

    def process_trade(self, trade: SpotTrade) -> None:
        """거래 처리 및 장부 기록."""
        ticker = trade.pair.ticker
        logger.info(f"거래 처리 시작: ticker={ticker}, side={trade.side.value}, trade_id={trade.trade_id}")

        if trade.side == SpotSide.BUY:
            self._process_buy_trade(trade)
        else:  # SpotSide.SELL
            self._process_sell_trade(trade)

        logger.info(f"거래 처리 완료: ticker={ticker}, side={trade.side.value}")

    def _process_buy_trade(self, trade: SpotTrade) -> None:
        """BUY 거래 처리: 화폐 차감, PairStack 추가, 장부 기록."""
        logger.debug(f"BUY 거래 처리: asset={trade.pair.get_asset()}, value={trade.pair.get_value()}")

        # 1. quote 화폐 차감
        quote_token = trade.pair.get_value_token()
        quote_symbol = quote_token.symbol
        quote_amount = quote_token.amount

        current_balance = self.get_currency_balance(quote_symbol)
        if current_balance < quote_amount:
            self._raise_insufficient_balance(quote_symbol, quote_amount, current_balance)

        self.withdraw_currency(quote_symbol, quote_amount)

        # 2. PairStack에 Pair 추가
        ticker = trade.pair.ticker
        if ticker not in self._pair_stacks:
            self._pair_stacks[ticker] = PairStack()

        self._pair_stacks[ticker].append(trade.pair)

        # 3. Ledger 기록
        self._record_to_ledger(trade)

        # 4. 수수료 처리
        self._process_fee(trade)

    def _process_sell_trade(self, trade: SpotTrade) -> None:
        """SELL 거래 처리: PairStack 분리(FIFO), 화폐 증가, 장부 기록."""
        ticker = trade.pair.ticker
        logger.debug(f"SELL 거래 처리: ticker={ticker}, asset={trade.pair.get_asset()}")

        # 1. PairStack에서 자산 분리
        if ticker not in self._pair_stacks or self._pair_stacks[ticker].is_empty():
            self._raise_no_position(ticker)

        asset_amount = trade.pair.get_asset()
        current_asset = self._pair_stacks[ticker].total_asset_amount()

        if current_asset < asset_amount:
            self._raise_insufficient_assets(ticker, asset_amount, current_asset)

        # FIFO: split_by_asset_amount로 분리
        self._pair_stacks[ticker].split_by_asset_amount(asset_amount)

        # 2. quote 화폐 증가
        quote_token = trade.pair.get_value_token()
        self.deposit_currency(quote_token.symbol, quote_token.amount)

        # 3. Ledger 기록
        self._record_to_ledger(trade)

        # 4. 수수료 처리
        self._process_fee(trade)

    def _record_to_ledger(self, trade: SpotTrade) -> None:
        """Ledger에 거래 기록."""
        ticker = trade.pair.ticker
        if ticker not in self._ledgers:
            self._ledgers[ticker] = SpotLedger(ticker=ticker)
        self._ledgers[ticker].add_trade(trade)

    def _process_fee(self, trade: SpotTrade) -> None:
        """거래 수수료 처리."""
        if trade.fee is not None:
            fee_symbol = trade.fee.symbol
            fee_amount = trade.fee.amount
            logger.info(f"수수료 차감: symbol={fee_symbol}, amount={fee_amount}")
            self.withdraw_currency(fee_symbol, fee_amount)

    def _raise_insufficient_balance(self, symbol: str, requested: float, available: float) -> None:
        """잔액 부족 에러."""
        logger.error(f"잔액 부족: symbol={symbol}, requested={requested}, available={available}")
        raise ValueError(
            f"Insufficient balance for {symbol}: "
            f"requested {requested}, available {available}"
        )

    def _raise_no_position(self, ticker: str) -> None:
        """포지션 없음 에러."""
        logger.error(f"SELL 거래 실패 - 포지션 없음: ticker={ticker}")
        raise ValueError(f"Insufficient assets for {ticker}: no position available")

    def _raise_insufficient_assets(self, ticker: str, requested: float, available: float) -> None:
        """자산 부족 에러."""
        logger.error(f"SELL 거래 실패 - 자산 부족: ticker={ticker}, requested={requested}, available={available}")
        raise ValueError(
            f"Insufficient assets for {ticker}: "
            f"requested {requested}, available {available}"
        )

    def __str__(self) -> str:
        """읽기 쉬운 문자열 표현 반환."""
        currency_count = len(self._currencies)
        ticker_count = len(self.list_tickers())
        return f"SpotWallet(currencies={currency_count}, tickers={ticker_count})"

    def __repr__(self) -> str:
        """상세한 문자열 표현 반환."""
        return (
            f"SpotWallet(currencies={list(self._currencies.keys())}, "
            f"tickers={self.list_tickers()})"
        )
