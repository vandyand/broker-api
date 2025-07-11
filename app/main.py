from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.database import engine, Base
from app.api import accounts, instruments, orders, positions, trades, prices, historical_data
from app.config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting broker API service...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down broker API service...")


# Create FastAPI app
app = FastAPI(
    title="Broker API",
    description="A comprehensive REST API for trading operations with support for forex and cryptocurrency instruments",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(accounts.router)
app.include_router(instruments.router)
app.include_router(orders.router)
app.include_router(positions.router)
app.include_router(trades.router)
app.include_router(prices.router)
app.include_router(historical_data.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Broker API Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "broker-api",
        "version": "1.0.0"
    }


@app.get("/api/v1")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Broker API",
        "version": "1.0.0",
        "description": "Trading operations API with forex and crypto support",
        "endpoints": {
            "accounts": "/accounts",
            "instruments": "/instruments", 
            "orders": "/orders",
            "positions": "/positions",
            "trades": "/trades",
            "prices": "/prices",
            "historical_data": "/historical"
        }
    } 