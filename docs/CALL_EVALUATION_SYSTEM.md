# Voice AI Call Evaluation System Documentation

> **Version:** 1.0  
> **Last Updated:** January 2026  
> **Purpose:** Comprehensive guide for implementing automated call quality evaluation in Voice AI applications

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Evaluation Metrics](#evaluation-metrics)
4. [Components](#components)
   - [Call Evaluator (LLM-based)](#1-call-evaluator-llm-based)
   - [Call Logger](#2-call-logger)
   - [Webhook Handler](#3-webhook-handler)
   - [Domain Models](#4-domain-models)
5. [API Endpoints](#api-endpoints)
6. [Data Flow](#data-flow)
7. [Integration Guide](#integration-guide)
8. [Configuration](#configuration)
9. [Sample Outputs](#sample-outputs)
10. [Customization Guide](#customization-guide)

---

## Overview

This evaluation system provides **automated quality assessment** for Voice AI calls by:

1. **Receiving webhook events** from Vapi (or similar voice AI platforms) when calls end
2. **Extracting transcripts** from call artifacts
3. **Running LLM evaluation** using Groq's Structured Outputs feature
4. **Logging results** to CSV for analysis and reporting
5. **Providing API endpoints** for statistics and call log retrieval

### Key Features

- ✅ **Real-time evaluation** triggered automatically on call end
- ✅ **Structured JSON output** with guaranteed schema compliance
- ✅ **5 evaluation dimensions**: sentiment, summary, category, escalation, resolution
- ✅ **CSV-based storage** for easy analysis in Excel/Google Sheets
- ✅ **Statistics API** for monitoring dashboards
- ✅ **Fallback mechanisms** for graceful degradation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VOICE AI PLATFORM (Vapi)                        │
│                                                                              │
│    Call Started → Conversation → Call Ended → Webhook Triggered              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WEBHOOK ENDPOINT                                │
│                           POST /webhook/vapi                                 │
│                                                                              │
│  1. Receive end-of-call-report webhook                                       │
│  2. Extract transcript from artifact.messages                                │
│  3. Parse call metadata (duration, cost, recording URL)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CALL EVALUATOR                                  │
│                         (Groq LLM + Structured Outputs)                      │
│                                                                              │
│  Input: Call transcript                                                      │
│  Output: CallEvaluation {                                                    │
│      user_sentiment: positive | neutral | confused | frustrated              │
│      call_summary: "2-3 sentence summary"                                    │
│      query_category: "classification"                                        │
│      escalation_required: true | false                                       │
│      query_resolved: true | false                                            │
│  }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CALL LOGGER                                     │
│                           (CSV File Storage)                                 │
│                                                                              │
│  Stores: call_id, timestamp, duration, sentiment, summary, category,         │
│          escalation, resolved, transcript, recording_url, cost               │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API ENDPOINTS                                   │
│                                                                              │
│  GET /webhook/call-logs          → List recent calls                         │
│  GET /webhook/call-logs/stats    → Aggregated statistics                     │
│  GET /webhook/call-logs/download → Download CSV file                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Evaluation Metrics

The system evaluates each call on **5 dimensions**:

### 1. User Sentiment

Assesses the user's emotional state during the call.

| Value | Description | Detection Signals |
|-------|-------------|-------------------|
| `positive` | User expressed thanks, satisfaction, or relief | "thank you", "that's helpful", "great" |
| `neutral` | Matter-of-fact interaction, no strong emotion | Straightforward Q&A |
| `confused` | User needed clarification, seemed uncertain | "I don't understand", "what do you mean" |
| `frustrated` | User expressed annoyance or dissatisfaction | "this is frustrating", complaints |

### 2. Call Summary

A **2-3 sentence summary** covering:
- What the user asked
- How the AI responded
- The outcome of the conversation

### 3. Query Category

Classifies the primary topic for **trend analysis**. Categories are customizable per application:

| Category | Description |
|----------|-------------|
| `onboarding_navigation` | Stuck on screens, button issues |
| `consent_questions` | EULA, privacy, terms questions |
| `biometric_concerns` | Face ID, identity verification |
| `spot_health` | At-home testing questions |
| `telehealth` | Results delivery questions |
| `permissions` | Notifications, microphone access |
| `data_privacy` | Data sharing, user rights |
| `technical_issue` | Bugs, crashes, app not working |
| `out_of_scope` | Medical advice, billing, unrelated |
| `general_inquiry` | Other app questions |

### 4. Escalation Required

Boolean flag indicating if **human follow-up is needed**:
- `true`: User frustrated, issue unresolved, needs human support
- `false`: AI handled the query satisfactorily

### 5. Query Resolved

Boolean flag indicating if the **AI fully resolved the query**:
- `true`: AI answered completely, user seemed satisfied
- `false`: Query left unresolved or partially addressed

---

## Components

### 1. Call Evaluator (LLM-based)

**File:** `src/services/call_evaluator.py`

The evaluator uses **Groq's Structured Outputs** feature to guarantee JSON schema compliance.

#### Key Classes

```python
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
    user_sentiment: UserSentiment
    call_summary: str
    query_category: QueryCategory
    escalation_required: bool
    query_resolved: bool
```

#### Evaluator Implementation

```python
class CallEvaluator:
    """Evaluates call transcripts using Groq LLM with Structured Outputs."""
    
    SUPPORTED_MODELS = {
        "strict": [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
        ],
        "best_effort": [
            "moonshotai/kimi-k2-instruct-0905",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "meta-llama/llama-4-scout-17b-16e-instruct",
        ]
    }
    
    def __init__(self, model: str = "openai/gpt-oss-20b", strict: bool = True):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = model
        self.strict = strict
        
        # JSON Schema for structured output
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
                        "call_summary": {"type": "string"},
                        "query_category": {
                            "type": "string",
                            "enum": [/* category values */]
                        },
                        "escalation_required": {"type": "boolean"},
                        "query_resolved": {"type": "boolean"}
                    },
                    "required": [
                        "user_sentiment", "call_summary", "query_category",
                        "escalation_required", "query_resolved"
                    ],
                    "additionalProperties": False
                }
            }
        }
    
    def evaluate(self, transcript: str) -> Optional[CallEvaluation]:
        """Evaluate a call transcript and return structured metrics."""
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
        
        result = json.loads(response.choices[0].message.content)
        return CallEvaluation(**result)
```

#### System Prompt for Evaluation

```python
SYSTEM_PROMPT = """You are a call quality analyst for [Your App] customer support.

Analyze the call transcript and evaluate:

1. **user_sentiment**: User's emotional state
   - "positive": expressed thanks, satisfaction, or relief
   - "neutral": matter-of-fact, no strong emotion
   - "confused": needed clarification, seemed uncertain
   - "frustrated": annoyed, complained, expressed dissatisfaction

2. **call_summary**: 2-3 sentences covering what user asked, how AI responded, and outcome

3. **query_category**: Main topic (choose ONE):
   - [Your categories here]

4. **escalation_required**: true if user frustrated, issue unresolved, or needs human support

5. **query_resolved**: true if AI fully answered and user seemed satisfied

Be accurate and objective. Base evaluation only on transcript content."""
```

---

### 2. Call Logger

**File:** `src/services/call_logger.py`

Handles CSV-based storage of call data and structured outputs.

#### CSV Schema

```python
CSV_COLUMNS = [
    "call_id",              # Unique call identifier
    "timestamp",            # When the call ended (ISO format)
    "duration_seconds",     # Call duration in seconds
    "user_sentiment",       # positive | neutral | confused | frustrated
    "call_summary",         # 2-3 sentence summary
    "query_category",       # Category for trend analysis
    "escalation_required",  # true/false - needs human follow-up
    "query_resolved",       # true/false - AI resolved query
    "transcript",           # Full call transcript (truncated to 5000 chars)
    "recording_url",        # URL to call recording
    "cost"                  # Call cost in USD
]
```

#### CallLogger Class

```python
class CallLogger:
    """Service to log call data to CSV file."""
    
    def __init__(self):
        self._ensure_data_dir()
        self._ensure_csv_headers()
    
    def log_call(self, entry: CallLogEntry) -> bool:
        """Append a call log entry to the CSV file."""
        with open(CALL_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            row = {
                "call_id": entry.call_id,
                "timestamp": entry.timestamp,
                "duration_seconds": entry.duration_seconds or "",
                "user_sentiment": entry.user_sentiment or "",
                "call_summary": self._clean_text(entry.call_summary),
                "query_category": entry.query_category or "",
                "escalation_required": str(entry.escalation_required) if entry.escalation_required is not None else "",
                "query_resolved": str(entry.query_resolved) if entry.query_resolved is not None else "",
                "transcript": self._clean_text(entry.transcript),
                "recording_url": entry.recording_url or "",
                "cost": entry.cost or ""
            }
            writer.writerow(row)
        return True
    
    def get_recent_calls(self, limit: int = 10) -> list[dict]:
        """Get the most recent call logs."""
        with open(CALL_LOG_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        return rows[-limit:] if len(rows) > limit else rows
```

---

### 3. Webhook Handler

**File:** `src/api/routes/webhook.py`

Receives webhooks from Vapi and orchestrates evaluation + logging.

#### Webhook Endpoint

```python
@router.post("/vapi")
async def vapi_webhook(request: Request):
    """
    Receive webhook events from Vapi.
    
    IMPORTANT: Vapi wraps all data inside a "message" object:
    { "message": { "type": "status-update", "status": "ended", ... } }
    """
    payload_dict = await request.json()
    
    # Extract message from wrapper
    message = payload_dict.get("message", payload_dict)
    event_type = message.get("type", "unknown")
    
    if event_type == "end-of-call-report":
        # Extract call data
        artifact = message.get("artifact", {})
        call_data = message.get("call", {})
        call_id = call_data.get("id")
        
        # Build transcript from messages array
        messages = artifact.get("messages", [])
        transcript_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("message", "")
            if role in ["user", "bot", "assistant"] and content:
                speaker = "User" if role == "user" else "Assistant"
                transcript_parts.append(f"{speaker}: {content}")
        transcript = "\n".join(transcript_parts)
        
        # Run LLM evaluation
        evaluator = get_call_evaluator()
        if evaluator.is_available() and transcript:
            evaluation = evaluator.evaluate(transcript)
            if evaluation:
                parsed_outputs = {
                    "user_sentiment": evaluation.user_sentiment.value,
                    "call_summary": evaluation.call_summary,
                    "query_category": evaluation.query_category.value,
                    "escalation_required": evaluation.escalation_required,
                    "query_resolved": evaluation.query_resolved
                }
        
        # Log to CSV
        call_logger = get_call_logger()
        entry = CallLogEntry(
            call_id=call_id,
            timestamp=datetime.now().isoformat(),
            duration_seconds=message.get("durationSeconds"),
            user_sentiment=parsed_outputs.get("user_sentiment"),
            call_summary=parsed_outputs.get("call_summary"),
            query_category=parsed_outputs.get("query_category"),
            escalation_required=parsed_outputs.get("escalation_required"),
            query_resolved=parsed_outputs.get("query_resolved"),
            transcript=transcript[:5000],
            recording_url=artifact.get("recordingUrl"),
            cost=message.get("cost")
        )
        call_logger.log_call(entry)
    
    return JSONResponse(content={"status": "ok"}, status_code=200)
```

---

### 4. Domain Models

**File:** `src/models/domain/webhook.py`

Pydantic models for type-safe data handling.

```python
class StructuredOutputs(BaseModel):
    """Parsed structured outputs from call conversations."""
    user_sentiment: Optional[str] = None
    call_summary: Optional[str] = None
    query_category: Optional[str] = None
    escalation_required: Optional[bool] = None
    query_resolved: Optional[bool] = None


class CallArtifact(BaseModel):
    """Call artifact containing structured outputs and other data."""
    structuredOutputs: Optional[Dict[str, Any]] = None
    transcript: Optional[str] = None
    recordingUrl: Optional[str] = None
    messages: Optional[list] = None


class VapiCall(BaseModel):
    """Vapi call object in webhook payload."""
    id: str
    status: Optional[str] = None
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    cost: Optional[float] = None
    artifact: Optional[CallArtifact] = None


class VapiWebhookPayload(BaseModel):
    """Vapi webhook payload structure."""
    type: str
    call: Optional[VapiCall] = None
    transcript: Optional[str] = None
    recordingUrl: Optional[str] = None


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
```

---

## API Endpoints

### 1. Get Recent Call Logs

```
GET /webhook/call-logs?limit=50
```

**Response:**
```json
{
  "status": "ok",
  "count": 10,
  "log_file": "/path/to/call_logs.csv",
  "calls": [
    {
      "call_id": "019b6422-a26d-7668-b3a7-eb90959af715",
      "timestamp": "2025-12-28T14:18:38.400782",
      "duration_seconds": "158.557",
      "user_sentiment": "positive",
      "call_summary": "The user asked about Spot Health...",
      "query_category": "spot_health",
      "escalation_required": "False",
      "query_resolved": "True",
      "transcript": "Assistant: Hi there...",
      "recording_url": "https://storage.vapi.ai/...",
      "cost": "0.2728"
    }
  ]
}
```

### 2. Get Call Statistics

```
GET /webhook/call-logs/stats
```

**Response:**
```json
{
  "status": "ok",
  "total_calls": 11,
  "sentiment_distribution": {
    "positive": 1,
    "frustrated": 2
  },
  "query_categories": {
    "spot_health": 3,
    "telehealth": 1,
    "out_of_scope": 2,
    "general_inquiry": 1
  },
  "resolution_rate": "27.3%",
  "escalation_rate": "18.2%",
  "resolved_count": 3,
  "escalated_count": 2,
  "average_duration_seconds": 87.7,
  "total_cost_usd": 1.2848
}
```

### 3. Download CSV File

```
GET /webhook/call-logs/download
```

Returns the full CSV file as a download.

---

## Data Flow

### End-to-End Process

1. **Call Ends** → Vapi sends `end-of-call-report` webhook
2. **Webhook Received** → Extract `message` from wrapper
3. **Parse Artifact** → Get messages array, build transcript
4. **LLM Evaluation** → Send transcript to Groq with structured output schema
5. **Parse Response** → Convert JSON to CallEvaluation model
6. **Log to CSV** → Append entry with all fields
7. **Return 200** → Always return OK to prevent retries

### Vapi Webhook Payload Structure

```json
{
  "message": {
    "type": "end-of-call-report",
    "analysis": {
      "summary": "AI-generated summary",
      "successEvaluation": "false"
    },
    "artifact": {
      "messages": [
        { "role": "bot", "message": "Hi there..." },
        { "role": "user", "message": "Hello..." }
      ],
      "transcript": "AI: Hi there...\nUser: Hello...",
      "recordingUrl": "https://storage.vapi.ai/..."
    },
    "call": {
      "id": "019b6493-15e7-7995-8abc-4f5b5f18b424"
    },
    "durationSeconds": 60.558,
    "cost": 0.1199
  }
}
```

---

## Integration Guide

### Step 1: Install Dependencies

```bash
pip install fastapi pydantic groq uvicorn
```

Or add to `requirements.txt`:
```
fastapi==0.115.12
pydantic==2.11.4
groq==1.0.0
uvicorn==0.34.2
```

### Step 2: Set Environment Variables

```bash
export GROQ_API_KEY="your-groq-api-key"
```

### Step 3: Copy Core Files

Copy these files to your project:

```
src/
├── services/
│   ├── call_evaluator.py    # LLM evaluation logic
│   └── call_logger.py       # CSV logging
├── models/
│   └── domain/
│       └── webhook.py       # Pydantic models
└── api/
    └── routes/
        └── webhook.py       # Webhook endpoint
```

### Step 4: Customize Categories

Edit `call_evaluator.py` to match your application's categories:

```python
class QueryCategory(str, Enum):
    # Add your own categories
    ACCOUNT_ISSUES = "account_issues"
    BILLING = "billing"
    TECHNICAL_SUPPORT = "technical_support"
    PRODUCT_INQUIRY = "product_inquiry"
    FEEDBACK = "feedback"
    OTHER = "other"
```

### Step 5: Update System Prompt

Customize the evaluation prompt for your domain:

```python
SYSTEM_PROMPT = """You are a call quality analyst for [YOUR COMPANY] customer support.

Analyze the call transcript and evaluate:

1. **user_sentiment**: User's emotional state
   - "positive": expressed thanks, satisfaction, or relief
   - "neutral": matter-of-fact, no strong emotion
   - "confused": needed clarification, seemed uncertain
   - "frustrated": annoyed, complained, expressed dissatisfaction

2. **call_summary**: 2-3 sentences covering what user asked, how AI responded, and outcome

3. **query_category**: Main topic (choose ONE):
   - "account_issues": Login, password, account settings
   - "billing": Payments, invoices, refunds
   - "technical_support": App bugs, errors, how-to questions
   - "product_inquiry": Features, pricing, availability
   - "feedback": Suggestions, compliments, complaints
   - "other": Anything else

4. **escalation_required**: true if user frustrated, issue unresolved, or needs human support

5. **query_resolved**: true if AI fully answered and user seemed satisfied

Be accurate and objective. Base evaluation only on transcript content."""
```

### Step 6: Configure Vapi Webhook

In your Vapi Dashboard:
1. Go to Assistant Settings → Server URL
2. Set URL to: `https://your-domain.com/webhook/vapi`
3. Enable `end-of-call-report` in server messages

### Step 7: Test Locally with ngrok

```bash
# Start your FastAPI server
uvicorn src.main:app --reload --port 8000

# In another terminal, start ngrok
ngrok http 8000

# Copy the ngrok URL to Vapi Dashboard
# e.g., https://xxxx.ngrok.io/webhook/vapi
```

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | API key for Groq LLM | Yes |

### Call Evaluator Settings

```python
# Default configuration
evaluator = CallEvaluator(
    model="openai/gpt-oss-20b",  # Fast, cost-effective
    strict=True                   # Guaranteed schema compliance
)

# Alternative: More powerful model
evaluator = CallEvaluator(
    model="openai/gpt-oss-120b",  # Higher quality
    strict=True
)
```

### Supported Groq Models

**Strict Mode (Guaranteed Schema):**
- `openai/gpt-oss-20b` - Fast, recommended for production
- `openai/gpt-oss-120b` - Higher quality, slower

**Best-Effort Mode:**
- `moonshotai/kimi-k2-instruct-0905`
- `meta-llama/llama-4-maverick-17b-128e-instruct`
- `meta-llama/llama-4-scout-17b-16e-instruct`

---

## Sample Outputs

### Positive Resolution Example

**Input Transcript:**
```
User: I'm trying to understand the Spot Health feature.
Assistant: Spot Health is an optional at-home testing service...
User: That makes sense. Thank you so much!
Assistant: You're welcome! Take care.
```

**Evaluation Output:**
```json
{
  "user_sentiment": "positive",
  "call_summary": "The user asked about the Spot Health feature during onboarding. The assistant explained that Spot Health is an optional at-home testing service, requires consent, is not available in New York, and does not create a doctor-patient relationship. The user thanked the assistant and indicated they were satisfied.",
  "query_category": "spot_health",
  "escalation_required": false,
  "query_resolved": true
}
```

### Frustrated User Example

**Input Transcript:**
```
User: I don't like you. I'm going. Bye bye.
Assistant: Thanks for calling. Take care.
```

**Evaluation Output:**
```json
{
  "user_sentiment": "frustrated",
  "call_summary": "User greeted the assistant, the assistant offered help, but the user expressed dislike and ended the call without asking a question.",
  "query_category": "out_of_scope",
  "escalation_required": true,
  "query_resolved": false
}
```

---

## Customization Guide

### Adding New Metrics

1. **Update the Pydantic model:**
```python
class CallEvaluation(BaseModel):
    user_sentiment: UserSentiment
    call_summary: str
    query_category: QueryCategory
    escalation_required: bool
    query_resolved: bool
    # Add new fields
    call_quality_score: int  # 1-10 rating
    key_topics: list[str]    # List of discussed topics
```

2. **Update the JSON schema:**
```python
self.response_format = {
    "type": "json_schema",
    "json_schema": {
        "schema": {
            "properties": {
                # ... existing properties ...
                "call_quality_score": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10
                },
                "key_topics": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    }
}
```

3. **Update the system prompt:**
```python
SYSTEM_PROMPT = """...
6. **call_quality_score**: Rate the overall call quality from 1-10
7. **key_topics**: List 2-3 main topics discussed
..."""
```

### Alternative LLM Providers

You can replace Groq with other providers that support structured outputs:

**OpenAI:**
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    response_format={"type": "json_schema", "json_schema": {...}}
)
```

**Anthropic (with tool use):**
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
# Use tool_use for structured outputs
```

### Database Storage (Alternative to CSV)

Replace CSV with SQLite or PostgreSQL:

```python
from sqlalchemy import create_engine, Column, String, Float, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(String, primary_key=True)
    timestamp = Column(String)
    duration_seconds = Column(Float)
    user_sentiment = Column(String)
    call_summary = Column(String)
    query_category = Column(String)
    escalation_required = Column(Boolean)
    query_resolved = Column(Boolean)
    transcript = Column(String)
    recording_url = Column(String)
    cost = Column(Float)
```

---

## Troubleshooting

### Common Issues

**1. Empty evaluations:**
- Check `GROQ_API_KEY` is set
- Verify transcript length > 20 characters
- Check Groq API status

**2. Missing structured outputs:**
- Ensure Vapi sends `end-of-call-report` event
- Verify webhook URL is correct
- Check server logs for parsing errors

**3. Webhook not triggering:**
- Verify ngrok is running (for local testing)
- Check Vapi dashboard for failed webhooks
- Ensure server returns 200 OK

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

Save webhooks for debugging:

```python
# In webhook handler
debug_file = f"data/webhook_{event_type}_{timestamp}.json"
with open(debug_file, "w") as f:
    json.dump(payload_dict, f, indent=2)
```

---

## Best Practices

1. **Always return 200 OK** from webhooks to prevent retries
2. **Use strict mode** for guaranteed schema compliance
3. **Truncate transcripts** to avoid token limits (5000 chars recommended)
4. **Log raw webhooks** for debugging during development
5. **Monitor costs** - track Groq API usage in production
6. **Set up alerts** for high escalation rates
7. **Review evaluations** periodically for accuracy
8. **Version your prompts** to track changes over time

---

## License

This evaluation system was built for the Mercola Health Coach Voice AI project and is available for reuse in other Voice AI applications.
