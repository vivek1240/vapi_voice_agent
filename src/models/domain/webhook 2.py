"""
Vapi Webhook Models - For receiving call events and structured outputs.

These models match the Structured Outputs configured in Vapi Dashboard.

Official Vapi Webhook Format (from docs.vapi.ai):
{
  "type": "call.ended",
  "call": {
    "id": "call_abc123",
    "artifact": {
      "structuredOutputs": {
        "<uuid>": { "name": "user_sentiment", "result": "positive" },
        "<uuid>": { "name": "call_summary", "result": "..." }
      }
    }
  }
}
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Literal, Dict
from datetime import datetime
from enum import Enum


# =============================================================================
# STRUCTURED OUTPUT ENUMS - Match your Vapi Dashboard configuration
# =============================================================================

class UserSentiment(str, Enum):
    """
    User sentiment classification.
    
    Assess the user's emotional state based on their tone and words.
    """
    POSITIVE = "positive"      # User expressed thanks, satisfaction, or relief
    NEUTRAL = "neutral"        # Matter-of-fact interaction, no strong emotion
    CONFUSED = "confused"      # User needed multiple explanations or seemed uncertain
    FRUSTRATED = "frustrated"  # User expressed annoyance, complained, or seemed upset


class QueryCategory(str, Enum):
    """
    Query category classification for identifying trends and pain points.
    
    Classify the primary topic into exactly one category.
    """
    ONBOARDING_NAVIGATION = "onboarding_navigation"  # Stuck on screens, button issues
    CONSENT_QUESTIONS = "consent_questions"          # EULA, privacy, terms
    BIOMETRIC_CONCERNS = "biometric_concerns"        # Face ID, data privacy
    SPOT_HEALTH = "spot_health"                      # Testing questions
    TELEHEALTH = "telehealth"                        # Results delivery
    PERMISSIONS = "permissions"                       # Notifications, microphone
    DATA_PRIVACY = "data_privacy"                    # Data sharing, rights
    TECHNICAL_ISSUE = "technical_issue"              # Bugs, crashes
    OUT_OF_SCOPE = "out_of_scope"                    # Medical advice, billing
    GENERAL_INQUIRY = "general_inquiry"              # Other app questions


# =============================================================================
# STRUCTURED OUTPUTS MODEL
# =============================================================================

class StructuredOutputItem(BaseModel):
    """
    Individual structured output item from Vapi webhook.
    
    Each structured output is keyed by UUID with name and result.
    """
    name: str = Field(..., description="Name of the structured output (e.g., 'user_sentiment')")
    result: Any = Field(None, description="The extracted value (string, boolean, object, etc.)")


class StructuredOutputs(BaseModel):
    """
    Parsed structured outputs from call conversations.
    
    These match the 5 structured outputs configured in Vapi Dashboard:
    1. user_sentiment - Monitor customer satisfaction
    2. call_summary - Brief summary for support team
    3. query_category - Categorize for trends analysis
    4. escalation_required - Flag for human follow-up
    5. query_resolved - Track AI resolution success
    """
    
    user_sentiment: Optional[str] = Field(
        None, 
        description="User emotional state: positive, neutral, confused, or frustrated"
    )
    
    call_summary: Optional[str] = Field(
        None, 
        description="2-3 sentence summary: what user asked, how AI helped, outcome"
    )
    
    query_category: Optional[str] = Field(
        None, 
        description="Primary topic category for trend analysis"
    )
    
    escalation_required: Optional[bool] = Field(
        None, 
        description="True if call needs human follow-up from support team"
    )
    
    query_resolved: Optional[bool] = Field(
        None, 
        description="True if AI fully answered the query without needing escalation"
    )


class CallArtifact(BaseModel):
    """
    Call artifact containing structured outputs and other data.
    
    Per Vapi docs: call.artifact.structuredOutputs contains the extracted data.
    """
    structuredOutputs: Optional[Dict[str, StructuredOutputItem]] = Field(
        None, 
        description="Dict of UUID -> {name, result} for each structured output"
    )
    transcript: Optional[str] = Field(None, description="Full call transcript")
    recordingUrl: Optional[str] = Field(None, description="URL to call recording")
    messages: Optional[list] = Field(None, description="List of messages in the call")


class VapiCall(BaseModel):
    """
    Vapi call object in webhook payload.
    
    Contains call metadata and artifact with structured outputs.
    """
    id: str = Field(..., description="Unique call ID")
    status: Optional[str] = Field(None, description="Call status")
    startedAt: Optional[str] = Field(None, description="Call start timestamp")
    endedAt: Optional[str] = Field(None, description="Call end timestamp")
    cost: Optional[float] = Field(None, description="Call cost in USD")
    artifact: Optional[CallArtifact] = Field(None, description="Call artifacts including structured outputs")
    
    # Allow extra fields
    class Config:
        extra = "allow"


class VapiWebhookPayload(BaseModel):
    """
    Vapi webhook payload structure.
    
    Per official Vapi docs (docs.vapi.ai/assistants/structured-outputs-examples):
    - type: "call.ended" for completed calls with structured outputs
    - call: Contains id, artifact.structuredOutputs, etc.
    
    Event types include:
    - call.started / call.ended
    - status-update
    - transcript
    - function-call
    """
    # Event type
    type: str = Field(..., description="Event type: call.ended, status-update, etc.")
    
    # Call object (contains structured outputs in artifact)
    call: Optional[VapiCall] = Field(None, description="Call object with artifact.structuredOutputs")
    
    # Legacy fields (may still be present in some webhook types)
    transcript: Optional[str] = Field(None, description="Full call transcript (legacy)")
    recordingUrl: Optional[str] = Field(None, description="URL to call recording (legacy)")
    
    # Allow extra fields for flexibility
    class Config:
        extra = "allow"


class CallLogEntry(BaseModel):
    """Entry for CSV logging."""
    call_id: str
    timestamp: str
    duration_seconds: Optional[float] = None
    user_sentiment: Optional[str] = None
    call_summary: Optional[str] = None
    query_category: Optional[str] = None
    escalation_required: Optional[bool] = None
    query_resolved: Optional[bool] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    cost: Optional[float] = None

