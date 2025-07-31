#!/usr/bin/env python3
"""
Check available models and API key status
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import client

def check_models():
    """Check what models are available"""
    print("🔍 Checking Available Models...")
    print("=" * 50)
    
    try:
        # List available models
        models = client.models.list()
        
        print("📋 Available Models:")
        for model in models.data:
            print(f"  - {model.id}")
            
        # Check for specific models we need
        model_ids = [model.id for model in models.data]
        
        print("\n🎯 Checking Required Models:")
        print(f"  DALL-E 3: {'✅ Available' if 'dall-e-3' in model_ids else '❌ Not Available'}")
        print(f"  GPT-4o: {'✅ Available' if 'gpt-4o' in model_ids else '❌ Not Available'}")
        print(f"  GPT-4 Image: {'✅ Available' if 'gpt-image-1' in model_ids else '❌ Not Available'}")
        print(f"  GPT-4o-mini: {'✅ Available' if 'gpt-4o-mini' in model_ids else '❌ Not Available'}")
        
        # Check for any GPT-4 variants
        gpt4_models = [m for m in model_ids if 'gpt-4' in m]
        print(f"\n🤖 GPT-4 Variants Available: {gpt4_models}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking models: {str(e)}")
        return False

def check_api_key():
    """Check if API key is valid"""
    print("\n🔑 Checking API Key...")
    print("=" * 50)
    
    try:
        # Try a simple API call to test the key
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use a cheaper model for testing
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("✅ API key is valid!")
        print(f"✅ Test response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ API key error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🧪 Model and API Key Checker")
    print("=" * 50)
    
    # Check API key first
    api_key_ok = check_api_key()
    
    if api_key_ok:
        # Check available models
        models_ok = check_models()
        
        print("\n📊 Summary:")
        print("=" * 50)
        print(f"API Key: {'✅ Valid' if api_key_ok else '❌ Invalid'}")
        print(f"Models: {'✅ Available' if models_ok else '❌ Error'}")
        
        if api_key_ok and models_ok:
            print("\n🎉 Your setup looks good! Both DALL-E 3 and GPT-4o should work.")
        else:
            print("\n⚠️  There are issues with your setup. Check the errors above.")
    else:
        print("\n❌ Cannot check models without a valid API key.")

if __name__ == "__main__":
    main() 