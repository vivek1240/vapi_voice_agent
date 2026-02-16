import logging
import requests

from fastapi import HTTPException

from src.config.settings import VapiSettings
from src.config.call_config import get_call_config
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
        
        Priority order for configuration:
        1. Per-call request values (highest priority)
        2. Config file / environment defaults (CALL_* env vars)
        3. Vapi dashboard assistant config (used when nothing is set)
        """
        try:
            # Load call config defaults
            call_config = get_call_config()
            
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

            # Build assistantOverrides - merge config defaults with request overrides
            # Start with raw overrides if provided
            assistant_overrides = dict(request.assistant_overrides) if request.assistant_overrides else {}
            
            # Determine effective values (request > config > None)
            # Model configuration
            model_provider = (request.model.provider if request.model else None) or call_config.model_provider
            model_name = (request.model.model if request.model else None) or call_config.model_name
            model_temp = (request.model.temperature if request.model else None) or call_config.model_temperature
            
            if model_provider and model_name:
                model_config = {
                    "provider": model_provider,
                    "model": model_name,
                }
                if model_temp is not None:
                    model_config["temperature"] = model_temp
                assistant_overrides["model"] = model_config
            
            # Voice configuration
            voice_provider = (request.voice.provider if request.voice else None) or call_config.voice_provider
            voice_id = (request.voice.voice_id if request.voice else None) or call_config.voice_id
            
            if voice_provider and voice_id:
                assistant_overrides["voice"] = {
                    "provider": voice_provider,
                    "voiceId": voice_id  # Note: camelCase for Vapi API
                }
            
            # First message (request > config)
            first_message = request.first_message or call_config.first_message
            if first_message:
                assistant_overrides["firstMessage"] = first_message
            
            # System prompt (request > config)
            system_prompt = request.system_prompt or call_config.system_prompt
            if system_prompt:
                if "model" not in assistant_overrides:
                    assistant_overrides["model"] = {}
                # Vapi requires model.provider when model object is present in overrides
                if "provider" not in assistant_overrides["model"]:
                    assistant_overrides["model"]["provider"] = "openai"
                if "model" not in assistant_overrides["model"] or not assistant_overrides["model"].get("model"):
                    assistant_overrides["model"]["model"] = "gpt-4o"
                assistant_overrides["model"]["messages"] = [
                    {"role": "system", "content": system_prompt}
                ]

            logger.info(f"Preparing web call config for assistant {assistant_id}")
            if assistant_overrides:
                logger.info(f"With overrides: {list(assistant_overrides.keys())}")
            else:
                logger.info("No overrides - using Vapi dashboard defaults")

            # Return configuration for frontend to use with Vapi Web SDK
            # The frontend will call: vapi.start(assistantId, assistantOverrides)
            return WebCallResponse(
                call_id="pending",  # Call ID will be generated when frontend starts the call
                status="ready",
                web_call_url=None,
                transport={
                    "provider": "vapi-web-sdk",
                    "publicKey": self.settings.vapi_public_key,
                    "assistantId": assistant_id,
                    "assistantOverrides": assistant_overrides if assistant_overrides else None
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
