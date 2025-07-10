# Trading Functionality Test Guide

This guide will help you test the complete trading functionality of the broker API, including order placement, position tracking, and P&L calculations.

## 🚀 Quick Start

### 1. Start the API Service

```bash
# Start the service with Docker
docker-compose up --build

# Or start without Docker (if you have Python dependencies installed)
cd app
python main.py
```

### 2. Run Quick Health Check

```bash
python quick_test.py
```

This will verify that all API endpoints are working correctly.

## 📊 Trading Demo Scripts

### Comprehensive Trading Demo

The main trading demo script tests the complete trading flow:

```bash
python test_trading_demo.py
```

**What it tests:**
- ✅ Account creation and management
- ✅ Instrument discovery (forex & crypto)
- ✅ Price fetching from Oanda (forex) and Bitunix (crypto)
- ✅ Order placement (buy/sell) for both instrument types
- ✅ Order execution and trade creation
- ✅ Position tracking and updates
- ✅ P&L calculations (realized and unrealized)
- ✅ Account balance updates
- ✅ Trade history tracking

### Account Balance Test

Test account balance tracking and position management:

```bash
python test_account_balance.py
```

**What it tests:**
- ✅ Account balance changes through trading
- ✅ Position creation and updates
- ✅ P&L calculation updates
- ✅ Complete trade cycle (buy then sell)

## 🔧 API Credentials Setup

### For Forex Trading (Oanda)

