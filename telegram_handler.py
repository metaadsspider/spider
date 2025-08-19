"""
Telegram bot handler and message sending functionality
"""

import asyncio
import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TelegramBotHandler:
    """Handles Telegram bot operations and message sending"""
    
    def __init__(self, config):
        self.config = config
        self.bot_running = False
        
        # Telegram API endpoints
        self.send_message_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
        self.send_photo_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendPhoto"
        self.send_video_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendVideo"
        self.send_animation_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendAnimation"
        self.send_media_group_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMediaGroup"
        self.get_updates_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/getUpdates"
        
        self.offset = 0
    
    async def start(self):
        """Start the Telegram bot"""
        try:
            self.bot_running = True
            logger.info("📱 Telegram bot handler started")
            
            # Send startup notification to the channel
            await self._send_startup_notification()
            
            # Start polling for updates
            await self._start_polling()
            
        except Exception as e:
            logger.error(f"❌ Error starting Telegram bot: {e}")
            raise
    
    async def _send_startup_notification(self):
        """Send a notification that the bot has started"""
        message = (
            "🤖 <b>Twitter to Telegram Bot Started!</b>\n\n"
            f"✅ Monitoring: @{self.config.twitter_username}\n"
            f"📱 Forwarding to: {self.config.telegram_chat_id}\n"
            f"⏱️ Polling interval: {self.config.polling_interval} seconds\n\n"
            "The bot is now actively monitoring for new tweets!"
        )
        
        try:
            await self.send_message(message)
            logger.info("✅ Startup notification sent to Telegram")
        except Exception as e:
            logger.error(f"❌ Failed to send startup notification: {e}")
    
    async def _start_polling(self):
        """Start polling for Telegram updates"""
        while self.bot_running:
            try:
                response = requests.get(
                    self.get_updates_url,
                    params={"offset": self.offset, "timeout": 10},
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok") and data.get("result"):
                        await self._process_updates(data["result"])
                        
                await asyncio.sleep(1)  # Small delay between polls
                
            except Exception as e:
                logger.error(f"❌ Error in polling loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_updates(self, updates):
        """Process incoming Telegram updates"""
        for update in updates:
            self.offset = update["update_id"] + 1
            
            if "message" in update:
                message = update["message"]
                text = message.get("text", "")
                chat_id = message["chat"]["id"]
                user = message.get("from", {})
                
                if text.startswith("/"):
                    await self._handle_command(text, chat_id, user)
    
    async def _handle_command(self, command: str, chat_id: int, user: Dict):
        """Handle bot commands"""
        username = user.get("username", user.get("id", "unknown"))
        logger.info(f"📱 Command '{command}' received from user: {username}")
        
        if command == "/start":
            await self._send_start_response(chat_id, user)
        elif command == "/status":
            await self._send_status_response(chat_id)
        elif command == "/help":
            await self._send_help_response(chat_id)
    
    async def _send_start_response(self, chat_id: int, user: Dict):
        """Send response to /start command"""
        first_name = user.get("first_name", "User")
        welcome_message = (
            f"👋 Hello {first_name}!\n\n"
            "🤖 <b>Twitter to Telegram Bot is Active!</b>\n\n"
            f"🐦 Monitoring: @{self.config.twitter_username}\n"
            f"📢 Forwarding to: {self.config.telegram_chat_id}\n"
            f"⚡ Response time: ≤10 seconds\n\n"
            "📋 <b>Available Commands:</b>\n"
            "/start - Show this welcome message\n"
            "/status - Check bot status\n"
            "/help - Get help information\n\n"
            "✅ <b>Bot is working perfectly!</b>\n"
            "New original tweets will be forwarded automatically."
        )
        
        await self._send_direct_message(chat_id, welcome_message)
    
    async def _send_status_response(self, chat_id: int):
        """Send response to /status command"""
        status_message = (
            "📊 <b>Bot Status Report</b>\n\n"
            f"🟢 Status: <b>Active & Running</b>\n"
            f"🐦 Monitoring: @{self.config.twitter_username}\n"
            f"📢 Target Channel: {self.config.telegram_chat_id}\n"
            f"⏱️ Check Interval: {self.config.polling_interval}s\n"
            f"🔄 Max Retries: {self.config.max_retries}\n\n"
            "✅ All systems operational!"
        )
        
        await self._send_direct_message(chat_id, status_message)
    
    async def _send_help_response(self, chat_id: int):
        """Send response to /help command"""
        help_message = (
            "❓ <b>Help - Twitter to Telegram Bot</b>\n\n"
            "🎯 <b>Purpose:</b>\n"
            "This bot monitors Twitter accounts and forwards original tweets to Telegram channels in real-time.\n\n"
            "⚡ <b>Features:</b>\n"
            "• Forwards tweets within 10 seconds\n"
            "• Supports text, images, videos, GIFs\n"
            "• Excludes retweets and replies\n"
            "• Handles multiple media attachments\n"
            "• Real-time status monitoring\n\n"
            "🔧 <b>Commands:</b>\n"
            "/start - Welcome message & status\n"
            "/status - Check current bot status\n"
            "/help - Show this help message\n\n"
            "📞 <b>Support:</b>\n"
            "If you encounter any issues, check the logs or restart the bot."
        )
        
        await self._send_direct_message(chat_id, help_message)
    
    async def _send_direct_message(self, chat_id: int, text: str):
        """Send a direct message to a specific chat"""
        try:
            response = requests.post(
                self.send_message_url,
                data={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to send direct message: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error sending direct message: {e}")
    
    
    async def send_message(self, text: str):
        """Send a text message to the configured channel"""
        try:
            response = requests.post(
                self.send_message_url,
                data={
                    "chat_id": self.config.telegram_chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
    
    async def send_photo(self, photo_url: str, caption: str):
        """Send a photo with caption"""
        try:
            # Download the photo
            photo_response = requests.get(photo_url, timeout=15)
            if photo_response.status_code != 200:
                logger.error(f"❌ Failed to download photo: {photo_url}")
                return
            
            response = requests.post(
                self.send_photo_url,
                data={
                    "chat_id": self.config.telegram_chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
                },
                files={"photo": photo_response.content},
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to send photo: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error sending photo: {e}")
    
    async def send_video(self, video_url: str, caption: str):
        """Send a video with caption"""
        try:
            response = requests.post(
                self.send_video_url,
                data={
                    "chat_id": self.config.telegram_chat_id,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "video": video_url
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to send video: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error sending video: {e}")
    
    async def send_animation(self, animation_url: str, caption: str):
        """Send an animation/GIF with caption"""
        try:
            response = requests.post(
                self.send_animation_url,
                data={
                    "chat_id": self.config.telegram_chat_id,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "animation": animation_url
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to send animation: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error sending animation: {e}")
    
    async def send_media_group(self, photo_urls: List[str], caption: str):
        """Send multiple photos as a media group"""
        try:
            media_group = []
            
            for i, url in enumerate(photo_urls):
                item = {"type": "photo", "media": url}
                if i == 0:  # Add caption to first photo only
                    item["caption"] = caption
                    item["parse_mode"] = "HTML"
                media_group.append(item)
            
            response = requests.post(
                self.send_media_group_url,
                json={
                    "chat_id": self.config.telegram_chat_id,
                    "media": media_group
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to send media group: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error sending media group: {e}")
