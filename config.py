"""
Configuration management for the Twitter to Telegram Bot
"""

import os
from typing import Optional

class Config:
    """Configuration class to manage all bot settings"""
    
    def __init__(self):
        # Twitter API Configuration
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "AAAAAAAAAAAAAAAAAAAAAL6I3gEAAAAAOVMgbd4FLeqjVmygJ3jmWuHPZnQ%3Dfrt68vvp6XnQTpUcUZqmitdIfhbXwLynCzivQ15qhIAFzQZcPx")
        self.twitter_username = os.getenv("TWITTER_USERNAME", "CricCrazyJohns")
        
        # Telegram Bot Configuration
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8269663176:AAGQvRcN4dUzkmAPBCufwAqBliB43qxX0oI")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "@CricketNewsSkull")
        
        # Polling Configuration  
        self.polling_interval = int(os.getenv("POLLING_INTERVAL", "30"))  # seconds (increased to respect rate limits)
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("RETRY_DELAY", "10"))  # seconds
        
        # Twitter API URLs
        self.user_lookup_url = f"https://api.twitter.com/2/users/by/username/{self.twitter_username}"
        self.tweets_url_template = "https://api.twitter.com/2/users/{user_id}/tweets?exclude=retweets,replies&tweet.fields=created_at,referenced_tweets&expansions=attachments.media_keys&media.fields=type,url,variants"
        
        # Headers for Twitter API
        self.twitter_headers = {"Authorization": f"Bearer {self.twitter_bearer_token}"}
    
    def validate(self) -> bool:
        """Validate that all required configuration is present"""
        required_vars = [
            ("TWITTER_BEARER_TOKEN", self.twitter_bearer_token),
            ("TWITTER_USERNAME", self.twitter_username),
            ("TELEGRAM_BOT_TOKEN", self.telegram_bot_token),
            ("TELEGRAM_CHAT_ID", self.telegram_chat_id)
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value or var_value.strip() == "":
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    def get_twitter_user_id_url(self) -> str:
        """Get the URL for Twitter user lookup"""
        return self.user_lookup_url
    
    def get_twitter_tweets_url(self, user_id: str) -> str:
        """Get the URL for fetching user tweets"""
        return self.tweets_url_template.format(user_id=user_id)
