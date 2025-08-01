#!/bin/bash

echo "🚀 Preparing for Vercel deployment..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Committing changes..."
    git add .
    git commit -m "Prepare for Vercel deployment"
fi

# Push to remote if it exists
if git remote get-url origin > /dev/null 2>&1; then
    echo "📤 Pushing to remote repository..."
    git push origin main
fi

echo "✅ Code prepared for deployment!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://vercel.com"
echo "2. Click 'New Project'"
echo "3. Import your GitHub repository"
echo "4. Set environment variables:"
echo "   - OPENAI_API_KEY"
echo "   - CLAUDE_API_KEY"
echo "   - DEEPSEEK_API_KEY (optional)"
echo "   - QWEN_API_KEY (optional)"
echo "5. Click 'Deploy'"
echo ""
echo "🌐 Your app will be available at the URL provided by Vercel" 