"""API Key rotation manager with automatic fallback"""
import os
import time
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


class APIKeyManager:
    """Manages multiple API keys with automatic rotation and fallback"""
    
    def __init__(self, key_prefix: str = "GOOGLE_API_KEY"):
        """
        Initialize API Key Manager
        
        Args:
            key_prefix: Prefix for environment variables (e.g., "GOOGLE_API_KEY")
        """
        self.key_prefix = key_prefix
        self.api_keys = self._load_api_keys()
        self.current_index = 0
        self.failed_keys = set()  # Track failed keys
        self.key_usage_count = {}  # Track usage per key
        self.last_rotation_time = time.time()
        
        if not self.api_keys:
            raise ValueError(f"No API keys found with prefix '{key_prefix}_*'")
        
        print(f"✅ Loaded {len(self.api_keys)} API keys for rotation")
    
    def _load_api_keys(self) -> List[str]:
        """Load all API keys from environment variables"""
        keys = []
        i = 1
        
        # Try loading GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.
        while True:
            key_name = f"{self.key_prefix}_{i}"
            key_value = os.getenv(key_name)
            
            if key_value:
                keys.append(key_value.strip())
                print(f"  📌 Loaded {key_name}")
                i += 1
            else:
                break
        
        # Also try loading base key (GOOGLE_API_KEY without number)
        base_key = os.getenv(self.key_prefix)
        if base_key and base_key not in keys:
            keys.insert(0, base_key.strip())
            print(f"  📌 Loaded {self.key_prefix} (base key)")
        
        return keys
    
    def get_current_key(self) -> str:
        """Get the current active API key"""
        if not self.api_keys:
            raise ValueError("No API keys available")
        
        # Get current key
        current_key = self.api_keys[self.current_index]
        
        # Track usage
        if current_key not in self.key_usage_count:
            self.key_usage_count[current_key] = 0
        self.key_usage_count[current_key] += 1
        
        return current_key
    
    def rotate_key(self, reason: str = "manual") -> str:
        """
        Rotate to the next available API key
        
        Args:
            reason: Reason for rotation (manual, rate_limit, error, etc.)
        
        Returns:
            Next available API key
        """
        # Mark current key as failed if rotating due to error
        if reason in ["rate_limit", "error", "expired"]:
            current_key = self.api_keys[self.current_index]
            self.failed_keys.add(current_key)
            print(f"  ⚠️  Key {self.current_index + 1} marked as failed ({reason})")
        
        # Try next key
        attempts = 0
        max_attempts = len(self.api_keys)
        
        while attempts < max_attempts:
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            next_key = self.api_keys[self.current_index]
            
            # Skip failed keys
            if next_key in self.failed_keys:
                attempts += 1
                continue
            
            print(f"  🔄 Rotated to key {self.current_index + 1}/{len(self.api_keys)}")
            self.last_rotation_time = time.time()
            return next_key
        
        # All keys failed - reset and try again
        print("  ⚠️  All keys failed! Resetting failed keys list...")
        self.failed_keys.clear()
        self.current_index = 0
        return self.api_keys[0]
    
    def mark_key_as_working(self):
        """Mark current key as working (remove from failed list)"""
        current_key = self.api_keys[self.current_index]
        if current_key in self.failed_keys:
            self.failed_keys.remove(current_key)
            print(f"  ✅ Key {self.current_index + 1} marked as working")
    
    def get_stats(self) -> dict:
        """Get usage statistics"""
        return {
            "total_keys": len(self.api_keys),
            "current_key_index": self.current_index + 1,
            "failed_keys_count": len(self.failed_keys),
            "active_keys": len(self.api_keys) - len(self.failed_keys),
            "key_usage": self.key_usage_count,
            "time_since_rotation": time.time() - self.last_rotation_time
        }
    
    def reset_all_keys(self):
        """Reset all keys (clear failed list)"""
        self.failed_keys.clear()
        self.current_index = 0
        print("  🔄 All keys reset")


# Global instance
_key_manager: Optional[APIKeyManager] = None


def get_key_manager(key_prefix: str = "GOOGLE_API_KEY") -> APIKeyManager:
    """Get or create global API key manager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager(key_prefix)
    return _key_manager


def get_api_key() -> str:
    """Get current API key (convenience function)"""
    manager = get_key_manager()
    return manager.get_current_key()


def rotate_api_key(reason: str = "manual") -> str:
    """Rotate API key (convenience function)"""
    manager = get_key_manager()
    return manager.rotate_key(reason)