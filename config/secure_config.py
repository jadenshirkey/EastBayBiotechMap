#!/usr/bin/env python3
"""
Secure Configuration Management for East Bay Biotech Map
Handles API keys and sensitive configuration with validation
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import hashlib
import json

logger = logging.getLogger(__name__)

class SecureConfig:
    """Secure configuration manager for API keys and sensitive data"""

    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize secure configuration

        Args:
            env_file: Optional path to .env file
        """
        # Load environment variables from .env file if it exists
        if env_file and env_file.exists():
            load_dotenv(env_file)
        else:
            # Try default locations
            for env_path in ['.env', '../.env', '../../.env']:
                env_path = Path(env_path)
                if env_path.exists():
                    load_dotenv(env_path)
                    break

        # Initialize configuration
        self._config = {}
        self._load_config()

    def _load_config(self):
        """Load and validate configuration from environment variables"""

        # Google Maps API Key
        google_maps_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if google_maps_key:
            # Validate it's not a placeholder
            if "YOUR_KEY_HERE" in google_maps_key or len(google_maps_key) < 20:
                raise ValueError("Invalid Google Maps API key. Please set GOOGLE_MAPS_API_KEY environment variable.")
            self._config['google_maps_api_key'] = google_maps_key
        else:
            logger.warning("GOOGLE_MAPS_API_KEY not set. Google Maps enrichment will be disabled.")

        # SEC EDGAR User Agent
        sec_user_agent = os.environ.get("SEC_EDGAR_USER_AGENT")
        if sec_user_agent:
            # Validate email format
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if not re.search(email_pattern, sec_user_agent):
                raise ValueError(
                    "SEC_EDGAR_USER_AGENT must include a valid email address.\n"
                    "Format: 'YourAppName/1.0 (your.email@domain.com)'"
                )
            self._config['sec_edgar_user_agent'] = sec_user_agent
        else:
            logger.warning("SEC_EDGAR_USER_AGENT not set. SEC EDGAR enrichment will be disabled.")

        # Database path
        db_path = os.environ.get("BIOTECH_DB_PATH", "data/bayarea_biotech_sources.db")
        self._config['database_path'] = Path(db_path)

        # API Rate Limits
        self._config['google_maps_rate_limit'] = float(os.environ.get("GOOGLE_MAPS_RATE_LIMIT", "0.1"))
        self._config['sec_edgar_rate_limit'] = float(os.environ.get("SEC_EDGAR_RATE_LIMIT", "0.1"))
        self._config['clinical_trials_rate_limit'] = float(os.environ.get("CLINICAL_TRIALS_RATE_LIMIT", "0.5"))

        # Retry configuration
        self._config['max_retries'] = int(os.environ.get("API_MAX_RETRIES", "3"))
        self._config['retry_delay'] = float(os.environ.get("API_RETRY_DELAY", "1.0"))

        # Security settings
        self._config['enable_ssl_verify'] = os.environ.get("ENABLE_SSL_VERIFY", "true").lower() == "true"

    def get(self, key: str, default=None):
        """
        Get configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    @property
    def google_maps_api_key(self) -> Optional[str]:
        """Get Google Maps API key"""
        return self._config.get('google_maps_api_key')

    @property
    def sec_edgar_user_agent(self) -> Optional[str]:
        """Get SEC EDGAR User Agent"""
        return self._config.get('sec_edgar_user_agent')

    @property
    def database_path(self) -> Path:
        """Get database path"""
        return self._config.get('database_path', Path("data/bayarea_biotech_sources.db"))

    def is_google_maps_enabled(self) -> bool:
        """Check if Google Maps API is configured"""
        return bool(self.google_maps_api_key)

    def is_sec_edgar_enabled(self) -> bool:
        """Check if SEC EDGAR API is configured"""
        return bool(self.sec_edgar_user_agent)

    def get_api_headers(self, service: str) -> dict:
        """
        Get API headers for a specific service

        Args:
            service: Service name ('google_maps', 'sec_edgar', etc.)

        Returns:
            Dictionary of headers
        """
        headers = {}

        if service == 'sec_edgar' and self.sec_edgar_user_agent:
            headers['User-Agent'] = self.sec_edgar_user_agent
            headers['Accept'] = 'application/json'

        return headers

    def mask_sensitive_value(self, value: str, visible_chars: int = 4) -> str:
        """
        Mask sensitive values for logging

        Args:
            value: Value to mask
            visible_chars: Number of characters to show at start and end

        Returns:
            Masked value
        """
        if not value or len(value) <= visible_chars * 2:
            return "***"

        return f"{value[:visible_chars]}...{value[-visible_chars:]}"

    def log_config_status(self):
        """Log configuration status (with sensitive values masked)"""
        logger.info("Configuration Status:")
        logger.info(f"  Google Maps API: {'Enabled' if self.is_google_maps_enabled() else 'Disabled'}")
        if self.is_google_maps_enabled():
            logger.info(f"    Key: {self.mask_sensitive_value(self.google_maps_api_key)}")

        logger.info(f"  SEC EDGAR API: {'Enabled' if self.is_sec_edgar_enabled() else 'Disabled'}")
        if self.is_sec_edgar_enabled():
            logger.info(f"    User-Agent: {self.sec_edgar_user_agent}")

        logger.info(f"  Database Path: {self.database_path}")
        logger.info(f"  SSL Verification: {self._config.get('enable_ssl_verify', True)}")
        logger.info(f"  Max Retries: {self._config.get('max_retries', 3)}")


# Global configuration instance
_config = None

def get_config() -> SecureConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = SecureConfig()
    return _config