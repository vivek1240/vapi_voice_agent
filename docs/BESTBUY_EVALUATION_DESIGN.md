# Best Buy Virtual Customer Support - Call Evaluation System Design

> **Version:** 1.0  
> **Date:** February 2026  
> **Use Case:** Best Buy Virtual Customer Support Agent ("Vivek")  
> **Purpose:** Automated call quality evaluation for electronics troubleshooting support

---

## Table of Contents

1. [Use Case Overview](#use-case-overview)
2. [Evaluation Dimensions](#evaluation-dimensions)
3. [Query Categories](#query-categories)
4. [Product Categories](#product-categories)
5. [Resolution Path Detection](#resolution-path-detection)
6. [Troubleshooting Tier Tracking](#troubleshooting-tier-tracking)
7. [Implementation Specification](#implementation-specification)
8. [System Prompt for Evaluator](#system-prompt-for-evaluator)
9. [Pydantic Models](#pydantic-models)
10. [JSON Schema](#json-schema)
11. [Sample Evaluations](#sample-evaluations)
12. [Dashboard Metrics](#dashboard-metrics)

---

## Use Case Overview

### Agent Profile

| Attribute | Value |
|-----------|-------|
| **Agent Name** | Vivek |
| **Company** | Best Buy |
| **Domain** | Electronics troubleshooting & customer support |
| **Primary Functions** | Product troubleshooting, issue diagnosis, service routing |
| **Communication Style** | Knowledgeable, patient, calm, reassuring, conversational |
| **Key Goal** | Resolve issues virtually when possible, route to in-person when needed |

### Resolution Paths

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          CUSTOMER DESCRIBES ISSUE                                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │    VIRTUAL      │ │   IN-PERSON     │ │    WARRANTY/    │
          │    SUPPORT      │ │    SERVICE      │ │   REPLACEMENT   │
          │                 │ │                 │ │                 │
          │ • Software      │ │ • Physical      │ │ • Defects       │
          │ • Settings      │ │   damage        │ │ • Protection    │
          │ • Connectivity  │ │ • Hardware      │ │   Plan claims   │
          │ • Performance   │ │   failure       │ │ • DOA products  │
          │ • Setup help    │ │ • Complex       │ │                 │
          │                 │ │   repairs       │ │                 │
          └─────────────────┘ └─────────────────┘ └─────────────────┘
                 │                   │                   │
                 ▼                   ▼                   ▼
          [Troubleshoot]      [Geek Squad]        [Claims Process]
```

---

## Evaluation Dimensions

The Best Buy evaluation system tracks **10 dimensions** across 4 categories:

### Category 1: Core Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `user_sentiment` | Enum | Customer's emotional state during the call |
| `call_summary` | String | 2-3 sentence summary of the interaction |
| `query_resolved` | Boolean | Whether the issue was fully resolved |
| `escalation_required` | Boolean | Whether transfer/callback is needed |

### Category 2: Domain-Specific Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `issue_category` | Enum | Type of technical issue (16 categories) |
| `product_category` | Enum | Product type (7 categories) |
| `resolution_path` | Enum | Virtual, In-Person, or Warranty path |

### Category 3: Efficiency Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `troubleshooting_tier` | Enum | Highest tier reached (1-3) |
| `first_call_resolution` | Boolean | Issue resolved in this call without callback/visit |

### Category 4: Quality Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `proper_diagnosis` | Boolean | Agent correctly identified the issue before troubleshooting |

---

## Query Categories

### Issue Categories (16 Total)

```python
class IssueCategory(str, Enum):
    """Technical issue categories for Best Buy support."""
    
    # Power & Startup
    POWER_STARTUP = "power_startup"
    # Won't turn on, won't boot, power button issues
    
    # Display & Visual
    DISPLAY_VISUAL = "display_visual"
    # No picture, distorted image, screen issues, resolution problems
    
    # Audio
    AUDIO_ISSUES = "audio_issues"
    # No sound, distorted audio, speaker/headphone problems
    
    # Connectivity
    WIFI_NETWORK = "wifi_network"
    # Wi-Fi connection issues, network problems
    
    BLUETOOTH_PAIRING = "bluetooth_pairing"
    # Bluetooth connection, device pairing issues
    
    # Performance
    SLOW_PERFORMANCE = "slow_performance"
    # Slow, laggy, freezing, crashing
    
    OVERHEATING = "overheating"
    # Device getting hot, thermal issues
    
    # Software
    SOFTWARE_APPS = "software_apps"
    # App crashes, software errors, OS issues
    
    SOFTWARE_UPDATES = "software_updates"
    # Update problems, failed updates
    
    # Storage
    STORAGE_MEMORY = "storage_memory"
    # Storage full, memory issues, backup problems
    
    # Setup & Configuration
    SETUP_INSTALLATION = "setup_installation"
    # Initial setup, installation help, configuration
    
    # Physical Damage
    PHYSICAL_DAMAGE = "physical_damage"
    # Cracked screen, broken parts, water damage
    
    # Hardware Failure
    HARDWARE_FAILURE = "hardware_failure"
    # Component failures, hardware malfunctions
    
    # Warranty & Returns
    WARRANTY_CLAIMS = "warranty_claims"
    # Warranty questions, protection plan claims
    
    RETURNS_EXCHANGE = "returns_exchange"
    # Return requests, exchanges, refunds
    
    # General
    GENERAL_INQUIRY = "general_inquiry"
    # Product questions, how-to, feature inquiries
```

### Issue Category Descriptions

| Category | Description | Example Customer Statement |
|----------|-------------|---------------------------|
| `power_startup` | Won't turn on, boot issues | "My laptop won't turn on at all" |
| `display_visual` | Screen/display problems | "My TV has a black screen but I hear audio" |
| `audio_issues` | Sound problems | "No sound coming from my soundbar" |
| `wifi_network` | Wi-Fi connectivity | "My smart TV won't connect to Wi-Fi" |
| `bluetooth_pairing` | Bluetooth issues | "My headphones won't pair with my phone" |
| `slow_performance` | Speed/performance | "My computer is running really slow" |
| `overheating` | Thermal issues | "My phone gets really hot" |
| `software_apps` | App/software problems | "This app keeps crashing" |
| `software_updates` | Update issues | "My phone update failed" |
| `storage_memory` | Storage problems | "My tablet says storage is full" |
| `setup_installation` | Setup help | "I just bought a TV and need help setting it up" |
| `physical_damage` | Visible damage | "I dropped my phone and cracked the screen" |
| `hardware_failure` | Hardware malfunction | "My laptop keyboard stopped working" |
| `warranty_claims` | Warranty questions | "Is this covered under my protection plan?" |
| `returns_exchange` | Return requests | "I want to return this product" |
| `general_inquiry` | General questions | "What's the difference between these two models?" |

---

## Product Categories

```python
class ProductCategory(str, Enum):
    """Product categories for Best Buy support."""
    
    SMARTPHONE_TABLET = "smartphone_tablet"
    # iPhones, Android phones, iPads, Android tablets
    
    TV_DISPLAY = "tv_display"
    # Smart TVs, monitors, projectors
    
    COMPUTER_LAPTOP = "computer_laptop"
    # Laptops, desktops, Chromebooks, MacBooks
    
    AUDIO_EQUIPMENT = "audio_equipment"
    # Headphones, speakers, soundbars, home theater
    
    HOME_APPLIANCE = "home_appliance"
    # Washing machines, refrigerators, microwaves, vacuums
    
    GAMING_CONSOLE = "gaming_console"
    # PlayStation, Xbox, Nintendo Switch, gaming PCs
    
    OTHER_ELECTRONICS = "other_electronics"
    # Smart home devices, wearables, cameras, drones
```

---

## Resolution Path Detection

```python
class ResolutionPath(str, Enum):
    """Resolution path determined during the call."""
    
    VIRTUAL_RESOLVED = "virtual_resolved"
    # Issue fully resolved via phone troubleshooting
    
    VIRTUAL_PARTIAL = "virtual_partial"
    # Some progress made, customer to continue independently
    
    IN_PERSON_GEEKSQUAD = "in_person_geeksquad"
    # Routed to Geek Squad in-store or in-home
    
    IN_PERSON_STORE = "in_person_store"
    # Routed to Best Buy store (non-repair)
    
    WARRANTY_CLAIM = "warranty_claim"
    # Directed to warranty/protection plan process
    
    MANUFACTURER_SUPPORT = "manufacturer_support"
    # Referred to manufacturer's direct support
    
    CALLBACK_SCHEDULED = "callback_scheduled"
    # Callback scheduled for later
    
    UNRESOLVED = "unresolved"
    # Customer hung up or issue not addressed
```

### Resolution Path Detection Rules

| Path | Detection Signals |
|------|-------------------|
| `virtual_resolved` | "That fixed it", "It's working now", successful test confirmed |
| `virtual_partial` | Customer will try remaining steps later, gave instructions to follow |
| `in_person_geeksquad` | Physical damage, hardware failure, scheduled Geek Squad visit |
| `in_person_store` | Return/exchange, needs to visit store |
| `warranty_claim` | Protection plan claim initiated, warranty process started |
| `manufacturer_support` | Referred to Apple/Samsung/etc. for warranty/specific support |
| `callback_scheduled` | Customer requested callback, scheduled follow-up |
| `unresolved` | Customer frustrated and left, couldn't determine issue, no resolution |

---

## Troubleshooting Tier Tracking

```python
class TroubleshootingTier(str, Enum):
    """Highest troubleshooting tier reached during the call."""
    
    TIER_1_BASIC = "tier_1_basic"
    # Restart, cable check, basic settings
    # Expected to resolve ~60% of issues
    
    TIER_2_INTERMEDIATE = "tier_2_intermediate"  
    # Network troubleshooting, factory reset, driver updates
    # Expected to resolve additional ~25% of issues
    
    TIER_3_ADVANCED = "tier_3_advanced"
    # Complex diagnostics, requires in-person
    # Remaining ~15% of issues
    
    NOT_APPLICABLE = "not_applicable"
    # No troubleshooting performed (warranty, returns, etc.)
```

### Tier Examples

**Tier 1 - Basic:**
- Power cycling / restart
- Cable and connection checks
- Basic settings adjustment
- Software/app updates
- Simple account sign-in fixes

**Tier 2 - Intermediate:**
- Network/router troubleshooting
- Factory reset guidance
- Driver updates (computers)
- Advanced settings configuration
- Error code interpretation
- Safe mode diagnostics

**Tier 3 - Advanced (In-Person Required):**
- Physical damage assessment
- Hardware component diagnosis
- Data recovery needs
- Complex repairs
- Parts replacement

---

## Implementation Specification

### File Structure

```
src/
├── services/
│   └── bestbuy_call_evaluator.py   # LLM evaluation service
├── models/
│   └── domain/
│       └── bestbuy_evaluation.py   # Pydantic models
└── scripts/
    └── test_bestbuy_evaluator.py   # Local testing script
```

### Environment Variables

```bash
GROQ_API_KEY=your-groq-api-key
```

---

## System Prompt for Evaluator

```python
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
- Customer confirmation of issue resolution"""
```

---

## Pydantic Models

```python
"""
Best Buy Evaluation Models
File: src/models/domain/bestbuy_evaluation.py
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class UserSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"


class IssueCategory(str, Enum):
    POWER_STARTUP = "power_startup"
    DISPLAY_VISUAL = "display_visual"
    AUDIO_ISSUES = "audio_issues"
    WIFI_NETWORK = "wifi_network"
    BLUETOOTH_PAIRING = "bluetooth_pairing"
    SLOW_PERFORMANCE = "slow_performance"
    OVERHEATING = "overheating"
    SOFTWARE_APPS = "software_apps"
    SOFTWARE_UPDATES = "software_updates"
    STORAGE_MEMORY = "storage_memory"
    SETUP_INSTALLATION = "setup_installation"
    PHYSICAL_DAMAGE = "physical_damage"
    HARDWARE_FAILURE = "hardware_failure"
    WARRANTY_CLAIMS = "warranty_claims"
    RETURNS_EXCHANGE = "returns_exchange"
    GENERAL_INQUIRY = "general_inquiry"


class ProductCategory(str, Enum):
    SMARTPHONE_TABLET = "smartphone_tablet"
    TV_DISPLAY = "tv_display"
    COMPUTER_LAPTOP = "computer_laptop"
    AUDIO_EQUIPMENT = "audio_equipment"
    HOME_APPLIANCE = "home_appliance"
    GAMING_CONSOLE = "gaming_console"
    OTHER_ELECTRONICS = "other_electronics"


class ResolutionPath(str, Enum):
    VIRTUAL_RESOLVED = "virtual_resolved"
    VIRTUAL_PARTIAL = "virtual_partial"
    IN_PERSON_GEEKSQUAD = "in_person_geeksquad"
    IN_PERSON_STORE = "in_person_store"
    WARRANTY_CLAIM = "warranty_claim"
    MANUFACTURER_SUPPORT = "manufacturer_support"
    CALLBACK_SCHEDULED = "callback_scheduled"
    UNRESOLVED = "unresolved"


class TroubleshootingTier(str, Enum):
    TIER_1_BASIC = "tier_1_basic"
    TIER_2_INTERMEDIATE = "tier_2_intermediate"
    TIER_3_ADVANCED = "tier_3_advanced"
    NOT_APPLICABLE = "not_applicable"


class BestBuyCallEvaluation(BaseModel):
    """Complete evaluation result for a Best Buy support call."""
    
    # Core Metrics
    user_sentiment: UserSentiment
    call_summary: str
    query_resolved: bool
    escalation_required: bool
    
    # Domain-Specific Metrics
    issue_category: IssueCategory
    product_category: ProductCategory
    resolution_path: ResolutionPath
    
    # Efficiency Metrics
    troubleshooting_tier: TroubleshootingTier
    first_call_resolution: bool
    
    # Quality Metrics
    proper_diagnosis: bool
```

---

## JSON Schema

```python
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
```

---

## Sample Evaluations

### Example 1: Successful TV Troubleshooting

**Transcript:**
```
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: Hi, my Samsung TV suddenly has no picture but I can still hear the audio.

Agent: I'm sorry to hear you're having trouble with your Samsung TV. Let's work together to get this sorted out. First, has the TV been dropped or experienced any physical damage recently?

Customer: No, nothing like that. It was working fine yesterday.

Agent: Good to know. Let's start with some basic troubleshooting. Could you try unplugging the TV from the wall outlet, wait about 30 seconds, and then plug it back in?

Customer: Okay, hold on... [pause] ...alright, I plugged it back in.

Agent: Great. Now turn it on and tell me what you see.

Customer: Still no picture, just black screen with sound.

Agent: Let's try another step. On your Samsung remote, press and hold the power button for about 10 seconds. This does a soft reset.

Customer: Doing that now... oh wait, the picture just came back!

Agent: Excellent! It looks like that did the trick. Is the picture displaying normally now?

Customer: Yes! It's working perfectly. That was easy!

Agent: I'm glad we got that working for you. Just so you know, this sometimes happens when the TV's internal processor gets stuck. If it happens again, try that same reset. Is there anything else I can help you with today?

Customer: No, that's all I needed. Thank you so much!

Agent: You're welcome! Thanks for calling Best Buy - have a great day!
```

**Evaluation:**
```json
{
  "user_sentiment": "positive",
  "call_summary": "Customer's Samsung TV had no picture but audio was working. Agent verified no physical damage, then guided customer through power cycling and a soft reset using the remote. The soft reset resolved the issue, and the customer confirmed the TV is working normally.",
  "query_resolved": true,
  "escalation_required": false,
  "issue_category": "display_visual",
  "product_category": "tv_display",
  "resolution_path": "virtual_resolved",
  "troubleshooting_tier": "tier_1_basic",
  "first_call_resolution": true,
  "proper_diagnosis": true
}
```

---

### Example 2: Physical Damage - Geek Squad Routing

**Transcript:**
```
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: Yeah, I dropped my iPhone and now the screen is cracked and it won't turn on.

Agent: I'm sorry to hear about that. Let me ask a couple questions to understand the situation. When did this happen, and how far did it fall?

Customer: It happened this morning. It fell off my kitchen counter onto the tile floor.

Agent: I see. Is the screen completely shattered or just cracked? And you said it won't power on at all?

Customer: The screen has a big crack across it and some smaller cracks around the edges. Yeah, I've tried the power button and charging it but nothing happens.

Agent: Based on what you're describing - the cracked screen and the fact that it won't power on after the drop - this sounds like it needs hands-on attention that I can't provide over the phone. The impact may have damaged internal components.

Customer: So what do I do?

Agent: Our Geek Squad team can diagnose exactly what's wrong and repair it. Before I recommend next steps, do you have a Best Buy Protection Plan or AppleCare+ on this iPhone?

Customer: I have the Best Buy Protection Plan.

Agent: Great news! Your Protection Plan should cover accidental damage like this. Here's what I recommend: bring your iPhone to the nearest Best Buy with Geek Squad services. They'll do a full diagnostic, and since you have the Protection Plan, the repair costs should be covered, possibly with a deductible depending on your plan. Would you like me to help you find the nearest location?

Customer: Yes, please.

Agent: I can see there's a Best Buy with Geek Squad about 3 miles from your location. They're open today until 9 PM. When you go in, bring the phone, your charger, and your proof of purchase if you have it. They can look up your Protection Plan in the system.

Customer: Okay, I'll head over there today. Thanks for the help.

Agent: I'm sorry we couldn't fix this over the phone, but the Geek Squad team will take great care of you. Is there anything else I can help with?

Customer: No, that's it. Thanks.

Agent: You're welcome. Thanks for calling Best Buy, and I hope the repair goes smoothly!
```

**Evaluation:**
```json
{
  "user_sentiment": "neutral",
  "call_summary": "Customer dropped their iPhone, resulting in a cracked screen and the phone not powering on. Agent correctly identified physical damage requiring in-person service, verified the customer has a Best Buy Protection Plan, and routed them to Geek Squad for repair with clear instructions on what to bring.",
  "query_resolved": true,
  "escalation_required": false,
  "issue_category": "physical_damage",
  "product_category": "smartphone_tablet",
  "resolution_path": "in_person_geeksquad",
  "troubleshooting_tier": "not_applicable",
  "first_call_resolution": false,
  "proper_diagnosis": true
}
```

---

### Example 3: Frustrated Customer - Wi-Fi Issues

**Transcript:**
```
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: I've been trying for two hours to get my new smart TV connected to Wi-Fi and it's not working. This is ridiculous.

Agent: I understand how frustrating that is, especially after spending two hours on it. Let's work through this together and get your TV connected. What brand and model is the TV?

Customer: It's an LG 55-inch. I just bought it from Best Buy last week.

Agent: Thanks. And just to confirm, other devices in your home are connecting to Wi-Fi without problems - like your phone or laptop?

Customer: Yes, everything else works fine. It's just this stupid TV.

Agent: That's actually helpful information - it tells us the issue is likely with the TV's connection to your router, not your internet itself. Let's try a few things. First, on the TV, go to Settings, then Network. What do you see there?

Customer: It shows my network name but says "Not Connected."

Agent: Good. Select your network and try entering the password again. Sometimes a small typo can cause this.

Customer: I've entered it like five times already. I know it's right.

Agent: I believe you. Let's try something else. On your TV, go to Settings, Network, and look for an option that says "Reset Network" or "Reset Network Settings." Do you see that?

Customer: Yeah, I see it.

Agent: Select that and confirm. This will clear any saved network data and let us start fresh.

Customer: Okay, done.

Agent: Now try connecting to your Wi-Fi network again with your password.

Customer: Entering the password now... [pause] ...oh my god, it's connecting. It says "Connected"!

Agent: Excellent! Let's verify it's working. Try opening a streaming app like Netflix or YouTube.

Customer: YouTube is loading... yes! It's working! I can't believe a reset fixed it. I wasted two hours trying everything else.

Agent: I'm glad we got it working. Sometimes the TV's network module just needs a fresh start. Is everything else on the TV working okay?

Customer: Yeah, it all looks good now. Thanks for your patience. I was pretty frustrated.

Agent: No problem at all - I completely understand. Is there anything else I can help you with today?

Customer: No, I'm good. Thanks again!

Agent: You're welcome! Thanks for calling Best Buy - enjoy your new TV!
```

**Evaluation:**
```json
{
  "user_sentiment": "frustrated",
  "call_summary": "Customer was frustrated after spending two hours trying to connect their new LG TV to Wi-Fi. Agent confirmed other devices work, verified the TV sees the network but won't connect, then guided customer through a network settings reset. The reset resolved the issue, and the customer confirmed Wi-Fi is now working.",
  "query_resolved": true,
  "escalation_required": false,
  "issue_category": "wifi_network",
  "product_category": "tv_display",
  "resolution_path": "virtual_resolved",
  "troubleshooting_tier": "tier_2_intermediate",
  "first_call_resolution": true,
  "proper_diagnosis": true
}
```

---

### Example 4: Return Request

**Transcript:**
```
Agent: Thank you for calling Best Buy Customer Support. This is Vivek. How can I help you today?

Customer: I want to return a laptop I bought two weeks ago.

Agent: I'd be happy to help you with that. Could you tell me a bit about why you're returning it? Is there an issue with the laptop, or is it just not what you needed?

Customer: It's just not powerful enough for what I need. The performance is too slow for my video editing software.

Agent: I understand - having the right specs for video editing is important. Since it's been two weeks, you're still within our return window. Most products can be returned within 15 days, or 60 days if you're a Total Tech member. Are you a Total Tech member?

Customer: No, just regular. So 15 days... is today okay?

Agent: Let me check - you said you bought it two weeks ago, so that would be 14 days. You should be just within the return period, but I'd recommend heading to the store today to be safe. Do you have the original receipt and all the accessories that came with the laptop?

Customer: I have the receipt and the box with everything in it.

Agent: Perfect. Just bring all of that to any Best Buy store and they can process the return for you. They'll inspect the laptop to make sure it's in good condition. Since you mentioned it wasn't powerful enough for video editing, would you like me to suggest some laptops that might be better suited for that when you go in?

Customer: Sure, that would help.

Agent: For video editing, I'd recommend looking at laptops with at least 16GB of RAM and a dedicated graphics card. The MacBook Pro, Dell XPS, and ASUS ProArt series are popular choices for video editors. When you're at the store, mention you're doing video editing and the team can help you find the right fit.

Customer: Okay, that's helpful. I'll head to the store now.

Agent: Sounds good. Is there anything else I can help you with today?

Customer: No, that's all. Thanks.

Agent: You're welcome. Thanks for calling Best Buy, and good luck finding the perfect laptop for your video editing!
```

**Evaluation:**
```json
{
  "user_sentiment": "neutral",
  "call_summary": "Customer wanted to return a laptop purchased two weeks ago because it wasn't powerful enough for video editing. Agent confirmed they're within the return window, verified they have the receipt and original packaging, and directed them to the store for the return. Agent also provided helpful suggestions for video editing-capable laptops.",
  "query_resolved": true,
  "escalation_required": false,
  "issue_category": "returns_exchange",
  "product_category": "computer_laptop",
  "resolution_path": "in_person_store",
  "troubleshooting_tier": "not_applicable",
  "first_call_resolution": false,
  "proper_diagnosis": true
}
```

---

## Dashboard Metrics

### Key Performance Indicators (KPIs)

| Metric | Formula | Target |
|--------|---------|--------|
| **First Call Resolution Rate** | FCR_count / total_calls × 100 | > 60% |
| **Virtual Resolution Rate** | virtual_resolved / total_calls × 100 | > 50% |
| **Query Resolution Rate** | resolved_count / total_calls × 100 | > 85% |
| **Customer Satisfaction** | (positive + neutral) / total × 100 | > 80% |
| **Escalation Rate** | escalated / total × 100 | < 10% |
| **Proper Diagnosis Rate** | correct_diagnosis / total × 100 | > 95% |

### Issue Distribution

Track call volume by issue category to identify:
- Most common issues → Knowledge base improvements
- High-escalation issues → Training needs
- Seasonal patterns → Staffing adjustments

### Product Distribution

Monitor which products generate the most support calls:
- Guide inventory decisions
- Identify problematic products
- Target training resources

### Resolution Path Funnel

```
Total Calls
    │
    ├── Virtual Resolved (target: 50%+)
    │       └── First Call Resolution: target 60%+
    │
    ├── Virtual Partial (monitor for follow-up)
    │
    ├── In-Person Geek Squad (physical/hardware)
    │
    ├── In-Person Store (returns/exchanges)
    │
    ├── Warranty Claims
    │
    └── Unresolved (target: <5%)
```

---

## CSV Schema

```python
BESTBUY_CSV_COLUMNS = [
    # Identifiers
    "call_id",
    "timestamp",
    "duration_seconds",
    
    # Core Metrics
    "user_sentiment",
    "call_summary",
    "query_resolved",
    "escalation_required",
    
    # Domain Metrics
    "issue_category",
    "product_category",
    "resolution_path",
    
    # Efficiency Metrics
    "troubleshooting_tier",
    "first_call_resolution",
    
    # Quality Metrics
    "proper_diagnosis",
    
    # Call Data
    "transcript",
    "recording_url",
    "cost"
]
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-04 | Initial design for Best Buy use case |
