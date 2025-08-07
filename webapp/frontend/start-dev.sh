#!/bin/bash

echo "🚀 Starting 3D Generation Frontend Development Server..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies. Please check the error messages above."
        exit 1
    fi
    echo "✅ Dependencies installed successfully!"
else
    echo "✅ Dependencies already installed."
fi

echo "🌐 Starting development server..."
echo "📱 The app will be available at http://localhost:8000"
echo "🔗 Make sure your Flask backend is running on http://localhost:8001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start
