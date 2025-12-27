from pydantic import BaseModel, Field
from typing import Optional

class CustomerInfo(BaseModel):
    number: str = Field(..., description="Customer phone number")

class CallRequest(BaseModel):
    assistant_id: str = Field(..., description="ID of the Vapi assistant")
    phone_number_id: str = Field(..., description="ID of the phone number to use")
    customer: CustomerInfo = Field(..., description="Customer information")

class TriggerCallRequest(BaseModel):
    """Request for triggering a web-based call (user connects via browser)."""
    assistant_id: Optional[str] = Field(None, description="Override default assistant ID")
    assistant_overrides: Optional[dict] = Field(None, description="Optional assistant configuration overrides")

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
