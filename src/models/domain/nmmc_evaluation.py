"""
NMMC Property Tax Call Evaluation Models

Pydantic models for evaluating NMMC Property Tax Recovery calls.
Tracks 10 dimensions across citizen engagement, compliance, and call quality metrics.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class CitizenSentiment(str, Enum):
    """Citizen sentiment classification for property tax recovery calls."""
    COOPERATIVE = "cooperative"        # Willing to pay, polite, understanding
    RESISTANT = "resistant"            # Pushback, excuses, delays
    CONFUSED = "confused"              # Doesn't understand dues, needs explanation
    HOSTILE = "hostile"                # Abusive, threatening, aggressive
    INDIFFERENT = "indifferent"        # Unresponsive, dismissive, disengaged


class CallOutcome(str, Enum):
    """Outcome classification for property tax recovery calls."""
    PAYMENT_AGREED = "payment_agreed"              # Citizen agreed to pay immediately
    DATE_COMMITTED = "date_committed"              # Citizen committed to a specific payment date
    PARTIAL_COMMITMENT = "partial_commitment"      # Vague promise, no specific date
    DISPUTE_RAISED = "dispute_raised"              # Citizen disputes the amount or assessment
    REFUSED = "refused"                            # Citizen outright refused to pay
    UNREACHABLE = "unreachable"                    # Wrong number, not available, no answer
    CALL_DROPPED = "call_dropped"                  # Call disconnected unexpectedly
    ALREADY_PAID = "already_paid"                  # Citizen claims payment was already made


class ConsequenceLevelReached(str, Enum):
    """Highest consequence level disclosed during the call."""
    NONE = "none"                                  # No consequences mentioned
    LEVEL_1_FINANCIAL = "level_1_financial"         # DPC, penalties, accumulating charges
    LEVEL_2_ADMINISTRATIVE = "level_2_administrative"  # Blocked permits, NOCs, transactions
    LEVEL_3_LEGAL = "level_3_legal"                # Seizure, sealing, auction, legal notices
    LEVEL_4_NUCLEAR = "level_4_nuclear"            # Court proceedings, credit impact, permanent record


class CitizenResponseType(str, Enum):
    """How the citizen responded to the recovery call."""
    IMMEDIATE_PAYMENT = "immediate_payment"        # Agreed to pay right away
    REQUESTED_TIME = "requested_time"              # Asked for more time with a date
    FINANCIAL_HARDSHIP = "financial_hardship"       # Cited inability to pay
    DISPUTED_AMOUNT = "disputed_amount"            # Challenged the assessed amount
    CLAIMED_PAID = "claimed_paid"                  # Said they already paid
    ABUSIVE = "abusive"                            # Used abusive language or threats
    DISCONNECTED = "disconnected"                  # Hung up or call dropped
    COOPERATIVE_INQUIRY = "cooperative_inquiry"     # Asked about payment methods, schemes


class PaymentCommitment(str, Enum):
    """Payment commitment status from the call."""
    COMMITTED_WITH_DATE = "committed_with_date"    # Specific date given
    VAGUE_PROMISE = "vague_promise"                # "I'll pay soon" without date
    REFUSED = "refused"                            # Explicitly refused
    NOT_DISCUSSED = "not_discussed"                # Payment not discussed (wrong number, etc.)


class AmountBracket(str, Enum):
    """Outstanding amount bracket discussed."""
    UNDER_10K = "under_10k"                        # Less than Rs. 10,000
    BRACKET_10K_50K = "10k_to_50k"                 # Rs. 10,000 - 50,000
    BRACKET_50K_1L = "50k_to_1_lakh"              # Rs. 50,000 - 1,00,000
    BRACKET_1L_5L = "1_lakh_to_5_lakh"            # Rs. 1,00,000 - 5,00,000
    ABOVE_5L = "above_5_lakh"                      # Above Rs. 5,00,000
    NOT_DISCUSSED = "not_discussed"                # Amount not mentioned


class NMMCCallEvaluation(BaseModel):
    """
    Complete evaluation result for an NMMC Property Tax Recovery call.

    10 evaluation dimensions across 4 categories:
    - Core Metrics: citizen_sentiment, call_summary, escalation_required
    - Outcome Metrics: call_outcome, citizen_response_type, payment_commitment
    - Enforcement Metrics: consequence_level_reached, proper_protocol_followed
    - Context Metrics: compliance_score, amount_bracket
    """

    # Core Metrics
    citizen_sentiment: CitizenSentiment = Field(
        description="Citizen's emotional state and cooperativeness during the call"
    )
    call_summary: str = Field(
        description="2-3 sentence summary covering: who was called, what was discussed, and the outcome"
    )
    escalation_required: bool = Field(
        description="Whether the case needs supervisor review or legal department escalation"
    )

    # Outcome Metrics
    call_outcome: CallOutcome = Field(
        description="Final outcome classification of the recovery call"
    )
    citizen_response_type: CitizenResponseType = Field(
        description="How the citizen responded to the recovery attempt"
    )
    payment_commitment: PaymentCommitment = Field(
        description="Whether citizen committed to payment and with what specificity"
    )

    # Enforcement Metrics
    consequence_level_reached: ConsequenceLevelReached = Field(
        description="Highest level of consequences disclosed during the call"
    )
    proper_protocol_followed: bool = Field(
        description="Whether the agent followed proper call protocol (greeting, identification, escalation ladder)"
    )

    # Context Metrics
    compliance_score: int = Field(
        ge=1, le=10,
        description="Overall compliance likelihood score from 1 (will not pay) to 10 (immediate payment)"
    )
    amount_bracket: AmountBracket = Field(
        description="Outstanding amount bracket discussed during the call"
    )


class NMMCCallLogEntry(BaseModel):
    """Entry for CSV logging - NMMC Property Tax specific."""
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
