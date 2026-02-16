"""
NMMC Property Tax Call Evaluator Service - Evaluates recovery call transcripts using Groq LLM.

Uses Groq's Structured Outputs feature for guaranteed JSON schema compliance.

Evaluates calls across 10 dimensions:
- Core: citizen_sentiment, call_summary, escalation_required
- Outcome: call_outcome, citizen_response_type, payment_commitment
- Enforcement: consequence_level_reached, proper_protocol_followed
- Context: compliance_score, amount_bracket
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# System prompt for the evaluator
NMMC_EVALUATOR_SYSTEM_PROMPT = """You are a call quality analyst for the Navi Mumbai Municipal Corporation (NMMC) Property Tax Recovery Department.

The NMMC recovery agent ("Vivek") calls citizens with outstanding property tax dues to recover payments. The agent follows a structured protocol: identification, stating purpose, escalating consequences, offering relief schemes, and documenting the citizen's response.

Analyze the call transcript and evaluate these 10 dimensions:

## 1. citizen_sentiment
Assess the citizen's emotional state and cooperativeness:
- "cooperative": willing to pay, polite, understanding of obligations
- "resistant": pushback, making excuses, trying to delay
- "confused": doesn't understand dues, needs explanation of amount or process
- "hostile": abusive, threatening, aggressive, using inappropriate language
- "indifferent": unresponsive, dismissive, disengaged from the conversation

## 2. call_summary
Write 2-3 sentences covering:
- Who was called (citizen name if available) and regarding which property/zone
- What was discussed (amount, consequences, schemes)
- The outcome (payment agreed, date given, refused, etc.)

## 3. call_outcome
Classify the final outcome (choose ONE):
- "payment_agreed": citizen agreed to pay immediately or within 24 hours
- "date_committed": citizen committed to a specific future payment date
- "partial_commitment": vague promise to pay without specific date
- "dispute_raised": citizen disputes the assessed amount or claims error
- "refused": citizen outright refused to pay
- "unreachable": wrong number, person not available, no meaningful contact
- "call_dropped": call disconnected unexpectedly before conclusion
- "already_paid": citizen claims they have already made the payment

## 4. consequence_level_reached
What was the highest level of consequences the agent disclosed?
- "none": no consequences mentioned (early disconnect, wrong number, etc.)
- "level_1_financial": DPC charges, penalties, accumulating interest
- "level_2_administrative": blocked permits, NOCs, property transactions frozen
- "level_3_legal": property seizure, sealing, auction notices, Section 128
- "level_4_nuclear": court proceedings, credit impact, permanent ownership record mark

## 5. citizen_response_type
How did the citizen respond to the recovery attempt?
- "immediate_payment": agreed to pay right away
- "requested_time": asked for more time but gave a specific date
- "financial_hardship": cited inability to pay due to financial difficulties
- "disputed_amount": challenged the assessed amount or calculation
- "claimed_paid": said they have already paid
- "abusive": used abusive language, threats, or personal attacks
- "disconnected": hung up or call dropped without resolution
- "cooperative_inquiry": asked about payment methods, schemes, or process

## 6. payment_commitment
What level of payment commitment was obtained?
- "committed_with_date": citizen gave a specific date for payment
- "vague_promise": citizen said they'll pay but no specific date
- "refused": citizen explicitly refused to pay
- "not_discussed": payment commitment not reached (wrong number, early disconnect, etc.)

## 7. proper_protocol_followed
Set to TRUE if the agent:
- Properly greeted and identified themselves as NMMC
- Confirmed the citizen's identity before discussing details
- Cited specific property code, zone, and amount
- Escalated consequences progressively (not dumping all at once)
- Mentioned relief schemes (Abhay Yojana) when appropriate
- Maintained professional composure even if citizen was hostile
- Ended with proper closing

Set to FALSE if the agent skipped critical steps or was unprofessional.

## 8. escalation_required
Set to TRUE if any of these apply:
- Citizen was extremely hostile or abusive (Tier 2-3)
- Citizen threatens legal action against NMMC
- Citizen claims political connections to avoid payment
- Amount is very large and citizen refuses completely
- Citizen raises legitimate dispute that needs officer review
- Multiple failed contact attempts

