"""
Best Buy Call Evaluation Models

Pydantic models for evaluating Best Buy Virtual Customer Support calls.
Tracks 10 dimensions across core, domain, efficiency, and quality metrics.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class UserSentiment(str, Enum):
    """Customer sentiment classification for Best Buy support."""
    POSITIVE = "positive"      # Thanks, satisfaction, relief
    NEUTRAL = "neutral"        # Matter-of-fact, just seeking help
    CONFUSED = "confused"      # Needed repeated explanations
    FRUSTRATED = "frustrated"  # Annoyed about issue, impatient
    ANGRY = "angry"            # Hostile, upset, demanded escalation


class IssueCategory(str, Enum):
    """Technical issue categories for Best Buy support."""
    
    # Power & Startup
    POWER_STARTUP = "power_startup"
    
    # Display & Visual
    DISPLAY_VISUAL = "display_visual"
    
    # Audio
    AUDIO_ISSUES = "audio_issues"
    
    # Connectivity
    WIFI_NETWORK = "wifi_network"
    BLUETOOTH_PAIRING = "bluetooth_pairing"
    
    # Performance
    SLOW_PERFORMANCE = "slow_performance"
    OVERHEATING = "overheating"
    
    # Software
    SOFTWARE_APPS = "software_apps"
    SOFTWARE_UPDATES = "software_updates"
    
    # Storage
    STORAGE_MEMORY = "storage_memory"
    
    # Setup & Configuration
    SETUP_INSTALLATION = "setup_installation"
    
    # Physical/Hardware
    PHYSICAL_DAMAGE = "physical_damage"
    HARDWARE_FAILURE = "hardware_failure"
    
    # Warranty & Returns
    WARRANTY_CLAIMS = "warranty_claims"
    RETURNS_EXCHANGE = "returns_exchange"
    
    # General
    GENERAL_INQUIRY = "general_inquiry"


class ProductCategory(str, Enum):
    """Product categories for Best Buy support."""
    SMARTPHONE_TABLET = "smartphone_tablet"
    TV_DISPLAY = "tv_display"
    COMPUTER_LAPTOP = "computer_laptop"
    AUDIO_EQUIPMENT = "audio_equipment"
    HOME_APPLIANCE = "home_appliance"
    GAMING_CONSOLE = "gaming_console"
    OTHER_ELECTRONICS = "other_electronics"


class ResolutionPath(str, Enum):
    """Resolution path determined during the call."""
    VIRTUAL_RESOLVED = "virtual_resolved"        # Fixed via phone
    VIRTUAL_PARTIAL = "virtual_partial"          # Some progress, continue later
    IN_PERSON_GEEKSQUAD = "in_person_geeksquad"  # Routed to Geek Squad
    IN_PERSON_STORE = "in_person_store"          # Visit store (non-repair)
    WARRANTY_CLAIM = "warranty_claim"            # Warranty process
    MANUFACTURER_SUPPORT = "manufacturer_support" # Referred to manufacturer
    CALLBACK_SCHEDULED = "callback_scheduled"     # Callback scheduled
    UNRESOLVED = "unresolved"                    # Not resolved


class TroubleshootingTier(str, Enum):
    """Highest troubleshooting tier reached."""
    TIER_1_BASIC = "tier_1_basic"              # Restart, cables, basic settings
    TIER_2_INTERMEDIATE = "tier_2_intermediate" # Factory reset, network, drivers
    TIER_3_ADVANCED = "tier_3_advanced"        # Complex diagnostics, in-person
    NOT_APPLICABLE = "not_applicable"          # No troubleshooting (returns, etc.)


class BestBuyCallEvaluation(BaseModel):
    """
    Complete evaluation result for a Best Buy support call.
    
    10 evaluation dimensions across 4 categories:
    - Core Metrics: sentiment, summary, resolved, escalation
    - Domain Metrics: issue category, product category, resolution path
    - Efficiency Metrics: troubleshooting tier, first call resolution
    - Quality Metrics: proper diagnosis
    """
    
    # Core Metrics
    user_sentiment: UserSentiment = Field(
        description="Customer's emotional state during the call"
    )
    call_summary: str = Field(
        description="2-3 sentence summary of the call"
    )
    query_resolved: bool = Field(
        description="Whether the customer's issue/question was fully addressed"
    )
    escalation_required: bool = Field(
        description="Whether transfer or manager involvement is needed"
    )
    
    # Domain-Specific Metrics
    issue_category: IssueCategory = Field(
        description="Primary technical issue category"
    )
    product_category: ProductCategory = Field(
        description="Type of product the customer has"
    )
    resolution_path: ResolutionPath = Field(
        description="How the call was resolved/routed"
    )
    
    # Efficiency Metrics
    troubleshooting_tier: TroubleshootingTier = Field(
        description="Highest troubleshooting tier reached"
    )
    first_call_resolution: bool = Field(
        description="Issue completely resolved in this single call"
    )
    
    # Quality Metrics
    proper_diagnosis: bool = Field(
        description="Agent correctly identified the issue before troubleshooting"
    )


class BestBuyCallLogEntry(BaseModel):
    """Entry for CSV logging - Best Buy specific."""
    call_id: str
    timestamp: str
    duration_seconds: Optional[float] = None
    
    # Core Metrics
    user_sentiment: Optional[str] = None
    call_summary: Optional[str] = None
    query_resolved: Optional[bool] = None
    escalation_required: Optional[bool] = None
    
    # Domain Metrics
    issue_category: Optional[str] = None
    product_category: Optional[str] = None
    resolution_path: Optional[str] = None
    
    # Efficiency Metrics
    troubleshooting_tier: Optional[str] = None
    first_call_resolution: Optional[bool] = None
    
    # Quality Metrics
    proper_diagnosis: Optional[bool] = None
    
    # Call Data
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    cost: Optional[float] = None
