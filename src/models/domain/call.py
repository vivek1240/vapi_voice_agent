from pydantic import BaseModel, Field
from typing import Optional

class CustomerInfo(BaseModel):
    number: str = Field(..., description="Customer phone number")

class CallRequest(BaseModel):
    assistant_id: str = Field(..., description="ID of the Vapi assistant")
    phone_number_id: str = Field(..., description="ID of the phone number to use")
    customer: CustomerInfo = Field(..., description="Customer information")

class TriggerCallRequest(BaseModel):
    """Simplified request for triggering an outbound call."""
    customer_number: str = Field(..., description="Customer phone number to call")
    assistant_id: Optional[str] = Field(None, description="Override default assistant ID")
    phone_number_id: Optional[str] = Field(None, description="Override default phone number ID")

class WebCallConfigResponse(BaseModel):
    """Response containing configuration for Web SDK to initiate a browser-based call."""
    public_key: str = Field(..., description="Vapi public key for Web SDK")
    assistant_id: str = Field(..., description="Assistant ID to use for the call")
    assistant_overrides: Optional[dict] = Field(None, description="Optional assistant configuration overrides")

class CallResponse(BaseModel):
    call_id: str = Field(..., description="ID of the created call")
    status: str = Field(..., description="Status of the call")
    message: Optional[str] = Field(None, description="Additional message about the call")
