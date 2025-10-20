"""Ledger module for tracking spot trade history.

This module provides data structures for recording and analyzing trade history
for spot trading pairs.
"""

from .spot_ledger_entry import SpotLedgerEntry
from .spot_ledger import SpotLedger

__all__ = ["SpotLedgerEntry", "SpotLedger"]