## 9. compliance_score
Rate from 1 to 10 the likelihood that this citizen will actually pay:
- 1-2: Refused, hostile, zero chance of voluntary payment
- 3-4: Resistant, vague promises, unlikely without enforcement
- 5-6: Uncertain, may pay if followed up, needs reminder
- 7-8: Likely to pay, gave a date, cooperative attitude
- 9-10: Will definitely pay, agreed immediately, already paying

## 10. amount_bracket
Classify the outstanding amount discussed:
- "under_10k": less than Rs. 10,000
- "10k_to_50k": Rs. 10,000 to 50,000
- "50k_to_1_lakh": Rs. 50,000 to 1,00,000
- "1_lakh_to_5_lakh": Rs. 1,00,000 to 5,00,000
- "above_5_lakh": above Rs. 5,00,000
- "not_discussed": amount was not mentioned in the call

---

Be accurate and objective. Base your evaluation only on the transcript content.
Pay special attention to:
- Whether the agent followed the proper escalation ladder
- If the citizen gave a specific payment date or just vague promises
- Whether Abhay Yojana or other relief schemes were mentioned
- If the agent maintained professional composure with hostile citizens
- The actual amount and zone mentioned in the conversation

IMPORTANT: You MUST respond with a valid JSON object containing exactly these 10 fields:
{
  "citizen_sentiment": "cooperative" | "resistant" | "confused" | "hostile" | "indifferent",
  "call_summary": "string",
  "call_outcome": "payment_agreed" | "date_committed" | "partial_commitment" | "dispute_raised" | "refused" | "unreachable" | "call_dropped" | "already_paid",
  "consequence_level_reached": "none" | "level_1_financial" | "level_2_administrative" | "level_3_legal" | "level_4_nuclear",
  "citizen_response_type": "immediate_payment" | "requested_time" | "financial_hardship" | "disputed_amount" | "claimed_paid" | "abusive" | "disconnected" | "cooperative_inquiry",
  "payment_commitment": "committed_with_date" | "vague_promise" | "refused" | "not_discussed",
  "proper_protocol_followed": true | false,
  "escalation_required": true | false,
  "compliance_score": 1-10,
  "amount_bracket": "under_10k" | "10k_to_50k" | "50k_to_1_lakh" | "1_lakh_to_5_lakh" | "above_5_lakh" | "not_discussed"
}

