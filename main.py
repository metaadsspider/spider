#!/usr/bin/env python3
"""
Main entry point for the Twitter to Telegram Bot
"""

import asyncio
import logging
import os
from telegram_handler import TelegramBotHandler
from twitter_monitor import TwitterMonitor
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to run the bot with auto-restart capability"""
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        try:
            # Initialize configuration
            config = Config()
            
            # Validate configuration
            if not config.validate():
                logger.error("Configuration validation failed. Please check your environment variables.")
                return
            
            logger.info(f"🚀 Starting Twitter to Telegram Bot (attempt {retry_count + 1})...")
            
            # Initialize components
            telegram_handler = TelegramBotHandler(config)
            twitter_monitor = TwitterMonitor(config, telegram_handler)
            
            # Start Telegram bot
            logger.info("📱 Starting Telegram bot...")
            bot_task = asyncio.create_task(telegram_handler.start())
            
            # Start Twitter monitoring
            logger.info("🐦 Starting Twitter monitoring...")
            monitor_task = asyncio.create_task(twitter_monitor.start_monitoring())
            
            # Wait for both tasks
            await asyncio.gather(bot_task, monitor_task)
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Fatal error (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                wait_time = min(30 * retry_count, 300)  # Max 5 minute wait
                logger.info(f"🔄 Restarting in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("❌ Max restart attempts reached. Bot stopped.")
                break

if __name__ == "__main__":
    asyncio.run(main())