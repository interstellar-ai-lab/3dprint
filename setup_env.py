#!/usr/bin/env python3
"""
Setup script to create .env file from env.local
This script helps you set up your local environment variables.
"""

import os
import shutil
from pathlib import Path

def setup_env():
    """Create .env file from env.local if it doesn't exist"""
    
    env_local = Path("env.local")
    env_file = Path(".env")
    
    if not env_local.exists():
        print("❌ env.local file not found!")
        print("Please create env.local with your API keys first.")
        return False
    
    if env_file.exists():
        print("✅ .env file already exists!")
        return True
    
    try:
        # Copy env.local to .env
        shutil.copy2(env_local, env_file)
        print("✅ Successfully created .env file from env.local")
        print("🔒 Your API keys are now stored locally (not in git)")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def check_env_setup():
    """Check if environment is properly set up"""
    
    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  .env file not found")
        return False
    
    # Check if OPENAI_API_KEY is set
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found in .env file")
        return False
    
    print("✅ Environment is properly set up!")
    print(f"🔑 API Key found: {api_key[:20]}...")
    return True

if __name__ == "__main__":
    print("🚀 Setting up local environment...")
    
    if setup_env():
        check_env_setup()
    else:
        print("\n📝 Manual setup required:")
        print("1. Copy env.local to .env: cp env.local .env")
        print("2. Edit .env and add your actual API keys")
        print("3. Run this script again to verify setup") 