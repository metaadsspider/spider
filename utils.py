"""
Utility functions for the Twitter to Telegram Bot
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MediaHandler:
    """Handles media processing and URL extraction"""
    
    @staticmethod
    def get_best_video_url(video_data: Dict[str, Any]) -> Optional[str]:
        """Extract the best quality video URL from Twitter video data"""
        try:
            variants = video_data.get("variants", [])
            if not variants:
                logger.warning("No video variants found")
                return None
            
            # Filter variants that have bitrate (exclude .m3u8 playlists)
            bitrate_variants = [v for v in variants if v.get("bit_rate")]
            
            if bitrate_variants:
                # Get the highest bitrate variant
                best_variant = max(bitrate_variants, key=lambda v: v.get("bit_rate", 0))
                return best_variant.get("url")
            else:
                # Fallback to first variant if no bitrate info
                return variants[0].get("url")
                
        except Exception as e:
            logger.error(f"❌ Error extracting video URL: {e}")
            return None
    
    @staticmethod
    def get_gif_url(gif_data: Dict[str, Any]) -> Optional[str]:
        """Extract GIF URL from Twitter animated GIF data"""
        try:
            variants = gif_data.get("variants", [])
            if variants:
                return variants[0].get("url")
            else:
                logger.warning("No GIF variants found")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error extracting GIF URL: {e}")
            return None

class RateLimiter:
    """Simple rate limiting utility"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests = []
    
    def can_make_request(self) -> bool:
        """Check if a request can be made within rate limits"""
        import time
        current_time = time.time()
        
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if current_time - req_time < self.time_window]
        
        # Check if under limit
        if len(self.requests) < self.max_requests:
            self.requests.append(current_time)
            return True
        
        return False

class TextFormatter:
    """Utility for formatting text for Telegram"""
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ""
        
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    @staticmethod
    def format_tweet_text(text: str, bold: bool = True) -> str:
        """Format tweet text for Telegram"""
        if not text:
            return ""
        
        # Escape HTML first
        formatted_text = TextFormatter.escape_html(text)
        
        # Apply bold formatting if requested
        if bold:
            formatted_text = f"<b>{formatted_text}</b>"
        
        return formatted_text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 1000) -> str:
        """Truncate text if it's too long"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."

class HealthChecker:
    """Simple health checking utility"""
    
    def __init__(self):
        self.last_successful_check = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
    
    def record_success(self):
        """Record a successful operation"""
        import time
        self.last_successful_check = time.time()
        self.consecutive_failures = 0
    
    def record_failure(self):
        """Record a failed operation"""
        self.consecutive_failures += 1
    
    def is_healthy(self) -> bool:
        """Check if the system is considered healthy"""
        return self.consecutive_failures < self.max_consecutive_failures
    
    def get_status(self) -> Dict[str, Any]:
        """Get current health status"""
        import time
        current_time = time.time()
        
        return {
            "healthy": self.is_healthy(),
            "consecutive_failures": self.consecutive_failures,
            "last_successful_check": self.last_successful_check,
            "time_since_last_success": (
                current_time - self.last_successful_check 
                if self.last_successful_check else None
            )
        }
