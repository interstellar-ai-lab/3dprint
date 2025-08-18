#!/usr/bin/env python3
"""
Test script to find user IDs from Supabase
"""

import os
import sys
from supabase import create_client, Client

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the supabase client from app.py
try:
    from app import supabase_client
    print("✅ Using existing Supabase client from app.py")
except ImportError:
    print("❌ Could not import supabase_client from app.py")
    print("Please run this script from the webapp directory")
    sys.exit(1)

def find_user_by_email(email):
    """Find user by email"""
    try:
        user_response = supabase_client.auth.admin.list_users()
        for user in user_response:
            if user.email == email:
                return user
        return None
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return None

def list_all_users():
    """List all users"""
    try:
        user_response = supabase_client.auth.admin.list_users()
        users = user_response  # The response is already a list
        print(f"\n📋 Found {len(users)} users:")
        print("-" * 80)
        for i, user in enumerate(users, 1):
            print(f"{i}. ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Created: {user.created_at}")
            print(f"   Last Sign In: {user.last_sign_in_at}")
            print("-" * 80)
        return users
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []

def main():
    print("🔍 Supabase User Finder")
    print("=" * 50)
    
    # List all users
    users = list_all_users()
    
    if not users:
        print("❌ No users found or error occurred")
        return
    
    # Try to find specific user
    test_email = "zeyupan1995@gmail.com"
    print(f"\n🔍 Looking for user: {test_email}")
    user = find_user_by_email(test_email)
    
    if user:
        print(f"✅ Found user:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Created: {user.created_at}")
        
        # Test wallet crediting
        print(f"\n🧪 Testing wallet crediting for user_id: {user.id}")
        test_credit(user.id)
    else:
        print(f"❌ User not found: {test_email}")
        print("\n💡 To create this user:")
        print("1. Sign up in your app with this email")
        print("2. Or create manually in Supabase Dashboard")

def test_credit(user_id):
    """Test crediting wallet"""
    try:
        import requests
        
        # Test the new endpoint
        response = requests.post(
            'http://localhost:8001/api/wallet/credit-by-user-id',
            json={
                'user_id': user_id,
                'amount': 5.00,
                'payment_reference': 'test_payment_123'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Wallet credited successfully!")
            print(f"   New balance: ${data['new_balance']}")
        else:
            print(f"❌ Failed to credit wallet: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing credit: {e}")

if __name__ == "__main__":
    main()
