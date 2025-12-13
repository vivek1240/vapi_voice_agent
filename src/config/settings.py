from pydantic_settings import BaseSettings

class VapiSettings(BaseSettings):
    vapi_api_key: str | None = "965ae1ac-2c85-4ace-8f46-34df5411b87a"
    vapi_api_url: str = "https://api.vapi.ai"

    class Config:
        env_file = ".env"