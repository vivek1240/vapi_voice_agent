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
        "<uuid>": { "name": "citizen_sentiment", "result": "cooperative" },
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
# STRUCTURED OUTPUT ENUMS - NMMC Property Tax Recovery
# =============================================================================

class CitizenSentiment(str, Enum):
    """Citizen sentiment classification for property tax recovery calls."""
    COOPERATIVE = "cooperative"
    RESISTANT = "resistant"
    CONFUSED = "confused"
    HOSTILE = "hostile"
    INDIFFERENT = "indifferent"


class CallOutcomeCategory(str, Enum):
    """Call outcome classification for NMMC recovery calls."""
    PAYMENT_AGREED = "payment_agreed"
    DATE_COMMITTED = "date_committed"
    PARTIAL_COMMITMENT = "partial_commitment"
    DISPUTE_RAISED = "dispute_raised"
    REFUSED = "refused"
    UNREACHABLE = "unreachable"
    CALL_DROPPED = "call_dropped"
    ALREADY_PAID = "already_paid"


# =============================================================================
# STRUCTURED OUTPUTS MODEL
# =============================================================================

class StructuredOutputItem(BaseModel):
    """
    Individual structured output item from Vapi webhook.

    Each structured output is keyed by UUID with name and result.
    """
    name: str = Field(..., description="Name of the structured output (e.g., 'citizen_sentiment')")
    result: Any = Field(None, description="The extracted value (string, boolean, object, etc.)")


class StructuredOutputs(BaseModel):
    """
    Parsed structured outputs from NMMC Property Tax Recovery calls.

    These match the structured outputs configured in Vapi Dashboard:
    1. citizen_sentiment - Monitor citizen cooperativeness
    2. call_summary - Brief summary for recovery team
    3. call_outcome - Outcome classification
    4. escalation_required - Flag for supervisor/legal escalation
    5. compliance_score - Likelihood of payment (1-10)
    """

    citizen_sentiment: Optional[str] = Field(
        None,
        description="Citizen emotional state: cooperative, resistant, confused, hostile, or indifferent"
    )

    call_summary: Optional[str] = Field(
        None,
        description="2-3 sentence summary: who was called, what was discussed, outcome"
    )

    call_outcome: Optional[str] = Field(
        None,
        description="Call outcome category for tracking recovery success"
    )

    escalation_required: Optional[bool] = Field(
        None,
        description="True if case needs supervisor review or legal escalation"
    )

    compliance_score: Optional[int] = Field(
        None,
        description="Likelihood of payment from 1 (won't pay) to 10 (immediate payment)"
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
    """Entry for CSV logging - NMMC Property Tax Recovery evaluation with 10 dimensions."""
    call_id: str
    timestamp: str
    duration_seconds: Optional[float] = None

    # Core Metrics
    citizen_sentiment: Optional[str] = None
    call_summary: Optional[str] = None
    escalation_required: Optional[bool] = None

    # Outcome Metrics
    call_outcome: Optional[str] = None
    citizen_response_type: Optional[str] = None
    payment_commitment: Optional[str] = None

    # Enforcement Metrics
    consequence_level_reached: Optional[str] = None
    proper_protocol_followed: Optional[bool] = None

    # Context Metrics
    compliance_score: Optional[int] = None
    amount_bracket: Optional[str] = None

    # Call Data
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    cost: Optional[float] = None

