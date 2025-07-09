#!/bin/bash

# Broker API Startup Script

echo "🚀 Starting Broker API Service..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your API credentials before starting the service"
    echo "   Required: OANDA_API_KEY, OANDA_ACCOUNT_ID, BITUNIX_API_KEY, BITUNIX_SECRET_KEY"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Check if running with Docker
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose up --build
else
    echo "🐍 Starting with Python..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    
    # Initialize database
    echo "🗄️  Initializing database..."
    python -m app.init_db
    
    # Start the service
    echo "🚀 Starting FastAPI server..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
fi 