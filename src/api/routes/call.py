import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from src.models.domain.call import CallRequest, CallResponse, TriggerCallRequest, WebCallConfigResponse, WebCallResponse
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


@router.post('/trigger_call/', response_model=WebCallResponse)
async def trigger_call(
    request: TriggerCallRequest = TriggerCallRequest(),
    service: CallService = Depends(get_call_service)
):
    """
    Trigger a web-based call - user connects to AI assistant via browser.
    
    Simply call this endpoint and the user can connect through their browser.
    No phone number needed - this is for web calls where the user
    talks to the AI assistant through WebRTC in their browser.
    
    **Example payloads:**
    
    Minimal (uses defaults from .env):
    ```json
    {}
    ```
    
    With custom first message:
    ```json
    {
        "first_message": "Hi! Welcome to customer support. How can I help?"
    }
    ```
    
    With model and voice overrides:
    ```json
    {
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.7
        },
        "voice": {
            "provider": "11labs",
            "voice_id": "sarah"
        },
        "first_message": "Hello! How can I assist you today?",
        "system_prompt": "You are a helpful customer support agent."
    }
    ```
    
    Returns transport config that the frontend uses with Vapi Web SDK:
    `vapi.start(assistantId, assistantOverrides)`
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
