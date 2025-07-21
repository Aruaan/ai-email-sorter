#!/usr/bin/env python3
"""
Test script to verify session persistence behavior
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_session_persistence():
    """Test that sessions are reused for the same email"""
    
    print("=== Testing Session Persistence ===")
    
    # First, check current sessions
    print("\n1. Current sessions before test:")
    try:
        response = requests.get(f"{BASE_URL}/dev/debug/sessions")
        if response.status_code == 200:
            sessions = response.json()
            print(f"Found {len(sessions['sessions'])} sessions:")
            for session in sessions['sessions']:
                print(f"  - Session {session['session_id'][:8]}... (Primary: {session['primary_account']})")
                print(f"    Categories: {[cat['name'] for cat in session['categories']]}")
        else:
            print(f"Error getting sessions: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n2. To test session persistence:")
    print("   - Log in with the same email multiple times")
    print("   - Check that the same session ID is reused")
    print("   - Verify only one 'Uncategorized' category exists per session")
    print("   - Use the debug endpoint: GET /dev/debug/sessions")

if __name__ == "__main__":
    test_session_persistence() 