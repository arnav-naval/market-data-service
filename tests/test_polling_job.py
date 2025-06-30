#!/usr/bin/env python3
"""
Test script for polling job functionality
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://app:8000/v1"
TEST_SYMBOLS = ["AAPL", "MSFT", "GOOGL"]
TEST_INTERVAL = 60  # 60 seconds
TEST_PROVIDER = "alpha_vantage"

async def test_polling_job():
    """Test the complete polling job workflow"""
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Polling Job Functionality")
        print("=" * 50)
        
        # 1. Start a polling job
        print("\n1. Starting polling job...")
        poll_request = {
            "symbols": TEST_SYMBOLS,
            "interval": TEST_INTERVAL,
            "provider": TEST_PROVIDER
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/prices/poll",
                json=poll_request,
                timeout=30.0
            )
            response.raise_for_status()
            
            job_data = response.json()
            job_id = job_data["job_id"]
            
            print(f"✅ Polling job created successfully!")
            print(f"   Job ID: {job_id}")
            print(f"   Status: {job_data['status']}")
            print(f"   Config: {json.dumps(job_data['config'], indent=2)}")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to create polling job: {e}")
            print(f"   Response: {e.response.text}")
            return
        except Exception as e:
            print(f"❌ Error creating polling job: {e}")
            return
        
        # 2. Check job status
        print(f"\n2. Checking job status for {job_id}...")
        try:
            response = await client.get(f"{BASE_URL}/jobs/{job_id}")
            response.raise_for_status()
            
            status_data = response.json()
            print(f"✅ Job status retrieved!")
            print(f"   Status: {status_data['status']}")
            print(f"   Symbols: {status_data['symbols']}")
            print(f"   Interval: {status_data['interval']}s")
            print(f"   Provider: {status_data['provider']}")
            print(f"   Created: {status_data['created_at']}")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to get job status: {e}")
            print(f"   Response: {e.response.text}")
        except Exception as e:
            print(f"❌ Error getting job status: {e}")
        
        # 3. List all jobs
        print(f"\n3. Listing all jobs...")
        try:
            response = await client.get(f"{BASE_URL}/jobs")
            response.raise_for_status()
            
            jobs_data = response.json()
            print(f"✅ Found {len(jobs_data['jobs'])} jobs:")
            
            for job in jobs_data['jobs']:
                print(f"   - {job['job_id']}: {job['status']} ({job['provider']})")
                
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to list jobs: {e}")
            print(f"   Response: {e.response.text}")
        except Exception as e:
            print(f"❌ Error listing jobs: {e}")
        
        # 4. Wait a bit and check status again
        print(f"\n4. Waiting 10 seconds and checking status again...")
        await asyncio.sleep(10)
        
        try:
            response = await client.get(f"{BASE_URL}/jobs/{job_id}")
            response.raise_for_status()
            
            status_data = response.json()
            print(f"✅ Updated job status: {status_data['status']}")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to get updated job status: {e}")
        except Exception as e:
            print(f"❌ Error getting updated job status: {e}")
        
        # 5. Stop the job
        print(f"\n5. Stopping polling job {job_id}...")
        try:
            response = await client.delete(f"{BASE_URL}/jobs/{job_id}")
            response.raise_for_status()
            
            stop_data = response.json()
            print(f"✅ {stop_data['message']}")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to stop job: {e}")
            print(f"   Response: {e.response.text}")
        except Exception as e:
            print(f"❌ Error stopping job: {e}")
        
        # 6. Verify job is stopped
        print(f"\n6. Verifying job is stopped...")
        try:
            response = await client.get(f"{BASE_URL}/jobs/{job_id}")
            response.raise_for_status()
            
            status_data = response.json()
            print(f"✅ Final job status: {status_data['status']}")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to get final job status: {e}")
        except Exception as e:
            print(f"❌ Error getting final job status: {e}")
        
        print(f"\n🎉 Polling job test completed!")

async def test_error_cases():
    """Test error cases and validation"""
    
    async with httpx.AsyncClient() as client:
        print("\n🧪 Testing Error Cases")
        print("=" * 30)
        
        # Test 1: Invalid symbols (empty list)
        print("\n1. Testing empty symbols list...")
        try:
            response = await client.post(
                f"{BASE_URL}/prices/poll",
                json={"symbols": [], "interval": 60, "provider": "alpha_vantage"}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: Invalid interval (too short)
        print("\n2. Testing invalid interval...")
        try:
            response = await client.post(
                f"{BASE_URL}/prices/poll",
                json={"symbols": ["AAPL"], "interval": 10, "provider": "alpha_vantage"}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: Invalid provider
        print("\n3. Testing invalid provider...")
        try:
            response = await client.post(
                f"{BASE_URL}/prices/poll",
                json={"symbols": ["AAPL"], "interval": 60, "provider": "invalid_provider"}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 4: Non-existent job
        print("\n4. Testing non-existent job...")
        try:
            response = await client.get(f"{BASE_URL}/jobs/non-existent-id")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Polling Job Tests")
    print("Make sure the FastAPI server is running on http://app:8000")
    print("=" * 60)
    
    # Test basic functionality
    await test_polling_job()
    
    # Test error cases
    await test_error_cases()
    
    print("\n✨ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 