#!/usr/bin/env python3
"""
Test script for database session management in polling jobs
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/v1"
TEST_SYMBOLS = ["AAPL", "MSFT"]
TEST_INTERVAL = 30  # 30 seconds for faster testing
TEST_PROVIDER = "alpha_vantage"

async def test_session_management():
    """Test that polling jobs work correctly with proper session management"""
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Database Session Management")
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
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to create polling job: {e}")
            print(f"   Response: {e.response.text}")
            return
        except Exception as e:
            print(f"❌ Error creating polling job: {e}")
            return
        
        # 2. Check job status immediately
        print(f"\n2. Checking job status immediately...")
        try:
            response = await client.get(f"{BASE_URL}/jobs/{job_id}")
            response.raise_for_status()
            
            status_data = response.json()
            print(f"✅ Job status: {status_data['status']}")
            
            # Should be running or accepted
            if status_data['status'] in ['accepted', 'running']:
                print(f"   ✅ Job is in expected state")
            else:
                print(f"   ⚠️  Unexpected job state: {status_data['status']}")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to get job status: {e}")
        except Exception as e:
            print(f"❌ Error getting job status: {e}")
        
        # 3. Wait for a few polling cycles
        print(f"\n3. Waiting for polling cycles (15 seconds)...")
        await asyncio.sleep(15)
        
        # 4. Check job status again
        print(f"\n4. Checking job status after polling cycles...")
        try:
            response = await client.get(f"{BASE_URL}/jobs/{job_id}")
            response.raise_for_status()
            
            status_data = response.json()
            print(f"✅ Job status after polling: {status_data['status']}")
            
            # Should still be running
            if status_data['status'] == 'running':
                print(f"   ✅ Job is still running (session management working)")
            else:
                print(f"   ⚠️  Job status changed to: {status_data['status']}")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to get job status: {e}")
        except Exception as e:
            print(f"❌ Error getting job status: {e}")
        
        # 5. Stop the job
        print(f"\n5. Stopping polling job...")
        try:
            response = await client.delete(f"{BASE_URL}/jobs/{job_id}")
            response.raise_for_status()
            
            stop_data = response.json()
            print(f"✅ {stop_data['message']}")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to stop job: {e}")
        except Exception as e:
            print(f"❌ Error stopping job: {e}")
        
        # 6. Verify job is stopped
        print(f"\n6. Verifying job is stopped...")
        try:
            response = await client.get(f"{BASE_URL}/jobs/{job_id}")
            response.raise_for_status()
            
            status_data = response.json()
            print(f"✅ Final job status: {status_data['status']}")
            
            if status_data['status'] == 'completed':
                print(f"   ✅ Job completed successfully")
            else:
                print(f"   ⚠️  Job status: {status_data['status']}")
            
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to get final job status: {e}")
        except Exception as e:
            print(f"❌ Error getting final job status: {e}")
        
        print(f"\n🎉 Session management test completed!")

async def test_multiple_jobs():
    """Test multiple concurrent jobs to ensure session isolation"""
    
    async with httpx.AsyncClient() as client:
        print("\n🧪 Testing Multiple Concurrent Jobs")
        print("=" * 40)
        
        # Start multiple jobs
        job_ids = []
        for i in range(2):
            poll_request = {
                "symbols": [f"SYMBOL{i}"],
                "interval": 45,
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
                job_ids.append(job_data["job_id"])
                print(f"✅ Started job {i+1}: {job_data['job_id']}")
                
            except Exception as e:
                print(f"❌ Failed to start job {i+1}: {e}")
        
        if job_ids:
            # Wait a bit
            await asyncio.sleep(10)
            
            # Check all jobs
            for i, job_id in enumerate(job_ids):
                try:
                    response = await client.get(f"{BASE_URL}/jobs/{job_id}")
                    response.raise_for_status()
                    
                    status_data = response.json()
                    print(f"✅ Job {i+1} status: {status_data['status']}")
                    
                except Exception as e:
                    print(f"❌ Failed to check job {i+1}: {e}")
            
            # Stop all jobs
            for i, job_id in enumerate(job_ids):
                try:
                    response = await client.delete(f"{BASE_URL}/jobs/{job_id}")
                    response.raise_for_status()
                    print(f"✅ Stopped job {i+1}")
                    
                except Exception as e:
                    print(f"❌ Failed to stop job {i+1}: {e}")

async def main():
    """Main test function"""
    print("🚀 Testing Database Session Management")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("=" * 60)
    
    # Test basic session management
    await test_session_management()
    
    # Test multiple concurrent jobs
    await test_multiple_jobs()
    
    print("\n✨ All session management tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 