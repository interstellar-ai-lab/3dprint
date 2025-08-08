#!/bin/bash

echo "🔧 Installing GCP Storage dependencies for the webapp..."

# Navigate to webapp directory
cd webapp

# Install the updated requirements
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Test GCP import
echo "🧪 Testing GCP import..."
python3 -c "
try:
    from google.cloud import storage
    from google.oauth2 import credentials as user_credentials
    from google.oauth2 import service_account
    print('✅ GCP libraries imported successfully')
except ImportError as e:
    print(f'❌ GCP import failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ GCP libraries are working correctly!"
else
    echo "❌ GCP libraries test failed"
    exit 1
fi

echo ""
echo "🎉 GCP Storage setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run the webapp: cd webapp && python3 app.py"
echo "2. Test the integration: python3 test_gcp_webapp_integration.py"
echo "3. Generate images through the webapp - they will be uploaded to gs://vicino.ai/generated_images/"
