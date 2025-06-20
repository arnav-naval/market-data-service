#!/usr/bin/env python3
"""
Database initialization script for Market Data Service.
Uses Alembic to create and manage database tables.
"""

import sys
import os
import subprocess

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def init_database():
    """Initialize database using Alembic"""
    print("Initializing database with Alembic...")
    
    try:
        # Generate initial migration if none exists
        print("Generating initial migration...")
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial migration"], 
                      check=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        # Apply the migration
        print("Applying migration...")
        subprocess.run(["alembic", "upgrade", "head"], 
                      check=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        print("Database initialized successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database() 