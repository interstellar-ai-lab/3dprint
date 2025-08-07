#!/bin/bash

echo "🚀 Setting up 3D Generation Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
    echo ""
    echo "🎯 Next steps:"
    echo "1. Make sure your Flask backend is running on http://localhost:5000"
    echo "2. Start the React development server:"
    echo "   npm start"
    echo ""
    echo "🌐 The frontend will be available at http://localhost:3000"
else
    echo "❌ Failed to install dependencies. Please check the error messages above."
    exit 1
fi
