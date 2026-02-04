"""
Best Buy Call Evaluator Service - Evaluates support call transcripts using Groq LLM.

Uses Groq's Structured Outputs feature for guaranteed JSON schema compliance.

Evaluates calls across 10 dimensions:
- Core: sentiment, summary, resolved, escalation
- Domain: issue category, product category, resolution path
- Efficiency: troubleshooting tier, first call resolution
- Quality: proper diagnosis
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# System prompt for the evaluator
BESTBUY_EVALUATOR_SYSTEM_PROMPT = """You are a call quality analyst for Best Buy's Virtual Customer Support.

The Best Buy support agent ("Vivek") helps customers troubleshoot electronics, diagnose issues, and determine whether problems can be resolved over the phone or require in-person service.

Analyze the call transcript and evaluate these 10 dimensions:

## 1. user_sentiment
Assess the customer's emotional state:
- "positive": expressed thanks, satisfaction, relief that issue was resolved
- "neutral": matter-of-fact, just seeking help without strong emotion
- "confused": needed repeated explanations, unsure about steps
- "frustrated": annoyed about the issue, impatient with troubleshooting
- "angry": hostile, upset with Best Buy or product, demanded escalation

## 2. call_summary
Write 2-3 sentences covering:
- What product and issue the customer had
- What troubleshooting was attempted or advice was given
- The outcome (resolved, routed to service, etc.)

## 3. issue_category
Classify the PRIMARY technical issue (choose ONE):
- "power_startup": Won't turn on, boot issues, power problems
- "display_visual": Screen issues, no picture, distorted display
- "audio_issues": No sound, audio quality, speaker/headphone problems
- "wifi_network": Wi-Fi connectivity, network connection issues
- "bluetooth_pairing": Bluetooth connection, device pairing
- "slow_performance": Slow, laggy, freezing, crashing
- "overheating": Device getting hot, thermal issues
- "software_apps": App crashes, software errors, OS problems
- "software_updates": Update failures, update-related issues
- "storage_memory": Storage full, memory issues
- "setup_installation": Initial setup, configuration help
- "physical_damage": Cracked screen, broken parts, water damage
- "hardware_failure": Component failures, hardware malfunctions
- "warranty_claims": Warranty questions, protection plan claims
- "returns_exchange": Return requests, exchanges, refunds
- "general_inquiry": Product questions, how-to, feature questions

## 4. product_category
Identify the product type:
- "smartphone_tablet": Phones, tablets, iPads
- "tv_display": TVs, monitors, projectors
- "computer_laptop": Laptops, desktops, computers
- "audio_equipment": Headphones, speakers, soundbars
- "home_appliance": Washers, refrigerators, kitchen appliances
- "gaming_console": PlayStation, Xbox, Nintendo, gaming devices
- "other_electronics": Smart home, wearables, cameras, etc.

## 5. resolution_path
Determine how the call concluded:
- "virtual_resolved": Issue fully fixed via phone troubleshooting
- "virtual_partial": Some progress, customer to continue later
- "in_person_geeksquad": Routed to Geek Squad service
- "in_person_store": Directed to visit a Best Buy store
- "warranty_claim": Warranty/protection plan process initiated
- "manufacturer_support": Referred to manufacturer's support
- "callback_scheduled": Follow-up callback scheduled
- "unresolved": Issue not resolved, customer left dissatisfied

## 6. troubleshooting_tier
What was the highest level of troubleshooting attempted?
- "tier_1_basic": Restart, cable checks, basic settings
- "tier_2_intermediate": Factory reset, network troubleshooting, drivers
- "tier_3_advanced": Complex diagnostics, in-person assessment needed
- "not_applicable": No troubleshooting (returns, warranty only, etc.)

## 7. first_call_resolution
Set to TRUE if:
- Issue was completely resolved in this single call
- Customer confirmed the fix worked
- No callback, store visit, or follow-up needed

Set to FALSE if:
- Customer needs to visit store or Geek Squad
- Callback was scheduled
- Customer will try steps later
- Issue could not be resolved

## 8. escalation_required
Set to TRUE if any of these apply:
- Customer requested to speak with a manager
- Issue requires specialist beyond standard support
- Customer is extremely upset and needs supervisor
- Technical issue beyond agent's capability
- Store/Geek Squad involvement is mandatory

## 9. query_resolved
Set to TRUE if:
- The customer's question/issue was fully addressed
- Customer expressed satisfaction or understanding
- Conversation reached a natural, positive conclusion

Set to FALSE if:
- Customer still had unresolved questions
- Customer seemed confused or unsatisfied at end
- Call ended abruptly without resolution

## 10. proper_diagnosis
Set to TRUE if:
- Agent correctly identified the issue before troubleshooting
- Agent confirmed the problem with the customer
- Troubleshooting steps matched the actual issue
- Physical damage was correctly identified when present

Set to FALSE if:
- Agent started wrong troubleshooting path
- Misidentified the issue type
- Failed to ask about physical damage when relevant
- Wasted time on irrelevant steps

---

Be accurate and objective. Base your evaluation only on the transcript content.
Pay special attention to:
- Whether physical damage was properly assessed
- If the right resolution path was chosen
- If troubleshooting was efficient and logical
- Customer confirmation of issue resolution

