#!/usr/bin/env python3
"""
Simple test runner for basic end-to-end test
"""
import sys
import os
import asyncio

def check_services():
    """Check if required services are running"""
    print("Checking if required services are running...")
    
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
        print("Please start services with: docker-compose up -d")
        return False
    
    return True

def run_simple_test():
    """Run the simple end-to-end test"""
    print("=" * 50)
    print("Running Simple End-to-End Test")
    print("=" * 50)
    
    # Check services
    if not check_services():
        sys.exit(1)
    
    # Add parent directory to Python path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    
    # Import and run the test
    try:
        from tests.test_simple_end_to_end import TestSimpleEndToEnd
        
        async def run_test():
            test = TestSimpleEndToEnd()
            return await test.test_basic_moving_average_calculation()
        
        success = asyncio.run(run_test())
        
        if success:
            print("\n✅ Simple end-to-end test passed!")
            return True
        else:
            print("\n❌ Simple end-to-end test failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = run_simple_test()
    sys.exit(0 if success else 1) 