Return ONLY the JSON object, no additional text."""


# JSON Schema for structured output
NMMC_EVALUATION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "nmmc_call_evaluation",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "citizen_sentiment": {
                    "type": "string",
                    "enum": ["cooperative", "resistant", "confused", "hostile", "indifferent"]
                },
                "call_summary": {
                    "type": "string"
                },
                "call_outcome": {
                    "type": "string",
                    "enum": [
                        "payment_agreed", "date_committed", "partial_commitment",
                        "dispute_raised", "refused", "unreachable",
                        "call_dropped", "already_paid"
                    ]
                },
                "consequence_level_reached": {
                    "type": "string",
                    "enum": [
                        "none", "level_1_financial", "level_2_administrative",
                        "level_3_legal", "level_4_nuclear"
                    ]
                },
                "citizen_response_type": {
                    "type": "string",
                    "enum": [
                        "immediate_payment", "requested_time", "financial_hardship",
                        "disputed_amount", "claimed_paid", "abusive",
                        "disconnected", "cooperative_inquiry"
                    ]
                },
                "payment_commitment": {
                    "type": "string",
                    "enum": ["committed_with_date", "vague_promise", "refused", "not_discussed"]
                },
                "proper_protocol_followed": {
                    "type": "boolean"
                },
                "escalation_required": {
                    "type": "boolean"
                },
                "compliance_score": {
                    "type": "integer"
                },
                "amount_bracket": {
                    "type": "string",
                    "enum": [
                        "under_10k", "10k_to_50k", "50k_to_1_lakh",
                        "1_lakh_to_5_lakh", "above_5_lakh", "not_discussed"
                    ]
                }
            },
            "required": [
                "citizen_sentiment", "call_summary", "call_outcome",
                "consequence_level_reached", "citizen_response_type",
                "payment_commitment", "proper_protocol_followed",
                "escalation_required", "compliance_score", "amount_bracket"
            ],
            "additionalProperties": False
        }
    }
}


# Import models
from src.models.domain.nmmc_evaluation import (
    NMMCCallEvaluation,
    CitizenSentiment,
    CallOutcome,
    ConsequenceLevelReached,
    CitizenResponseType,
    PaymentCommitment,
    AmountBracket
)


class NMMCCallEvaluator:
    """Evaluates NMMC Property Tax Recovery call transcripts using Groq LLM with JSON output."""

    # Models supporting JSON output on Groq
    SUPPORTED_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the evaluator.

        Args:
            model: Groq model to use
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = model
        self._client = None

        # Use json_object format for broader compatibility
        self.response_format = {"type": "json_object"}

    @property
    def client(self):
        """Lazy initialization of Groq client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("GROQ_API_KEY not set in environment")
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client

    def evaluate(self, transcript: str) -> Optional[NMMCCallEvaluation]:
        """
        Evaluate a call transcript and return structured metrics.

        Args:
            transcript: The call transcript text

        Returns:
            NMMCCallEvaluation with all metrics, or None if evaluation fails
        """
        if not transcript or len(transcript.strip()) < 20:
            logger.warning("Transcript too short for evaluation")
            return None

        try:
            logger.info(f"🔍 Evaluating NMMC recovery call transcript ({len(transcript)} chars) with {self.model}...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": NMMC_EVALUATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this NMMC property tax recovery call transcript:\n\n{transcript}"}
                ],
                response_format=self.response_format,
                temperature=0.1,
                max_tokens=800
            )

            # Parse the JSON response
            result_text = response.choices[0].message.content
            if not result_text:
                logger.error("Empty response from Groq")
                return None

            result = json.loads(result_text)

            logger.info(f"✅ NMMC Evaluation complete!")
            logger.info(f"   📊 Sentiment: {result.get('citizen_sentiment')}")
            logger.info(f"   📊 Outcome: {result.get('call_outcome')}")
            logger.info(f"   📊 Consequence Level: {result.get('consequence_level_reached')}")
            logger.info(f"   📊 Response Type: {result.get('citizen_response_type')}")
            logger.info(f"   📊 Payment Commitment: {result.get('payment_commitment')}")
            logger.info(f"   📊 Compliance Score: {result.get('compliance_score')}")
            logger.info(f"   📊 Protocol Followed: {result.get('proper_protocol_followed')}")
            logger.info(f"   📊 Escalation: {result.get('escalation_required')}")
            logger.info(f"   📊 Amount Bracket: {result.get('amount_bracket')}")

            # Clamp compliance_score to 1-10
            compliance = result.get("compliance_score", 5)
            if isinstance(compliance, (int, float)):
                compliance = max(1, min(10, int(compliance)))
            else:
                compliance = 5

            # Convert to NMMCCallEvaluation model
            return NMMCCallEvaluation(
                citizen_sentiment=CitizenSentiment(result["citizen_sentiment"]),
                call_summary=result["call_summary"],
                call_outcome=CallOutcome(result["call_outcome"]),
                consequence_level_reached=ConsequenceLevelReached(result["consequence_level_reached"]),
                citizen_response_type=CitizenResponseType(result["citizen_response_type"]),
                payment_commitment=PaymentCommitment(result["payment_commitment"]),
                proper_protocol_followed=result["proper_protocol_followed"],
                escalation_required=result["escalation_required"],
                compliance_score=compliance,
                amount_bracket=AmountBracket(result["amount_bracket"])
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response: {e}")
            return None
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def is_available(self) -> bool:
        """Check if the evaluator is properly configured."""
        return bool(self.api_key)


# Singleton instance
_evaluator: Optional[NMMCCallEvaluator] = None


def get_nmmc_call_evaluator() -> NMMCCallEvaluator:
    """Get the NMMC call evaluator singleton."""
    global _evaluator
    if _evaluator is None:
        _evaluator = NMMCCallEvaluator(
            model="llama-3.3-70b-versatile"
        )
    return _evaluator
