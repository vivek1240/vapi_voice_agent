from pydantic_settings import BaseSettings

class VapiSettings(BaseSettings):
    vapi_api_key: str | None = None  # Set via VAPI_API_KEY env variable
    vapi_api_url: str = "https://api.vapi.ai"
    vapi_public_key: str | None = None  # Public key for web SDK
    default_assistant_id: str | None = None  # Default assistant for quick calls
    default_phone_number_id: str | None = None  # Default phone number for outbound calls

    class Config:
        env_file = ".env"