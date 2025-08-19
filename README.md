# Twitter to Telegram Bot

Monitor Twitter accounts and automatically forward original tweets to Telegram channels.

## Quick Deploy to Railway (Free)

1. **Create GitHub Repository**
   - Upload all files from this folder to a new GitHub repo

2. **Deploy to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Add environment variables (see below)
   - Deploy

3. **Environment Variables**
   Add these in Railway dashboard:
   ```
   TWITTER_BEARER_TOKEN=your_twitter_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=@YourChannelName
   TWITTER_USERNAME=CricCrazyJohns
   ```

## Getting API Keys

**Twitter API:**
1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Create app and generate Bearer Token

**Telegram Bot:**
1. Message [@BotFather](https://t.me/botfather)
2. Use `/newbot` to create your bot
3. Add bot as admin to your channel

## Features

- Monitors Twitter account every 30 seconds
- Forwards only original tweets (no retweets/replies)
- Removes Twitter URLs from messages
- Supports images, videos, GIFs
- Auto-restart on crashes
- Bot commands: /start, /status, /help

## Alternative Deployment

**Docker:**
```bash
docker-compose up -d
```

**Heroku:**
1. Push to GitHub
2. Connect Heroku app to repo
3. Add environment variables
4. Deploy

Your bot will run 24/7 automatically!