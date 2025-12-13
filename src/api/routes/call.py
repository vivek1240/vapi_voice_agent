import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from src.models.domain.call import CallRequest, CallResponse, TriggerCallRequest, WebCallConfigResponse
from src.models.domain.response import ToolResponse
from src.models.domain.tool import ValidatedToolCall
from src.services.call_service import CallService
from src.api.dependencies import get_validated_tool_call

logger = logging.getLogger(__name__)

router = APIRouter(tags=["call"])

def get_call_service() -> CallService:
    return CallService()

@router.post('/make_call/', response_model=ToolResponse)
async def make_call(
    validated: Annotated[ValidatedToolCall[CallRequest], Depends(get_validated_tool_call('makeCall', CallRequest))],
    service: Annotated[CallService, Depends(get_call_service)]
):
    """
    Make an outbound call - used by Vapi tool calls.
    Requires the full VapiRequest wrapper format.
    """
    result = await service.make_call(validated.args)
    return ToolResponse.create(validated.tool_call_id, result)


@router.post('/trigger_call/', response_model=CallResponse)
async def trigger_call(
    request: TriggerCallRequest,
    service: Annotated[CallService, Depends(get_call_service)]
):
    """
    Simplified endpoint to trigger an outbound call with a single click.
    
    This endpoint can be called directly without the Vapi request wrapper.
    Just provide the customer phone number, and optionally override the 
    assistant_id and phone_number_id.
    
    Example payload:
    {
        "customer_number": "+1234567890"
    }
    
    Or with overrides:
    {
        "customer_number": "+1234567890",
        "assistant_id": "your-assistant-id",
        "phone_number_id": "your-phone-number-id"
    }
    """
    return await service.trigger_call(request)


@router.get('/web_call_config/', response_model=WebCallConfigResponse)
async def get_web_call_config(
    service: Annotated[CallService, Depends(get_call_service)]
):
    """
    Get configuration for initiating a web-based call using Vapi Web SDK.
    
    Use this endpoint to get the necessary configuration for your frontend
    to connect users directly through their browser (no phone number needed).
    
    Frontend usage with Vapi Web SDK:
    
    ```javascript
    import Vapi from '@vapi-ai/web';
    
    // Fetch config from this endpoint
    const config = await fetch('/call/web_call_config/').then(r => r.json());
    
    // Initialize Vapi with the public key
    const vapi = new Vapi(config.public_key);
    
    // Start the call when user clicks button
    document.getElementById('callButton').onclick = () => {
        vapi.start({ assistantId: config.assistant_id });
    };
    ```
    
    Returns:
        - public_key: Your Vapi public key for the Web SDK
        - assistant_id: The default assistant ID to use
        - assistant_overrides: Optional configuration overrides
    """
    return await service.get_web_call_config()