IMPORTANT: You MUST respond with a valid JSON object containing exactly these 10 fields:
{
  "user_sentiment": "positive" | "neutral" | "confused" | "frustrated" | "angry",
  "call_summary": "string",
  "query_resolved": true | false,
  "escalation_required": true | false,
  "issue_category": "power_startup" | "display_visual" | "audio_issues" | "wifi_network" | "bluetooth_pairing" | "slow_performance" | "overheating" | "software_apps" | "software_updates" | "storage_memory" | "setup_installation" | "physical_damage" | "hardware_failure" | "warranty_claims" | "returns_exchange" | "general_inquiry",
  "product_category": "smartphone_tablet" | "tv_display" | "computer_laptop" | "audio_equipment" | "home_appliance" | "gaming_console" | "other_electronics",
  "resolution_path": "virtual_resolved" | "virtual_partial" | "in_person_geeksquad" | "in_person_store" | "warranty_claim" | "manufacturer_support" | "callback_scheduled" | "unresolved",
  "troubleshooting_tier": "tier_1_basic" | "tier_2_intermediate" | "tier_3_advanced" | "not_applicable",
  "first_call_resolution": true | false,
  "proper_diagnosis": true | false
}

Return ONLY the JSON object, no additional text."""


# JSON Schema for structured output
BESTBUY_EVALUATION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "bestbuy_call_evaluation",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "user_sentiment": {
                    "type": "string",
                    "enum": ["positive", "neutral", "confused", "frustrated", "angry"]
                },
                "call_summary": {
                    "type": "string"
                },
                "query_resolved": {
                    "type": "boolean"
                },
                "escalation_required": {
                    "type": "boolean"
                },
                "issue_category": {
                    "type": "string",
                    "enum": [
                        "power_startup", "display_visual", "audio_issues",
                        "wifi_network", "bluetooth_pairing", "slow_performance",
                        "overheating", "software_apps", "software_updates",
                        "storage_memory", "setup_installation", "physical_damage",
                        "hardware_failure", "warranty_claims", "returns_exchange",
                        "general_inquiry"
                    ]
                },
                "product_category": {
                    "type": "string",
                    "enum": [
                        "smartphone_tablet", "tv_display", "computer_laptop",
                        "audio_equipment", "home_appliance", "gaming_console",
                        "other_electronics"
                    ]
                },
                "resolution_path": {
                    "type": "string",
                    "enum": [
                        "virtual_resolved", "virtual_partial", "in_person_geeksquad",
                        "in_person_store", "warranty_claim", "manufacturer_support",
                        "callback_scheduled", "unresolved"
                    ]
                },
                "troubleshooting_tier": {
                    "type": "string",
                    "enum": ["tier_1_basic", "tier_2_intermediate", "tier_3_advanced", "not_applicable"]
                },
                "first_call_resolution": {
                    "type": "boolean"
                },
                "proper_diagnosis": {
                    "type": "boolean"
                }
            },
            "required": [
                "user_sentiment", "call_summary", "query_resolved", "escalation_required",
                "issue_category", "product_category", "resolution_path",
                "troubleshooting_tier", "first_call_resolution", "proper_diagnosis"
            ],
            "additionalProperties": False
        }
    }
}


# Import models
from src.models.domain.bestbuy_evaluation import (
    BestBuyCallEvaluation,
    UserSentiment,
    IssueCategory,
    ProductCategory,
    ResolutionPath,
    TroubleshootingTier
)


class BestBuyCallEvaluator:
    """Evaluates Best Buy support call transcripts using Groq LLM with JSON output."""
    
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
    
    def evaluate(self, transcript: str) -> Optional[BestBuyCallEvaluation]:
        """
        Evaluate a call transcript and return structured metrics.
        
        Args:
            transcript: The call transcript text
            
        Returns:
            BestBuyCallEvaluation with all metrics, or None if evaluation fails
        """
        if not transcript or len(transcript.strip()) < 20:
            logger.warning("Transcript too short for evaluation")
            return None
        
        try:
            logger.info(f"🔍 Evaluating Best Buy call transcript ({len(transcript)} chars) with {self.model}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": BESTBUY_EVALUATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this Best Buy support call transcript:\n\n{transcript}"}
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
            
            logger.info(f"✅ Evaluation complete!")
            logger.info(f"   📊 Sentiment: {result.get('user_sentiment')}")
            logger.info(f"   📊 Issue: {result.get('issue_category')}")
            logger.info(f"   📊 Product: {result.get('product_category')}")
            logger.info(f"   📊 Resolution: {result.get('resolution_path')}")
            logger.info(f"   📊 FCR: {result.get('first_call_resolution')}")
            logger.info(f"   📊 Resolved: {result.get('query_resolved')}")
            
            # Convert to BestBuyCallEvaluation model
            return BestBuyCallEvaluation(
                user_sentiment=UserSentiment(result["user_sentiment"]),
                call_summary=result["call_summary"],
                query_resolved=result["query_resolved"],
                escalation_required=result["escalation_required"],
                issue_category=IssueCategory(result["issue_category"]),
                product_category=ProductCategory(result["product_category"]),
                resolution_path=ResolutionPath(result["resolution_path"]),
                troubleshooting_tier=TroubleshootingTier(result["troubleshooting_tier"]),
                first_call_resolution=result["first_call_resolution"],
                proper_diagnosis=result["proper_diagnosis"]
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
_evaluator: Optional[BestBuyCallEvaluator] = None


def get_bestbuy_call_evaluator() -> BestBuyCallEvaluator:
    """Get the Best Buy call evaluator singleton."""
    global _evaluator
    if _evaluator is None:
        _evaluator = BestBuyCallEvaluator(
            model="llama-3.3-70b-versatile"
        )
    return _evaluator
