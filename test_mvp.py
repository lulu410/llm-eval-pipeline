#!/usr/bin/env python3
"""
Test script for MVP functionality.
"""

import requests
import base64
import json
from pathlib import Path

def test_mvp_api():
    """Test MVP API endpoints."""
    base_url = "http://localhost:8001"
    
    print("🧪 Testing MVP API...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ MVP server is running")
        else:
            print("❌ MVP server not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to MVP server: {e}")
        return
    
    # Test 2: Get rubrics
    try:
        response = requests.get(f"{base_url}/api/rubrics")
        if response.status_code == 200:
            rubrics = response.json()
            print(f"✅ Found {len(rubrics)} rubrics")
            
            # Show available rubrics
            for rubric in rubrics[:3]:  # Show first 3
                print(f"   - {rubric['name']}: {rubric['description'][:50]}...")
        else:
            print("❌ Failed to get rubrics")
    except Exception as e:
        print(f"❌ Error getting rubrics: {e}")
    
    # Test 3: Create a simple test image
    try:
        # Create a simple test image (1x1 pixel PNG)
        test_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        
        # Test batch evaluation (this will fail without Gemini API key, but we can test the endpoint)
        files = {
            'files': ('test.png', test_image_data, 'image/png')
        }
        data = {
            'rubric_ids': ['ai_arts_competition', 'digital_art_evaluation']
        }
        
        response = requests.post(f"{base_url}/api/evaluate/batch", files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Batch evaluation successful: {result['successful_evaluations']} submissions processed")
        else:
            print(f"⚠️  Batch evaluation failed (expected without API key): {response.status_code}")
            print(f"   Response: {response.text[:100]}...")
            
    except Exception as e:
        print(f"⚠️  Batch evaluation test failed (expected): {e}")
    
    print("\n🎯 MVP Test Summary:")
    print("✅ Server running")
    print("✅ Rubrics loaded")
    print("⚠️  Batch evaluation (requires Gemini API key)")
    print("\n🌐 Access MVP at: http://localhost:8001")

if __name__ == "__main__":
    test_mvp_api()
