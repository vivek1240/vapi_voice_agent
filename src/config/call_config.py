"""
Call Configuration - Controls default assistant overrides.

This file IS committed to GitHub with your default settings.
Environment variables (CALL_* prefix) can override these for production.

Priority order:
1. Per-call API request (highest)
2. Environment variables (CALL_MODEL_PROVIDER, etc.)
3. Defaults defined below in this file
4. Vapi dashboard config (when set to None)
"""

from pydantic import BaseModel
from typing import Optional
from src.config.nmmc_system_prompt import NMMC_SYSTEM_PROMPT


# =============================================================================
# DEFAULT CONFIGURATION — NMMC Property Tax Recovery Agent "Vivek"
# =============================================================================
# Set to None to use Vapi dashboard defaults
# Set to a value to override for all calls

DEFAULTS = {
    # Model Configuration
    # Set to None = Use Vapi Dashboard settings
    "model_provider": None,        # e.g., "openai", "anthropic", "google", "groq"
    "model_name": None,            # e.g., "gpt-4o", "gpt-4o-mini", "claude-3-opus"
    "model_temperature": None,     # e.g., 0.7 (range: 0.0 to 2.0)
    
    # Voice Configuration
    "voice_provider": None,        # e.g., "11labs", "playht", "deepgram", "openai"
    "voice_id": None,              # e.g., "sarah", "burt", "rachel"
    
    # Assistant Behavior — NMMC Property Tax Recovery
    # Keep firstMessage as a short intro; the identity confirmation question is handled once in the system prompt.
    "first_message": "Good day. My name is Vivek and I am calling from the Property Tax Department of the Navi Mumbai Municipal Corporation.",
    "system_prompt": NMMC_SYSTEM_PROMPT,
}
# =============================================================================


import os


class CallConfig(BaseModel):
    """Call configuration with file defaults + env var overrides."""
    
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    model_temperature: Optional[float] = None
    voice_provider: Optional[str] = None
    voice_id: Optional[str] = None
    first_message: Optional[str] = None
    system_prompt: Optional[str] = None


def get_call_config() -> CallConfig:
    """
    Load call configuration.
    Priority: Environment variables > File defaults > None (use Vapi dashboard)
    """
    def get_value(key: str, default):
        """Get value from env var or fall back to file default."""
        env_key = f"CALL_{key.upper()}"
        env_val = os.getenv(env_key)
        if env_val is not None:
            return env_val
        return default
    
    def get_float(key: str, default):
        """Get float value from env or default."""
        env_key = f"CALL_{key.upper()}"
        env_val = os.getenv(env_key)
        if env_val is not None:
            try:
                return float(env_val)
            except ValueError:
                return default
        return default
    
    return CallConfig(
        model_provider=get_value("model_provider", DEFAULTS["model_provider"]),
        model_name=get_value("model_name", DEFAULTS["model_name"]),
        model_temperature=get_float("model_temperature", DEFAULTS["model_temperature"]),
        voice_provider=get_value("voice_provider", DEFAULTS["voice_provider"]),
        voice_id=get_value("voice_id", DEFAULTS["voice_id"]),
        first_message=get_value("first_message", DEFAULTS["first_message"]),
        system_prompt=get_value("system_prompt", DEFAULTS["system_prompt"]),
    )

