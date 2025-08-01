# Vercel Deployment Guide

This guide will help you deploy your multi-agent 3D generation application to Vercel.

## Prerequisites

- GitHub account
- Vercel account (free at [vercel.com](https://vercel.com))
- Your API keys ready

## Quick Deployment

### Option 1: Automated Script (Recommended)

```bash
# Run the deployment script
./deploy_vercel.sh
```

This script will:
- Check git status
- Commit any changes
- Push to GitHub
- Provide next steps

### Option 2: Manual Deployment

1. **Prepare your code**:
```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

2. **Deploy via Vercel Dashboard**:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Configure settings (see below)
   - Deploy

## Configuration

### Environment Variables

Set these in your Vercel project settings:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `CLAUDE_API_KEY` | Your Claude API key | Yes |
| `DEEPSEEK_API_KEY` | Your DeepSeek API key | No |
| `QWEN_API_KEY` | Your Qwen API key | No |

### Project Settings

- **Framework Preset**: Other
- **Root Directory**: `./` (default)
- **Build Command**: Leave empty
- **Output Directory**: Leave empty
- **Install Command**: Leave empty

## File Structure

Your project should have this structure for Vercel:

```
openai-agents-python/
├── vercel.json              # Vercel configuration
├── webapp/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── static/              # Static files
├── multiagent.py            # Main application logic
└── deploy_vercel.sh         # Deployment script
```

## Troubleshooting

### SSL/TLS Errors

If you encounter SSL errors with Vercel CLI:

1. **Use Dashboard Deployment**: This is more reliable
2. **Clear Vercel Cache**: `rm -rf ~/.vercel`
3. **Update CLI**: `npm install -g vercel@latest`
4. **Try Different Network**: Use mobile hotspot or different WiFi

### Build Errors

1. **Check Requirements**: Ensure all dependencies are in `webapp/requirements.txt`
2. **Check Python Version**: Vercel uses Python 3.9 by default
3. **Check File Paths**: Ensure `vercel.json` points to correct files

### Runtime Errors

1. **Check Environment Variables**: Ensure all API keys are set
2. **Check Logs**: Use Vercel dashboard to view function logs
3. **Test Locally**: Run `python webapp/main.py` to test locally

## Post-Deployment

1. **Test Your App**: Visit the provided URL
2. **Check Function Logs**: Monitor for any errors
3. **Set Up Custom Domain**: Optional - configure in Vercel dashboard

## Support

If you encounter issues:

1. Check Vercel documentation: [vercel.com/docs](https://vercel.com/docs)
2. Check function logs in Vercel dashboard
3. Test locally first: `python webapp/main.py`

## Security Notes

- Never commit API keys to git
- Use environment variables for all sensitive data
- Regularly rotate your API keys
- Monitor usage and costs 