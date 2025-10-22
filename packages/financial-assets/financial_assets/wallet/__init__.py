"""Wallet module for managing spot trading accounts and analysis.

This module provides:
- SpotWallet: Manages currencies, assets (PairStacks), and trade history
- WalletInspector: Provides statistics and analysis using director-worker pattern
- WalletWorker: Abstract base class for custom analysis workers
"""

from .spot_wallet import SpotWallet
from .wallet_inspector import WalletInspector
from .workers import WalletWorker

__all__ = ["SpotWallet", "WalletInspector", "WalletWorker"]
