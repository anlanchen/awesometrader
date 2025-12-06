# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AwesomeTrader is a comprehensive quantitative trading system built with Python, integrating data collection, strategy development, backtesting, and live trading capabilities. The system is based on LongPort OpenAPI and provides multi-market support for US, HK, CN, and SG markets.

## Core Architecture

### Main Components

- **`awesometrader/`** - Core framework modules (imported via `__init__.py`)
  - `collector.py` - Data collection using LongPort OpenAPI (`LongPortAPI` class)
  - `data/data_interface.py` - Data persistence and retrieval in CSV/Parquet formats (`DataInterface` class)
  - `trader/longport_trader_api.py` - Trading execution and account management (`LongPortTraderAPI` class)
  - `notify/dingtalk_messager.py` - DingTalk notification system (`DingTalkMessager` class)
  - `utils.py` - Common utilities (`Utils` class with project root and cache directory helpers)

- **`strategies/`** - Trading strategy implementations
  - Built on `backtesting.py` framework
  - Each strategy must implement `init()` and `next()` methods
  - Includes: `sma.py`, `sma_cross.py`, `macd.py`, `mfi.py`, `multi_factor.py`

- **`run_*.py`** - Main execution scripts (entry points)
  - `run_collector.py` - Interactive data collection orchestration
  - `run_trader.py` - Trading execution (currently placeholder)
  - `run_messager.py` - Daily account reporting and DingTalk notifications

- **`tests/`** - Test suite using Python's `unittest` framework
  - `test_data_simple.py` - Tests for data collection and persistence
  - `test_trade_simple.py` - Tests for trading operations (balance, positions, cash flow, orders)
  - `test_message_simple.py` - Tests for messaging functionality

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (recommended)
make install

# Or manually with uv
uv sync

# Clean project
make clean
```

### Running Applications
```bash
# Interactive data collection
python run_collector.py

# Account messaging/reporting
python run_messager.py

# With uv
uv run python run_collector.py
uv run python run_messager.py
```

### Testing
```bash
# Run all tests (using unittest or pytest)
python -m pytest tests/
# Or individually
python tests/test_data_simple.py
python tests/test_trade_simple.py
python tests/test_message_simple.py

# Run specific test case
python tests/test_trade_simple.py TestTradeModule.test_get_account_balance
python -m pytest tests/test_trade_simple.py::TestTradeModule::test_get_cash_flow -v
```

## Key Technical Details

### Data Flow
1. **Collection**: LongPort API → `collector.py` → cached CSV/Parquet files
2. **Processing**: `data/data_interface.py` handles data validation and persistence
3. **Strategy**: Backtesting framework processes historical data
4. **Trading**: `trader.py` executes orders via LongPort API
5. **Monitoring**: `messager.py` sends DingTalk notifications

### Market Support
- **US Markets**: NYSE, NASDAQ with pre/post market data
- **HK Markets**: HKEX with morning/afternoon sessions
- **CN Markets**: Shanghai/Shenzhen Stock Exchanges
- **SG Markets**: Singapore Exchange

### Environment Configuration
The system uses `.env` files for configuration. Key variables:
- `LONGPORT_*` - API credentials
- `START_DATE` - Historical data collection start date
- `STOCK_POOL_FILE` - Stock watchlist file
- `UPDATE_DELAY_MINUTES` - Post-market update delay

### Data Storage
- **Format**: CSV (primary), Parquet (optional)
- **Structure**: `/caches/{SYMBOL}/{period}.csv`
- **Periods**: Day, Week, Month, Quarter, Year
- **Validation**: Automatic data integrity checks

### Trading Session Management
- Dynamic trading session detection via API
- Multi-timezone support with automatic conversion
- Scheduled data updates based on market hours
- Trading day validation for each market

## Common Development Patterns

### Adding New Trader Methods
When adding new trading API methods to `trader.py`:
1. Check LongPort API documentation at https://open.longbridge.com/
2. Follow the pattern of existing methods (e.g., `get_stock_positions`, `get_cash_flow`)
3. Add comprehensive error handling with `loguru` logging
4. Return appropriate data types (usually `List[Any]` for collections)
5. Add corresponding test case in `tests/test_trade_simple.py` following the existing test structure:
   - Use `unittest.TestCase` base class
   - Test multiple scenarios (all data, filtered data, edge cases)
   - Verify data structure with `assertIsInstance` and `assertTrue(hasattr(...))`
   - Log detailed results for debugging
   - Add test to the suite at the bottom of the file

### Adding New Strategies
1. Create strategy file in `strategies/` directory
2. Inherit from `backtesting.py` framework base classes (`Strategy`)
3. Implement `init()` for indicator setup and `next()` for trading logic
4. Use technical indicators from TA-Lib (imported as `talib`)
5. Access price data via `self.data` (OHLCV)

### Data Collection Workflow
The `LongPortAPI` class orchestrates multi-market data collection:
1. Sync watchlist from LongPort: `sync_watchlist_to_stock_pool()`
2. Collect historical data: `collect_historical_data()`
3. Update latest data: `update_latest_data_by_market()`
4. Schedule automatic updates: `setup_daily_trading_session_update()`

### Testing Patterns
- All tests use `unittest` framework with `setUp()` and `tearDown()` methods
- Tests are organized by module: data, trade, message
- Each test includes detailed logging with `loguru` for debugging
- Use `self.assertIsNotNone()`, `self.assertIsInstance()`, `self.assertEqual()` for validation
- Tests print summaries with statistics (counts, distributions, etc.)

## Dependencies

Core dependencies managed via `pyproject.toml` (Python 3.10+):
- `longport` - LongPort OpenAPI client for market data and trading
- `backtesting` - Strategy backtesting framework
- `ta-lib` - Technical analysis indicators (SMA, MACD, RSI, MFI, etc.)
- `pandas` + `numpy` - Data manipulation and numerical computing
- `pyarrow` - Parquet file format support
- `loguru` - Structured logging throughout the system
- `schedule` - Task scheduling for automated data updates
- `python-dotenv` - Environment configuration (.env files)
- `pytz` - Timezone handling for multi-market support
- `requests` - HTTP client
- `humanize` - Human-readable data formatting

Package management uses `uv` (modern Python package manager).

## Important Notes

### API and Data
- All timestamps are timezone-aware using `pytz`
- Stock symbols follow format: `SYMBOL.MARKET` (e.g., `BABA.US`, `700.HK`, `000001.SH`)
- API rate limiting is implemented to respect LongPort limits
- Data files are automatically organized: `/caches/{SYMBOL}/{period}.csv`

### Code Patterns
- Module imports: `from awesometrader import LongPortAPI, DataInterface, LongPortTraderAPI, DingTalkMessager, Utils`
- All core classes initialize from environment variables via `Config.from_env()` (LongPort)
- Project root detection: `Utils.get_project_root()` (searches for `pyproject.toml`, `.env`, or `uv.lock`)
- Cache directory: `Utils.get_cache_dir()` (creates `/caches` if not exists)

### Trading
- `LongPortTraderAPI` class provides methods for: account balance, stock positions, cash flow, order operations
- Order lifecycle: submit → get_detail/get_today_orders → replace (modify) → cancel
- Supports multiple order types: LO (limit), MO (market), conditional orders
- Both paper trading and live trading modes supported (configured via LongPort API credentials)