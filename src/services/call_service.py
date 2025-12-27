import logging
import requests

from fastapi import HTTPException

from src.config.settings import VapiSettings
from src.models.domain.call import CallRequest, CallResponse, TriggerCallRequest, WebCallConfigResponse, WebCallResponse
from src.utils.helpers import handle_service_error

logger = logging.getLogger(__name__)

class CallService:
    def __init__(self):
        try:
            self.settings = VapiSettings()
            if not self.settings.vapi_api_key:
                logger.error("Vapi API key is not configured")
                raise ValueError(
                    "Vapi API key is not configured. Please set VAPI_API_KEY environment variable or add it to .env file.")
        except Exception as e:
            logger.error(f"Failed to load Vapi API settings: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize call service. Check environment variables."
            )
    
    async def make_call(self, call_data: CallRequest) -> CallResponse:
        """Make an outbound call using the full Vapi request format."""
        try:
            request_data = {
                "assistantId": call_data.assistant_id,
                "phoneNumberId": call_data.phone_number_id,
                "customer": {
                    "number": call_data.customer.number
                }
            }

            response = requests.post(
                f"{self.settings.vapi_api_url}/call",
                headers={
                    "Authorization": f"Bearer {self.settings.vapi_api_key}"
                },
                json=request_data,
            )

            response.raise_for_status()
            response_data = response.json()
            
            logger.info(f"Response data: {response_data}")
            logger.info(f"Successfully created call with ID: {response_data.get('id')}")

            return CallResponse(
                call_id=response_data.get("id"),
                status=response_data.get("status", "unknown")
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to make call via Vapi API: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                status_code = e.response.status_code
                error_detail = f"Vapi API error: {e.response.text}"
            else:
                status_code = 500
                error_detail = f"Failed to connect to Vapi API: {str(e)}"
            
            raise HTTPException(status_code=status_code, detail=error_detail)
        except Exception as e:
            handle_service_error(e, "call_service", "make_call")

    async def trigger_call(self, request: TriggerCallRequest) -> WebCallResponse:
        """
        Get configuration to trigger a web-based call.
        The frontend uses this config with Vapi Web SDK to connect the user via browser.
        
        Returns all necessary information for the frontend to initiate the call.
        """
        try:
            # Use provided values or fall back to defaults from settings
            assistant_id = request.assistant_id or self.settings.default_assistant_id
            
            # Validate required fields
            if not assistant_id:
                raise HTTPException(
                    status_code=400,
                    detail="assistant_id is required. Either provide it in the request or set DEFAULT_ASSISTANT_ID in environment."
                )
            
            if not self.settings.vapi_public_key:
                raise HTTPException(
                    status_code=400,
                    detail="VAPI_PUBLIC_KEY is not configured. Set it in environment for web-based calls."
                )

            logger.info(f"Preparing web call config for assistant {assistant_id}")

            # Return configuration for frontend to use with Vapi Web SDK
            # The frontend will call: vapi.start({ assistantId: assistant_id, assistantOverrides: ... })
            return WebCallResponse(
                call_id="pending",  # Call ID will be generated when frontend starts the call
                status="ready",
                web_call_url=None,
                transport={
                    "provider": "vapi-web-sdk",
                    "publicKey": self.settings.vapi_public_key,
                    "assistantId": assistant_id,
                    "assistantOverrides": request.assistant_overrides
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            handle_service_error(e, "call_service", "trigger_call")

    async def get_web_call_config(self) -> WebCallConfigResponse:
        """
        Get configuration for initiating a web-based call using Vapi Web SDK.
        The frontend can use this config to connect the user directly through their browser.
        
        Usage on frontend:
        1. Fetch this config
        2. Use Vapi Web SDK: vapi.start({ assistantId: config.assistant_id })
        """
        try:
            if not self.settings.vapi_public_key:
                raise HTTPException(
                    status_code=400,
                    detail="VAPI_PUBLIC_KEY is not configured. Set it in environment for web-based calls."
                )
            
            if not self.settings.default_assistant_id:
                raise HTTPException(
                    status_code=400,
                    detail="DEFAULT_ASSISTANT_ID is not configured. Set it in environment."
                )

            return WebCallConfigResponse(
                public_key=self.settings.vapi_public_key,
                assistant_id=self.settings.default_assistant_id,
                assistant_overrides=None  # Can be extended to include custom overrides
            )
        except HTTPException:
            raise
        except Exception as e:
            handle_service_error(e, "call_service", "get_web_call_config")
