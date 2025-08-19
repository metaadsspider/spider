"""
Twitter monitoring functionality
"""

import asyncio
import requests
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from utils import MediaHandler

logger = logging.getLogger(__name__)

class TwitterMonitor:
    """Handles Twitter API monitoring and tweet processing"""
    
    def __init__(self, config, telegram_handler):
        self.config = config
        self.telegram_handler = telegram_handler
        self.user_id: Optional[str] = None
        self.last_seen_id: Optional[str] = None
        self.media_handler = MediaHandler()
        self.retry_count = 0
        
    async def start_monitoring(self):
        """Start monitoring Twitter for new tweets"""
        # First, get the user ID
        if not await self._get_user_id():
            logger.error("❌ Failed to get Twitter user ID. Stopping monitor.")
            return
        
        logger.info(f"✅ Successfully tracking @{self.config.twitter_username} (User ID: {self.user_id})")
        
        # Start the monitoring loop
        await self._monitoring_loop()
    
    async def _get_user_id(self) -> bool:
        """Fetch the Twitter user ID for the configured username"""
        try:
            response = requests.get(
                self.config.get_twitter_user_id_url(),
                headers=self.config.twitter_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get("data", {})
                self.user_id = user_data.get("id")
                
                if self.user_id:
                    return True
                else:
                    logger.error(f"❌ No user ID found for username: {self.config.twitter_username}")
                    return False
            else:
                logger.error(f"❌ Twitter API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error while fetching user ID: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error while fetching user ID: {e}")
            return False
    
    async def _monitoring_loop(self):
        """Main monitoring loop with rate limit handling"""
        consecutive_rate_limits = 0
        
        while True:
            try:
                success = await self._check_new_tweets()
                
                if success:
                    self.retry_count = 0
                    consecutive_rate_limits = 0
                    await asyncio.sleep(self.config.polling_interval)
                else:
                    # Rate limited, increase delay
                    consecutive_rate_limits += 1
                    delay = min(60 * consecutive_rate_limits, 900)  # Max 15 min delay
                    logger.info(f"⏳ Rate limited. Waiting {delay} seconds before next attempt...")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                self.retry_count += 1
                logger.error(f"⚠️ Error in monitoring loop (attempt {self.retry_count}): {e}")
                
                if self.retry_count >= self.config.max_retries:
                    logger.error(f"❌ Max retries ({self.config.max_retries}) reached. Resetting retry count.")
                    self.retry_count = 0
                
                await asyncio.sleep(self.config.retry_delay)
    
    async def _check_new_tweets(self) -> bool:
        """Check for new tweets and process them. Returns True if successful, False if rate limited."""
        try:
            tweets_url = self.config.get_twitter_tweets_url(self.user_id)
            response = requests.get(
                tweets_url,
                headers=self.config.twitter_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                await self._process_tweets(data)
                return True
            elif response.status_code == 429:
                # Rate limited - don't log error, just return False
                return False
            else:
                logger.error(f"❌ Twitter API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error while checking tweets: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error while checking tweets: {e}")
            return False
    
    async def _process_tweets(self, data: Dict[str, Any]):
        """Process the tweet data from Twitter API"""
        if "data" not in data or not data["data"]:
            return
        
        # Get the latest tweet
        tweet = data["data"][0]
        tweet_id = tweet["id"]
        
        # Skip if we've already seen this tweet
        if tweet_id == self.last_seen_id:
            return
        
        # Skip if this is a retweet or reply (additional check)
        if self._is_retweet_or_reply(tweet):
            logger.info(f"🔄 Skipping retweet/reply: {tweet_id}")
            self.last_seen_id = tweet_id
            return
        
        logger.info(f"📝 Processing new tweet: {tweet_id}")
        
        try:
            # Process and forward the tweet
            await self._forward_tweet(tweet, data.get("includes", {}))
            self.last_seen_id = tweet_id
            logger.info(f"✅ Successfully forwarded tweet: {tweet_id}")
            
        except Exception as e:
            logger.error(f"❌ Error forwarding tweet {tweet_id}: {e}")
    
    def _is_retweet_or_reply(self, tweet: Dict[str, Any]) -> bool:
        """Check if tweet is a retweet or reply"""
        # Check for referenced tweets (retweets, quotes, replies)
        referenced_tweets = tweet.get("referenced_tweets", [])
        if referenced_tweets:
            return True
        
        # Check if tweet text starts with @mention (likely a reply)
        text = tweet.get("text", "")
        if text.startswith("@"):
            return True
        
        return False
    
    def _remove_twitter_urls(self, text: str) -> str:
        """Remove Twitter URLs from text"""
        import re
        
        # Remove t.co URLs (Twitter's URL shortener)
        text = re.sub(r'https://t\.co/\S+', '', text)
        
        # Remove other common Twitter URL patterns
        text = re.sub(r'https://twitter\.com/\S+', '', text)
        text = re.sub(r'https://x\.com/\S+', '', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _forward_tweet(self, tweet: Dict[str, Any], includes: Dict[str, Any]):
        """Forward tweet to Telegram"""
        text = tweet.get("text", "")
        
        # Remove Twitter URLs from text
        clean_text = self._remove_twitter_urls(text)
        formatted_text = f"<b>{clean_text}</b>"
        
        # Handle media attachments
        media_keys = tweet.get("attachments", {}).get("media_keys", [])
        media_items = includes.get("media", [])
        
        if media_keys and media_items:
            await self._forward_tweet_with_media(formatted_text, media_keys, media_items)
        else:
            await self._forward_text_only(formatted_text)
    
    async def _forward_tweet_with_media(self, text: str, media_keys: List[str], media_items: List[Dict]):
        """Forward tweet with media attachments"""
        # Categorize media
        photos = []
        videos = []
        gifs = []
        
        for media in media_items:
            if media["media_key"] in media_keys:
                media_type = media["type"]
                if media_type == "photo":
                    photos.append(media["url"])
                elif media_type == "video":
                    videos.append(media)
                elif media_type == "animated_gif":
                    gifs.append(media)
        
        # Handle different media types
        if len(photos) > 1:
            await self.telegram_handler.send_media_group(photos, text)
        elif len(photos) == 1:
            await self.telegram_handler.send_photo(photos[0], text)
        elif videos:
            video_url = self.media_handler.get_best_video_url(videos[0])
            if video_url:
                await self.telegram_handler.send_video(video_url, text)
        elif gifs:
            gif_url = self.media_handler.get_gif_url(gifs[0])
            if gif_url:
                await self.telegram_handler.send_animation(gif_url, text)
        else:
            await self._forward_text_only(text)
    
    async def _forward_text_only(self, text: str):
        """Forward text-only tweet"""
        await self.telegram_handler.send_message(text)
