#!/usr/bin/env python3
"""
Simple database initialization script for Market Data Service.
Creates PostgreSQL tables using SQLAlchemy.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import engine, Base
from app.models import RawMarketData  # Import to register with Base

def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database() 