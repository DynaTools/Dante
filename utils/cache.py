"""
Translation cache implementation to reduce API calls.
"""
import time
from typing import Dict, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationCache:
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Initialize the translation cache.
        
        Args:
            max_size (int): Maximum number of entries to keep in the cache
            ttl (int): Time-to-live for cache entries in seconds (default: 1 hour)
        """
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl  # Time-to-live in seconds
    
    def _generate_key(self, text: str, target_lang: str, source_lang: Optional[str], tone: str) -> str:
        """
        Generate a unique key for the cache based on translation parameters.
        
        Args:
            text (str): Text to translate
            target_lang (str): Target language code
            source_lang (Optional[str]): Source language code
            tone (str): Tone setting (formal, informal, default)
            
        Returns:
            str: A unique key for the cache
        """
        # Normalize source_lang to handle None consistently
        source = source_lang if source_lang else "auto"
        return f"{text}|{source}|{target_lang}|{tone}"
    
    def get_translation(self, text: str, target_lang: str, source_lang: Optional[str] = None, 
                       tone: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get cached translation if available and not expired.
        
        Args:
            text (str): Text to translate
            target_lang (str): Target language code
            source_lang (Optional[str]): Source language code or None for auto-detection
            tone (str): Formal or informal tone
            
        Returns:
            Optional[Dict[str, Any]]: Cached translation result or None if not found
        """
        key = self._generate_key(text, target_lang, source_lang, tone)
        
        if key in self.cache:
            # Check if the entry has expired
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                logger.info(f"Cache hit for '{text[:20]}...' to {target_lang}")
                return entry["result"]
            else:
                # Remove expired entry
                logger.info(f"Cache expired for '{text[:20]}...' to {target_lang}")
                del self.cache[key]
        
        return None
    
    def cache_translation(self, text: str, result: Dict[str, Any], target_lang: str, 
                         source_lang: Optional[str] = None, tone: str = "default") -> None:
        """
        Cache a translation result.
        
        Args:
            text (str): Text that was translated
            result (Dict[str, Any]): Translation result including translation and provider
            target_lang (str): Target language code
            source_lang (Optional[str]): Source language code or None for auto-detection
            tone (str): Formal or informal tone
        """
        # Only cache successful translations
        if not result.get("translation") or result.get("error"):
            return
        
        key = self._generate_key(text, target_lang, source_lang, tone)
        
        # Add timestamp to track entry age
        entry = {
            "result": result,
            "timestamp": time.time()
        }
        
        # Add to cache
        self.cache[key] = entry
        
        # If cache exceeds max size, remove oldest entries
        if len(self.cache) > self.max_size:
            # Sort by timestamp and keep only the most recent entries
            sorted_keys = sorted(self.cache.keys(), 
                                key=lambda k: self.cache[k]["timestamp"])
            
            # Remove oldest entries
            for old_key in sorted_keys[:len(sorted_keys) - self.max_size]:
                del self.cache[old_key]
        
        logger.info(f"Cached translation for '{text[:20]}...' to {target_lang}")
    
    def clear_cache(self) -> None:
        """Clear all entries from the cache."""
        self.cache = {}
        logger.info("Translation cache cleared")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, int]: Dictionary with cache stats (entries, size)
        """
        return {
            "entries": len(self.cache),
            "max_size": self.max_size
        }