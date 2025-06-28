#!/usr/bin/env python3
"""
Test runner for end-to-end tests
"""
import sys
import os
import subprocess
import time

def check_services_running():
    """Check if required services are running"""
    print("Checking if required services are running...")
    
    # Check if we can connect to the services
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="postgres",
            port=5432,
            database="market_data",
            user="arnav",
            password="market123"
        )
        conn.close()
        print("✓ PostgreSQL is running")
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False
    
    try:
        from confluent_kafka import Producer
        producer = Producer({'bootstrap.servers': 'localhost:9092'})
        producer.flush(timeout=5)
        print("✓ Kafka is running")
    except Exception as e:
        print(f"✗ Kafka connection failed: {e}")
        return False
    
    return True

def run_tests():
    """Run the end-to-end tests"""
    print("=" * 60)
    print("Running End-to-End Tests for Market Data Service")
    print("=" * 60)
    
    # Check if services are running
    if not check_services_running():
        print("\n❌ Required services are not running!")
        print("Please start the services using: docker-compose up -d")
        sys.exit(1)
    
    # Add the parent directory to Python path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    
    # Run pytest
    print("\n🚀 Starting tests...")
    test_args = [
        "pytest",
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        "tests/test_end_to_end.py"
    ]
    
    try:
        result = subprocess.run(test_args, cwd=parent_dir, check=True)
        print("\n✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code: {e.returncode}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 