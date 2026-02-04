"""
Call Evaluator Service - Runs LLM evaluations on call transcripts using Groq.

Uses Groq's Structured Outputs feature for guaranteed JSON schema compliance.
Based on: https://console.groq.com/docs/structured-outputs

Evaluates calls for:
- user_sentiment: positive | neutral | confused | frustrated
- call_summary: 2-3 sentence summary
- query_category: Classification of the call topic
- escalation_required: Whether human follow-up is needed
- query_resolved: Whether the AI fully resolved the query
"""

import os
import json
import logging
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)


class UserSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"


class QueryCategory(str, Enum):
    ONBOARDING_NAVIGATION = "onboarding_navigation"
    CONSENT_QUESTIONS = "consent_questions"
    BIOMETRIC_CONCERNS = "biometric_concerns"
    SPOT_HEALTH = "spot_health"
    TELEHEALTH = "telehealth"
    PERMISSIONS = "permissions"
    DATA_PRIVACY = "data_privacy"
    TECHNICAL_ISSUE = "technical_issue"
    OUT_OF_SCOPE = "out_of_scope"
    GENERAL_INQUIRY = "general_inquiry"


class CallEvaluation(BaseModel):
    """Result of evaluating a call transcript."""
    user_sentiment: UserSentiment = Field(description="User's emotional state during the call")
    call_summary: str = Field(description="2-3 sentence summary of the call")
    query_category: QueryCategory = Field(description="Primary topic category of the call")
    escalation_required: bool = Field(description="Whether human follow-up is needed")
    query_resolved: bool = Field(description="Whether the AI fully resolved the user's query")


SYSTEM_PROMPT = """You are a call quality analyst for Mercola Health Coach customer support.

Analyze the call transcript and evaluate:

1. **user_sentiment**: User's emotional state
   - "positive": expressed thanks, satisfaction, or relief
   - "neutral": matter-of-fact, no strong emotion
   - "confused": needed clarification, seemed uncertain
   - "frustrated": annoyed, complained, expressed dissatisfaction

2. **call_summary**: 2-3 sentences covering what user asked, how AI responded, and outcome

3. **query_category**: Main topic (choose ONE):
   - "onboarding_navigation": stuck on screens, button issues
   - "consent_questions": EULA, privacy, terms questions
   - "biometric_concerns": face ID, identity verification
   - "spot_health": at-home testing questions
   - "telehealth": results delivery questions
   - "permissions": notifications, microphone access
   - "data_privacy": data sharing, user rights
   - "technical_issue": bugs, crashes, app not working
   - "out_of_scope": medical advice, billing, unrelated
   - "general_inquiry": other app questions

4. **escalation_required**: true if user frustrated, issue unresolved, or needs human support

5. **query_resolved**: true if AI fully answered and user seemed satisfied

Be accurate and objective. Base evaluation only on transcript content."""


class CallEvaluator:
    """Evaluates call transcripts using Groq LLM with Structured Outputs."""
    
    # Models supporting json_schema structured outputs on Groq
    SUPPORTED_MODELS = {
        "strict": [  # Guaranteed schema compliance
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
        ],
        "best_effort": [  # Best-effort schema compliance
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b", 
            "moonshotai/kimi-k2-instruct-0905",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "meta-llama/llama-4-scout-17b-16e-instruct",
        ]
    }
    
    def __init__(self, model: str = "openai/gpt-oss-20b", strict: bool = True):
        """
        Initialize the evaluator.
        
        Args:
            model: Groq model to use (must support structured outputs)
            strict: Use strict mode for guaranteed schema compliance
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = model
        self.strict = strict
        self._client = None
        
        # Build the JSON schema for structured output
        self.response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "call_evaluation",
                "strict": self.strict,
                "schema": {
                    "type": "object",
                    "properties": {
                        "user_sentiment": {
                            "type": "string",
                            "enum": ["positive", "neutral", "confused", "frustrated"]
                        },
                        "call_summary": {
                            "type": "string"
                        },
                        "query_category": {
                            "type": "string",
                            "enum": [
                                "onboarding_navigation",
                                "consent_questions",
                                "biometric_concerns",
                                "spot_health",
                                "telehealth",
                                "permissions",
                                "data_privacy",
                                "technical_issue",
                                "out_of_scope",
                                "general_inquiry"
                            ]
                        },
                        "escalation_required": {
                            "type": "boolean"
                        },
                        "query_resolved": {
                            "type": "boolean"
                        }
                    },
                    "required": [
                        "user_sentiment",
                        "call_summary", 
                        "query_category",
                        "escalation_required",
                        "query_resolved"
                    ],
                    "additionalProperties": False
                }
            }
        }
    
    @property
    def client(self):
        """Lazy initialization of Groq client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("GROQ_API_KEY not set in environment")
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client
    
    def evaluate(self, transcript: str) -> Optional[CallEvaluation]:
        """
        Evaluate a call transcript and return structured metrics.
        
        Args:
            transcript: The call transcript text
            
        Returns:
            CallEvaluation with all metrics, or None if evaluation fails
        """
        if not transcript or len(transcript.strip()) < 20:
            logger.warning("Transcript too short for evaluation")
            return None
        
        try:
            logger.info(f"🤖 Evaluating transcript ({len(transcript)} chars) with {self.model}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this transcript:\n\n{transcript}"}
                ],
                response_format=self.response_format,
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content
            if not result_text:
                logger.error("Empty response from Groq")
                return None
            
            result = json.loads(result_text)
            logger.info(f"✅ Evaluation complete!")
            logger.info(f"   Sentiment: {result.get('user_sentiment')}")
            logger.info(f"   Category: {result.get('query_category')}")
            logger.info(f"   Resolved: {result.get('query_resolved')}")
            
            # Convert to CallEvaluation model
            return CallEvaluation(
                user_sentiment=UserSentiment(result["user_sentiment"]),
                call_summary=result["call_summary"],
                query_category=QueryCategory(result["query_category"]),
                escalation_required=result["escalation_required"],
                query_resolved=result["query_resolved"]
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response: {e}")
            return None
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if the evaluator is properly configured."""
        return bool(self.api_key)


# Singleton instance
_evaluator: Optional[CallEvaluator] = None


def get_call_evaluator() -> CallEvaluator:
    """Get the call evaluator singleton."""
    global _evaluator
    if _evaluator is None:
        # Use openai/gpt-oss-20b with strict mode for guaranteed schema compliance
        _evaluator = CallEvaluator(
            model="openai/gpt-oss-20b",
            strict=True
        )
    return _evaluator
