from pydantic import BaseModel, Field
from typing import Optional

class CustomerInfo(BaseModel):
    number: str = Field(..., description="Customer phone number")

class CallRequest(BaseModel):
    assistant_id: str = Field(..., description="ID of the Vapi assistant")
    phone_number_id: str = Field(..., description="ID of the phone number to use")
    customer: CustomerInfo = Field(..., description="Customer information")

class ModelConfig(BaseModel):
    """LLM model configuration for assistant overrides."""
    provider: str = Field("openai", description="LLM provider: openai, anthropic, google, groq, together-ai, deepseek")
    model: str = Field("gpt-4o", description="Model name: gpt-4o, gpt-4o-mini, claude-3-opus, gemini-pro, etc.")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Temperature (0-2)")

class VoiceConfig(BaseModel):
    """Voice configuration for assistant overrides."""
    provider: str = Field("11labs", description="Voice provider: 11labs, playht, deepgram, azure, cartesia, openai")
    voice_id: str = Field(..., description="Voice ID from the provider (e.g., 'sarah', 'burt' for 11labs)")

class TriggerCallRequest(BaseModel):
    """Request for triggering a web-based call (user connects via browser)."""
    assistant_id: Optional[str] = Field(None, description="Override default assistant ID")
    
    # Structured configuration (user-friendly)
    model: Optional[ModelConfig] = Field(None, description="Override LLM model configuration")
    voice: Optional[VoiceConfig] = Field(None, description="Override voice configuration")
    first_message: Optional[str] = Field(None, description="First message the assistant says")
    system_prompt: Optional[str] = Field(None, description="System prompt for the assistant")
    
    # Raw overrides (for advanced users who know Vapi format)
    assistant_overrides: Optional[dict] = Field(None, description="Raw assistant overrides (advanced)")

class WebCallConfigResponse(BaseModel):
    """Response containing configuration for Web SDK to initiate a browser-based call."""
    public_key: str = Field(..., description="Vapi public key for Web SDK")
    assistant_id: str = Field(..., description="Assistant ID to use for the call")
    assistant_overrides: Optional[dict] = Field(None, description="Optional assistant configuration overrides")

class CallResponse(BaseModel):
    call_id: str = Field(..., description="ID of the created call")
    status: str = Field(..., description="Status of the call")
    message: Optional[str] = Field(None, description="Additional message about the call")

class WebCallResponse(BaseModel):
    """Response for web call containing connection details."""
    call_id: str = Field(..., description="ID of the created call")
    status: str = Field(..., description="Status of the call")
    web_call_url: Optional[str] = Field(None, description="URL to connect to the web call")
    transport: Optional[dict] = Field(None, description="Transport/WebRTC configuration for connecting")