1. Get Oanda API credentials from [Oanda Practice Account](https://www.oanda.com/account/practice)
2. Set environment variables:

```bash
export OANDA_API_KEY="your_api_key_here"
export OANDA_ACCOUNT_ID="your_account_id_here"
export OANDA_ENVIRONMENT="practice"  # or "live"
```

### For Crypto Trading (Bitunix)

1. Get Bitunix API credentials from [Bitunix](https://www.bitunix.com/)
2. Set environment variables:

```bash
export BITUNIX_API_KEY="your_api_key_here"
export BITUNIX_SECRET_KEY="your_secret_key_here"
```

### Environment File

Create a `.env` file in the root directory:

```env
# Oanda API (Forex)
OANDA_API_KEY=your_oanda_api_key
OANDA_ACCOUNT_ID=your_oanda_account_id
OANDA_ENVIRONMENT=practice

# Bitunix API (Crypto)
BITUNIX_API_KEY=your_bitunix_api_key
BITUNIX_SECRET_KEY=your_bitunix_secret_key

# Database
DATABASE_URL=sqlite:///./broker_api.db

# Logging
LOG_LEVEL=INFO
```

## 📈 Test Scenarios

### Scenario 1: Basic Forex Trading

1. **Create Demo Account**
   ```bash
   curl -X POST "http://localhost:8000/accounts/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Forex Demo", "account_type": "practice", "balance": 10000.0, "currency": "USD"}'
   ```

2. **Get Available Instruments**
   ```bash
   curl "http://localhost:8000/instruments/?instrument_type=forex"
   ```

3. **Place Buy Order**
   ```bash
   curl -X POST "http://localhost:8000/orders/" \
     -H "Content-Type: application/json" \
     -d '{"account_id": 1, "instrument_id": 1, "order_type": "market", "side": "buy", "quantity": 1000.0}'
   ```

4. **Check Position**
   ```bash
   curl "http://localhost:8000/positions/account/1"
   ```

### Scenario 2: Crypto Futures Trading

1. **Create Crypto Account**
   ```bash
   curl -X POST "http://localhost:8000/accounts/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Crypto Demo", "account_type": "practice", "balance": 50000.0, "currency": "USD"}'
   ```

2. **Place Crypto Order**
   ```bash
   curl -X POST "http://localhost:8000/orders/" \
     -H "Content-Type: application/json" \
     -d '{"account_id": 2, "instrument_id": 6, "order_type": "market", "side": "buy", "quantity": 0.1}'
   ```

3. **Update P&L**
   ```bash
   curl -X POST "http://localhost:8000/positions/account/2/update-all-pnl"
   ```

## 🔍 API Endpoints Reference

### Accounts
- `GET /accounts/` - List all accounts
- `POST /accounts/` - Create new account
- `GET /accounts/{id}` - Get account details
- `PUT /accounts/{id}` - Update account

### Instruments
- `GET /instruments/` - List all instruments
- `GET /instruments/{id}` - Get instrument details

### Orders
- `GET /orders/` - List all orders
- `POST /orders/` - Create new order
- `GET /orders/{id}` - Get order details
- `PUT /orders/{id}` - Update order
- `DELETE /orders/{id}` - Cancel order
- `POST /orders/{id}/execute` - Manually execute order

### Positions
- `GET /positions/` - List all positions
- `GET /positions/account/{account_id}` - Get account positions
- `POST /positions/{id}/update-pnl` - Update position P&L
- `POST /positions/account/{account_id}/update-all-pnl` - Update all account positions P&L

### Trades
- `GET /trades/` - List all trades
- `GET /trades/account/{account_id}` - Get account trades

### Prices
- `GET /prices/{symbol}` - Get current price for symbol

## 🧪 Manual Testing with curl

### Test Order Flow

```bash
# 1. Create account
ACCOUNT_ID=$(curl -s -X POST "http://localhost:8000/accounts/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Account", "account_type": "practice", "balance": 10000.0, "currency": "USD"}' | jq -r '.id')

# 2. Get instrument
INSTRUMENT_ID=$(curl -s "http://localhost:8000/instruments/?instrument_type=forex" | jq -r '.items[0].id')

# 3. Place order
ORDER_ID=$(curl -s -X POST "http://localhost:8000/orders/" \
  -H "Content-Type: application/json" \
  -d "{\"account_id\": $ACCOUNT_ID, \"instrument_id\": $INSTRUMENT_ID, \"order_type\": \"market\", \"side\": \"buy\", \"quantity\": 1000.0}" | jq -r '.id')

# 4. Wait and check status
sleep 3
curl -s "http://localhost:8000/orders/$ORDER_ID" | jq '.status'

# 5. Check position
curl -s "http://localhost:8000/positions/account/$ACCOUNT_ID" | jq '.'

# 6. Check account balance
curl -s "http://localhost:8000/accounts/$ACCOUNT_ID" | jq '.balance'
```

## 🐛 Troubleshooting

### Common Issues

1. **Orders not executing**
   - Check if price service is working: `curl "http://localhost:8000/prices/EUR_USD"`
   - Verify API credentials are set correctly
   - Check logs for errors

2. **Price service not working**
   - Verify Oanda/Bitunix API credentials
   - Check network connectivity
   - Review API rate limits

3. **Database issues**
   - Ensure database file is writable
   - Check database initialization: `python app/init_db.py`

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

### API Documentation

Visit the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📊 Expected Results

### Successful Trading Flow

1. **Order Creation**: Order status should be "pending"
2. **Order Execution**: Order status should change to "filled"
3. **Position Creation**: New position should appear with correct quantity and average price
4. **Balance Update**: Account balance should decrease by (quantity × price + commission)
5. **Trade Record**: Trade should be created with execution details
6. **P&L Update**: Position should show unrealized P&L when updated

### Sample Output

```
[14:30:15] INFO: Starting Comprehensive Trading Demo
[14:30:15] SUCCESS: API is healthy
[14:30:15] SUCCESS: Created Forex Demo Account with $25,000.00
[14:30:15] SUCCESS: Created Crypto Demo Account with $50,000.00
[14:30:16] SUCCESS: Found 13 instruments
[14:30:16] INFO: - Forex: 5
[14:30:16] INFO: - Crypto: 8
[14:30:16] SUCCESS: EUR_USD: 1.08543 / 1.08545
[14:30:16] SUCCESS: BTC_USDT: 43250.00 / 43252.00
[14:30:17] SUCCESS: Placed EUR/USD buy order: 10000.0 EUR
[14:30:17] SUCCESS: Placed GBP/USD sell order: 5000.0 GBP
[14:30:17] SUCCESS: Placed BTC/USDT buy order: 0.5 BTC
[14:30:17] SUCCESS: Placed ETH/USDT sell order: 2.0 ETH
[14:30:20] SUCCESS: Order 1: filled at $1.08545
[14:30:20] SUCCESS: Order 2: filled at $1.26543
[14:30:20] SUCCESS: Order 3: filled at $43252.00
[14:30:20] SUCCESS: Order 4: filled at $2650.00
[14:30:20] SUCCESS: Forex Demo Account: 2 positions
[14:30:20] INFO: - EUR_USD: 10000.0000 @ $1.08545
[14:30:20] INFO: Unrealized P&L: $0.00, Realized P&L: $0.00
[14:30:20] INFO: - GBP_USD: -5000.0000 @ $1.26543
[14:30:20] INFO: Unrealized P&L: $0.00, Realized P&L: $0.00
[14:30:20] SUCCESS: Crypto Demo Account: 2 positions
[14:30:20] INFO: - BTC_USDT: 0.5000 @ $43252.00
[14:30:20] INFO: Unrealized P&L: $0.00, Realized P&L: $0.00
[14:30:20] INFO: - ETH_USDT: -2.0000 @ $2650.00
[14:30:20] INFO: Unrealized P&L: $0.00, Realized P&L: $0.00
[14:30:21] SUCCESS: Updated P&L for Forex Demo Account
[14:30:21] SUCCESS: Updated P&L for Crypto Demo Account
[14:30:21] SUCCESS: Forex Demo Account: $13,456.78
[14:30:21] SUCCESS: Crypto Demo Account: $38,234.56
[14:30:21] SUCCESS: Forex Demo Account: 4 trades
[14:30:21] INFO: - BUY 10000.0000 EUR_USD @ $1.08545 ($10.85 commission)
[14:30:21] INFO: - SELL 5000.0000 GBP_USD @ $1.26543 ($6.33 commission)
[14:30:21] SUCCESS: Crypto Demo Account: 2 trades
[14:30:21] INFO: - BUY 0.5000 BTC_USDT @ $43252.00 ($21.63 commission)
[14:30:21] INFO: - SELL 2.0000 ETH_USDT @ $2650.00 ($5.30 commission)
[14:30:21] SUCCESS: Trading Demo Completed Successfully!
```

## 🎯 Next Steps

After successful testing:

1. **Implement Risk Management**: Add position size limits, stop-loss orders
2. **Add More Order Types**: Limit orders, stop orders, trailing stops
3. **Real-time Updates**: WebSocket connections for live price updates
4. **Advanced Analytics**: Performance metrics, drawdown analysis
5. **Multi-account Support**: Portfolio management across multiple accounts
6. **Backtesting**: Historical data analysis and strategy testing

---

**Happy Trading! 🚀** 