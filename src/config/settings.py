from pydantic_settings import BaseSettings

class VapiSettings(BaseSettings):
    vapi_api_key: str | None = "965ae1ac-2c85-4ace-8f46-34df5411b87a"
    vapi_api_url: str = "https://api.vapi.ai"
    vapi_public_key: str | None = None  # Public key for web SDK
    default_assistant_id: str | None =  "1f97450a-9d2f-4e39-8948-02582a67274b"  # Default assistant for quick calls
    default_phone_number_id: str | None = "2900b3f9-31df-49a5-8abe-322dc0d85a47"  # Default phone number for outbound calls

    class Config:
        env_file = ".env"