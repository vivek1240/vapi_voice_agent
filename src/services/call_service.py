import logging
import requests

from fastapi import HTTPException

from src.config.settings import VapiSettings
from src.models.domain.call import CallRequest, CallResponse, TriggerCallRequest, WebCallConfigResponse
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

    async def trigger_call(self, request: TriggerCallRequest) -> CallResponse:
        """
        Simplified endpoint to trigger an outbound call.
        Uses default assistant_id and phone_number_id from settings if not provided.
        This is the endpoint users can call directly with just a customer phone number.
        """
        try:
            # Use provided values or fall back to defaults from settings
            assistant_id = request.assistant_id or self.settings.default_assistant_id
            phone_number_id = request.phone_number_id or self.settings.default_phone_number_id
            
            # Validate required fields
            if not assistant_id:
                raise HTTPException(
                    status_code=400,
                    detail="assistant_id is required. Either provide it in the request or set DEFAULT_ASSISTANT_ID in environment."
                )
            if not phone_number_id:
                raise HTTPException(
                    status_code=400,
                    detail="phone_number_id is required. Either provide it in the request or set DEFAULT_PHONE_NUMBER_ID in environment."
                )

            request_data = {
                "assistantId": assistant_id,
                "phoneNumberId": phone_number_id,
                "customer": {
                    "number": request.customer_number
                }
            }

            logger.info(f"Triggering call to {request.customer_number} with assistant {assistant_id}")

            response = requests.post(
                f"{self.settings.vapi_api_url}/call",
                headers={
                    "Authorization": f"Bearer {self.settings.vapi_api_key}",
                    "Content-Type": "application/json"
                },
                json=request_data,
            )

            response.raise_for_status()
            response_data = response.json()
            
            logger.info(f"Call triggered successfully. Call ID: {response_data.get('id')}")

            return CallResponse(
                call_id=response_data.get("id"),
                status=response_data.get("status", "queued"),
                message=f"Call initiated to {request.customer_number}"
            )
        except HTTPException:
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger call via Vapi API: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                status_code = e.response.status_code
                error_detail = f"Vapi API error: {e.response.text}"
            else:
                status_code = 500
                error_detail = f"Failed to connect to Vapi API: {str(e)}"
            
            raise HTTPException(status_code=status_code, detail=error_detail)
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
