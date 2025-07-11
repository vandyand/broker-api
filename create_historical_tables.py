#!/usr/bin/env python3
"""
Create Historical Data Tables
Creates the database tables for historical candlestick data
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.database import engine
from app.models.historical_data import Base

load_dotenv()


def create_historical_tables():
    """Create historical data tables"""
    print("🔧 Creating Historical Data Tables")
    print("=" * 50)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Historical data tables created successfully!")
        
        # List created tables
        tables = Base.metadata.tables.keys()
        print(f"📋 Created tables: {', '.join(tables)}")
        
        print("\n📊 Table Details:")
        for table_name, table in Base.metadata.tables.items():
            print(f"  - {table_name}: {len(table.columns)} columns")
            for column in table.columns:
                print(f"    • {column.name}: {column.type}")
        
        print("\n🎉 Database setup complete!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    create_historical_tables() 