"""Configuration utility using environment variables."""

import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)


class Config:
    """Configuration class for Sharp Agents application."""
    
    def __init__(self):
        # Database Configuration
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sharp_agents.db")
        
        # API URLs
        self.POLYMARKET_API_URL = os.getenv("POLYMARKET_API_URL", "https://clob.polymarket.com")
        self.KALSHI_API_URL = os.getenv("KALSHI_API_URL", "https://api.kalshi.com/trade-api/v2")
        
        # API Keys
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.POLYMARKET_API_KEY = os.getenv("POLYMARKET_API_KEY")
        self.KALSHI_API_KEY = os.getenv("KALSHI_API_KEY")
        self.KALSHI_API_SECRET = os.getenv("KALSHI_API_SECRET")
        
        # Kalshi Configuration
        self.KALSHI_REQUEST_TIMEOUT = int(os.getenv("KALSHI_REQUEST_TIMEOUT", "10"))
        self.SAFE_MODE = os.getenv("SAFE_MODE", "true").lower() == "true"
        
        # Application Settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.ARBITRAGE_MIN_THRESHOLD = float(os.getenv("ARBITRAGE_MIN_THRESHOLD", "0.02"))
        self.SCRAPE_INTERVAL_SECONDS = int(os.getenv("SCRAPE_INTERVAL_SECONDS", "300"))
        
        # Flask Configuration
        self.FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
        self.FLASK_ENV = os.getenv("FLASK_ENV", "development")
        self.FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
        self.FLASK_PORT = int(os.getenv("FLASK_PORT", "8000"))
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        return self.DATABASE_URL
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return self.OPENAI_API_KEY
    
    def get_polymarket_api_key(self) -> Optional[str]:
        """Get Polymarket API key."""
        return self.POLYMARKET_API_KEY
    
    def get_kalshi_api_key(self) -> Optional[str]:
        """Get Kalshi API key."""
        return self.KALSHI_API_KEY
    
    def get_kalshi_api_secret(self) -> Optional[str]:
        """Get Kalshi API secret."""
        return self.KALSHI_API_SECRET
    
    def get_kalshi_request_timeout(self) -> int:
        """Get Kalshi API request timeout in seconds."""
        return self.KALSHI_REQUEST_TIMEOUT
    
    def is_safe_mode(self) -> bool:
        """Check if safe mode is enabled (prevents accidental orders)."""
        return self.SAFE_MODE
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.FLASK_ENV == "production"
    
    def get_arbitrage_threshold(self) -> float:
        """Get minimum arbitrage threshold as decimal (e.g., 0.02 for 2%)."""
        return self.ARBITRAGE_MIN_THRESHOLD
    
    def get_scrape_interval(self) -> int:
        """Get scraping interval in seconds."""
        return self.SCRAPE_INTERVAL_SECONDS
    
    def get_flask_port(self) -> int:
        """Get Flask server port."""
        return self.FLASK_PORT
    
    def validate(self) -> bool:
        """Validate required configuration values."""
        required_fields = [
            "OPENAI_API_KEY",
            "DATABASE_URL"
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Required configuration field '{field}' is missing")
        
        return True
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            "DATABASE_URL": self.DATABASE_URL,
            "POLYMARKET_API_URL": self.POLYMARKET_API_URL,
            "KALSHI_API_URL": self.KALSHI_API_URL,
            "KALSHI_REQUEST_TIMEOUT": self.KALSHI_REQUEST_TIMEOUT,
            "SAFE_MODE": self.SAFE_MODE,
            "LOG_LEVEL": self.LOG_LEVEL,
            "ARBITRAGE_MIN_THRESHOLD": self.ARBITRAGE_MIN_THRESHOLD,
            "SCRAPE_INTERVAL_SECONDS": self.SCRAPE_INTERVAL_SECONDS,
            "FLASK_ENV": self.FLASK_ENV,
            "FLASK_DEBUG": self.FLASK_DEBUG,
            "FLASK_PORT": self.FLASK_PORT
        }


# Global configuration instance
_config = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        _config.validate()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment variables."""
    global _config
    _config = Config()
    _config.validate()
    return _config


# Backward compatibility functions
def get_config_value(key: str, default: str = None) -> str:
    """Get a specific configuration value (backward compatibility)."""
    config = get_config()
    return getattr(config, key, default)


def get_database_url() -> str:
    """Get database connection URL (backward compatibility)."""
    return get_config().get_database_url()


def get_openai_api_key() -> str:
    """Get OpenAI API key (backward compatibility)."""
    return get_config().get_openai_api_key()


def is_production() -> bool:
    """Check if running in production mode (backward compatibility)."""
    return get_config().is_production()


def get_kalshi_request_timeout() -> int:
    """Get Kalshi API request timeout in seconds (backward compatibility)."""
    return get_config().get_kalshi_request_timeout()


def is_safe_mode() -> bool:
    """Check if safe mode is enabled (backward compatibility)."""
    return get_config().is_safe_mode()
