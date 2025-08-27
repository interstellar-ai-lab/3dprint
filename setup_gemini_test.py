#!/usr/bin/env python3
"""
Setup script for Gemini Image Editing Test Suite.
This script helps install dependencies and configure the environment.
"""

import os
import sys
import subprocess
import platform

def print_header():
    """Print a formatted header."""
    print("🚀 Gemini Image Editing Test Suite Setup")
    print("=" * 50)

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    packages = [
        "google-generativeai>=0.8.0",
        "Pillow>=10.4.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "python-dotenv>=1.0.0"
    ]
    
    failed_packages = []
    
    for package in packages:
        print(f"Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
        else:
            print(f"❌ Failed to install {package}")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️  Some packages failed to install: {', '.join(failed_packages)}")
        print("You may need to install them manually or check your pip configuration.")
        return False
    
    print("\n✅ All dependencies installed successfully!")
    return True

def check_api_key():
    """Check if Gemini API key is configured."""
    print("\n🔑 Checking API key configuration...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("✅ GEMINI_API_KEY environment variable found")
        print(f"   Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
        return True
    else:
        print("❌ GEMINI_API_KEY environment variable not found")
        return False

def setup_api_key():
    """Help user set up the API key."""
    print("\n🔧 Setting up API key...")
    
    print("To use the Gemini API, you need to:")
    print("1. Visit https://makersuite.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Set it as an environment variable")
    
    # Try to create .env file
    env_file = ".env"
    if not os.path.exists(env_file):
        try:
            with open(env_file, "w") as f:
                f.write("# Gemini API Key\n")
                f.write("# Replace 'your_api_key_here' with your actual API key\n")
                f.write("GEMINI_API_KEY=your_api_key_here\n")
            print(f"✅ Created {env_file} template file")
            print(f"   Edit {env_file} and add your actual API key")
        except Exception as e:
            print(f"❌ Could not create {env_file}: {e}")
    
    # Show platform-specific commands
    system = platform.system().lower()
    if system == "windows":
        print("\nOn Windows, run:")
        print("set GEMINI_API_KEY=your_api_key_here")
    else:
        print("\nOn macOS/Linux, run:")
        print("export GEMINI_API_KEY='your_api_key_here'")
        print("\nOr add to your shell profile (~/.bashrc, ~/.zshrc, etc.)")

def test_imports():
    """Test if all required modules can be imported."""
    print("\n🧪 Testing imports...")
    
    modules = [
        ("google.generativeai", "genai"),
        ("PIL", "PIL"),
        ("pytest", "pytest"),
        ("dotenv", "dotenv")
    ]
    
    failed_imports = []
    
    for module_name, import_name in modules:
        try:
            __import__(import_name)
            print(f"✅ {module_name} imported successfully")
        except ImportError as e:
            print(f"❌ {module_name} import failed: {e}")
            failed_imports.append(module_name)
    
    if failed_imports:
        print(f"\n⚠️  Some modules failed to import: {', '.join(failed_imports)}")
        return False
    
    print("\n✅ All modules imported successfully!")
    return True

def run_quick_test():
    """Run a quick test to verify everything works."""
    print("\n🚀 Running quick test...")
    
    try:
        # Try to run the test file
        result = subprocess.run([
            sys.executable, "test_gemini_image_edit.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Quick test passed!")
            return True
        else:
            print("❌ Quick test failed")
            print("Output:", result.stdout)
            print("Errors:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Quick test timed out")
        return False
    except Exception as e:
        print(f"❌ Quick test failed with error: {e}")
        return False

def main():
    """Main setup function."""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  Setup completed with warnings. Some dependencies may need manual installation.")
    
    # Check API key
    if not check_api_key():
        setup_api_key()
    
    # Test imports
    if not test_imports():
        print("\n⚠️  Some modules could not be imported. Check the installation.")
    
    # Run quick test
    if run_quick_test():
        print("\n🎉 Setup completed successfully!")
        print("\nYou can now run:")
        print("  python gemini_image_edit_demo.py    # Run the demo")
        print("  python test_gemini_image_edit.py    # Run the tests")
    else:
        print("\n⚠️  Setup completed but quick test failed.")
        print("Check the error messages above and try running the tests manually.")
    
    print("\n📚 For more information, see README_GEMINI_TEST.md")

if __name__ == "__main__":
    main()
