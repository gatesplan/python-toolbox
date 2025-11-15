# Throttle Pipeline

Adaptive rate limiting system for any rate-limited APIs.

## Overview

Throttle Pipeline is a generic rate limit management system that works with any rate-limited API. Originally designed for exchange APIs (Binance, Upbit, etc.), it provides adaptive throttling based on real-time response headers and is fully parameterizable for any use case.

## Features

- **Adaptive Throttling**: Configurable threshold-based dynamic safe interval calculation
- **Multi-Window Management**: User-defined multi-window tracking (second/minute/hour/day)
- **Dual Window Support**: Fixed Window (UTC reset) and Sliding Window (rolling)
- **Pluggable Architecture**: HeaderParser strategy pattern for easy extension
- **Zero Request Loss**: Delay instead of rejection to avoid 429 errors
- **Fully Parameterizable**: All policies (thresholds, window configs, parsers) are injectable

## Installation

```bash
# Core library only
pip install git+https://github.com/gatesplan/python-toolbox.git#subdirectory=packages/throttle-pipeline

# With Binance support
pip install "throttle-pipeline[binance] @ git+https://github.com/gatesplan/python-toolbox.git#subdirectory=packages/throttle-pipeline"

# With Upbit support
pip install "throttle-pipeline[upbit] @ git+https://github.com/gatesplan/python-toolbox.git#subdirectory=packages/throttle-pipeline"

# With both
pip install "throttle-pipeline[binance,upbit] @ git+https://github.com/gatesplan/python-toolbox.git#subdirectory=packages/throttle-pipeline"
```

## Usage

### Generic Wrapper (Custom API)

```python
from throttle_pipeline import ThrottleWrapper, ThrottleConfig, WindowConfig, HeaderParser

class MyApiHeaderParser(HeaderParser):
    def parse(self, headers):
        return {
            "requests": RateLimitInfo(
                remaining=int(headers.get("X-RateLimit-Remaining", 0)),
                limit=int(headers.get("X-RateLimit-Limit", 1000)),
                reset_time=...,
                usage_ratio=...
            )
        }

wrapper = ThrottleWrapper(
    api_client=my_api_client,
    config=ThrottleConfig(throttle_threshold=0.7, short_window_threshold=5),
    windows=[WindowConfig(limit=1000, interval_seconds=60, window_type="sliding")],
    header_parser=MyApiHeaderParser()
)
response = wrapper.call(some_request)
```

### Binance Wrapper (Convenience Factory)

```python
from throttle_pipeline import BinanceWrapper

# Default configuration
wrapper = BinanceWrapper(api_key="...", api_secret="...")
response = wrapper.call(request)

# Custom configuration
wrapper = BinanceWrapper(
    api_key="...",
    api_secret="...",
    config=ThrottleConfig(throttle_threshold=0.6, usage_history_size=200),
    windows=[
        WindowConfig(limit=2000, interval_seconds=60, window_type="fixed"),
        WindowConfig(limit=150000, interval_seconds=86400, window_type="fixed")
    ]
)
```

### Upbit Wrapper

```python
from throttle_pipeline import UpbitWrapper

wrapper = UpbitWrapper(access_key="...", secret_key="...")
response = wrapper.call(request)
```

## Configuration

### ThrottleConfig

- `throttle_threshold` (float, default=0.5): Usage ratio threshold to start throttling (0.0-1.0)
- `usage_history_size` (int, default=100): Number of recent requests to track for average calculation
- `min_usage_samples` (int, default=10): Minimum samples required before providing average
- `short_window_threshold` (int, default=10): Threshold in seconds to determine short windows

### WindowConfig

- `limit` (int): Maximum requests allowed in the window
- `interval_seconds` (int): Window duration in seconds
- `window_type` (str): "fixed" (UTC-based reset) or "sliding" (rolling window)

## Development Status

See [Architecture.md](Architecture.md) for detailed design and development progress.
