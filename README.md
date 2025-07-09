# Broker API Service

A comprehensive REST API for trading operations with support for forex and cryptocurrency instruments. This service provides a complete trading platform with account management, order execution, position tracking, and real-time price data.

## Features

- **Account Management**: Create and manage trading accounts (practice/live)
- **Instrument Support**: Forex and cryptocurrency instruments with real-time pricing
- **Order Management**: Market, limit, stop, and stop-limit orders
- **Position Tracking**: Automatic position updates with P&L calculations
- **Trade History**: Complete trade execution history
- **Real-time Pricing**: Integration with OANDA (forex) and Bitunix (crypto futures)
- **SQLite Database**: Lightweight database with easy migration path
- **Docker Support**: Containerized deployment
- **RESTful API**: Comprehensive CRUD operations

## Architecture

```
├── app/
│   ├── api/           # API route handlers
│   ├── models/        # SQLAlchemy database models
│   ├── schemas/       # Pydantic request/response schemas
│   ├── services/      # Business logic services
│   ├── config.py      # Configuration management
│   ├── database.py    # Database connection
│   └── main.py        # FastAPI application
├── data/              # SQLite database files
├── Dockerfile         # Docker containerization
├── docker-compose.yml # Docker Compose configuration
└── requirements.txt   # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)
- OANDA API credentials (for forex pricing)
- Bitunix API credentials (for crypto futures pricing)

### Environment Setup

1. Copy the environment template:
```bash
cp env.example .env
```

2. Edit `.env` with your API credentials:
```bash
# OANDA Configuration
OANDA_API_KEY=your_oanda_api_key_here
OANDA_ACCOUNT_ID=your_oanda_account_id_here
OANDA_ENVIRONMENT=practice

# Bitunix Configuration (Cryptocurrency Futures)
BITUNIX_API_KEY=your_bitunix_api_key_here
BITUNIX_SECRET_KEY=your_bitunix_secret_key_here
```

### Running with Docker (Recommended)

1. Build and start the service:
```bash
docker-compose up --build
```

2. The API will be available at `http://localhost:8000`

3. View the interactive API documentation at `http://localhost:8000/docs`

### Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python -m app.init_db
```

3. Start the service:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Accounts
- `POST /accounts/` - Create account
- `GET /accounts/` - List accounts (paginated)
- `GET /accounts/{id}` - Get account details
- `PUT /accounts/{id}` - Update account
- `DELETE /accounts/{id}` - Delete account

### Instruments
- `POST /instruments/` - Create instrument
- `GET /instruments/` - List instruments (paginated)
- `GET /instruments/{id}` - Get instrument details
- `GET /instruments/symbol/{symbol}` - Get instrument by symbol
- `PUT /instruments/{id}` - Update instrument
- `DELETE /instruments/{id}` - Delete instrument

### Orders
- `POST /orders/` - Create order
- `GET /orders/` - List orders (paginated)
- `GET /orders/{id}` - Get order details
- `PUT /orders/{id}` - Update order
- `DELETE /orders/{id}` - Cancel order
- `POST /orders/{id}/execute` - Manually execute order

### Positions
- `POST /positions/` - Create position
- `GET /positions/` - List positions (paginated)
- `GET /positions/{id}` - Get position details
- `GET /positions/account/{account_id}` - Get account positions
- `PUT /positions/{id}` - Update position
- `DELETE /positions/{id}` - Delete position
- `POST /positions/{id}/update-pnl` - Update position P&L

### Trades
- `GET /trades/` - List trades (paginated)
- `GET /trades/{id}` - Get trade details
- `GET /trades/account/{account_id}` - Get account trades
- `GET /trades/order/{order_id}` - Get order trades
- `GET /trades/instrument/{instrument_id}` - Get instrument trades

### Prices
- `GET /prices/{symbol}` - Get current price
- `GET /prices/instrument/{instrument_id}` - Get price by instrument ID
- `POST /prices/batch` - Get batch prices
- `GET /prices/account/{account_id}/positions` - Get account position prices

## Usage Examples

### Creating a Trading Account
```bash
curl -X POST "http://localhost:8000/accounts/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Trading Account",
    "account_type": "practice",
    "balance": 10000.0,
    "currency": "USD"
  }'
```

### Placing a Market Order
```bash
curl -X POST "http://localhost:8000/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "instrument_id": 1,
    "order_type": "market",
    "side": "buy",
    "quantity": 100.0
  }'
```

### Getting Current Price
```bash
curl -X GET "http://localhost:8000/prices/EUR_USD"
```

### Getting Account Positions
```bash
curl -X GET "http://localhost:8000/positions/account/1"
```

## Database Schema

### Accounts
- `id`: Primary key
- `name`: Account name (unique)
- `account_type`: practice/live
- `balance`: Current balance
- `currency`: Account currency
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Instruments
- `id`: Primary key
- `symbol`: Trading symbol (unique)
- `name`: Instrument name
- `instrument_type`: forex/crypto/equity/future
- `base_currency`: Base currency
- `quote_currency`: Quote currency
- `min_quantity`: Minimum order quantity
- `max_quantity`: Maximum order quantity
- `tick_size`: Price tick size
- `is_active`: Active status

### Orders
- `id`: Primary key
- `account_id`: Account reference
- `instrument_id`: Instrument reference
- `order_type`: market/limit/stop/stop_limit
- `side`: buy/sell
- `quantity`: Order quantity
- `price`: Limit price (optional)
- `stop_price`: Stop price (optional)
- `status`: pending/filled/partially_filled/cancelled/rejected
- `filled_quantity`: Filled quantity
- `average_fill_price`: Average fill price
- `commission`: Commission amount

### Positions
- `id`: Primary key
- `account_id`: Account reference
- `instrument_id`: Instrument reference
- `quantity`: Current position quantity
- `average_price`: Average entry price
- `unrealized_pnl`: Unrealized profit/loss
- `realized_pnl`: Realized profit/loss

### Trades
- `id`: Primary key
- `order_id`: Order reference
- `account_id`: Account reference
- `instrument_id`: Instrument reference
- `side`: buy/sell
- `quantity`: Trade quantity
- `price`: Execution price
- `commission`: Commission amount
- `realized_pnl`: Realized profit/loss
- `executed_at`: Execution timestamp

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./data/broker.db` |
| `OANDA_API_KEY` | OANDA API key | None |
| `OANDA_ACCOUNT_ID` | OANDA account ID | None |
| `OANDA_ENVIRONMENT` | OANDA environment | `practice` |
| `BITUNIX_API_KEY` | Bitunix API key | None |
| `BITUNIX_SECRET_KEY` | Bitunix secret key | None |
| `DEBUG` | Debug mode | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
The service uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations.

### Adding New Instrument Types
1. Add the new type to `InstrumentType` enum in `app/models.py`
2. Update the price service to handle the new type
3. Add appropriate validation in the API routes

## Production Deployment

### Security Considerations
- Configure proper CORS settings
- Add authentication/authorization
- Use environment-specific configurations
- Enable HTTPS
- Implement rate limiting
- Add request validation

### Scaling
- Use PostgreSQL or MySQL for production databases
- Implement connection pooling
- Add caching layer (Redis)
- Use load balancers for high availability
- Implement monitoring and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 