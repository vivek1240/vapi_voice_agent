"""
Vapi Webhook Routes - Receive call events and structured outputs.

Configure this webhook URL in your Vapi dashboard:
https://your-domain.com/webhook/vapi

For local testing with ngrok:
ngrok http 8000
Then use: https://xxxx.ngrok.io/webhook/vapi
"""

import logging
import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from src.services.call_logger import get_call_logger
from src.services.call_evaluator import get_call_evaluator
from src.models.domain.webhook import CallLogEntry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/vapi")
async def vapi_webhook(request: Request):
    """
    Receive webhook events from Vapi.
    
    IMPORTANT: Vapi wraps all data inside a "message" object:
    { "message": { "type": "status-update", "status": "ended", ... } }
    
    Event types (inside message):
    - status-update with status="ended": Call ended, has transcript in artifact
    - end-of-call-report: Final report with structured outputs
    - status-update: Other status changes (ringing, in-progress)
    - transcript: Real-time transcript updates
    """
    try:
        import json
        from datetime import datetime
        
        # Parse the raw JSON payload
        payload_dict = await request.json()
        
        # CRITICAL: Vapi wraps data in "message" - extract it!
        message = payload_dict.get("message", payload_dict)
        
        # Get event type from message (NOT top level)
        event_type = message.get("type", "unknown")
        status = message.get("status", "")
        
        logger.info(f"=== VAPI WEBHOOK ===")
        logger.info(f"Event: {event_type}, Status: {status}")
        
        # Save ALL payloads for debugging - with event type in filename
        debug_dir = os.path.join(os.path.dirname(__file__), "../../../data")
        os.makedirs(debug_dir, exist_ok=True)
        
        # Save latest
        debug_file = os.path.join(debug_dir, "last_webhook.json")
        with open(debug_file, "w") as f:
            json.dump(payload_dict, f, indent=2, default=str)
        
        # Also save by event type for analysis
        event_file = os.path.join(debug_dir, f"webhook_{event_type}_{status}.json")
        with open(event_file, "w") as f:
            json.dump(payload_dict, f, indent=2, default=str)
        logger.info(f"Saved payload to {event_file}")
        
        # Check if this is a call-ended event
        # Vapi sends multiple events:
        # - status-update with status="ended" -> has transcript
        # - end-of-call-report -> has analysis, duration, cost, recording
        is_call_ended = (event_type == "status-update" and status == "ended")
        is_end_report = event_type == "end-of-call-report"
        
        if is_end_report:
            # end-of-call-report has the most complete data - use this!
            logger.info(f"=== END-OF-CALL-REPORT - Full data available ===")
            logger.info(f"=== CALL ENDED - Processing ===")
            
            # Extract data from message wrapper
            artifact = message.get("artifact", {})
            call_data = message.get("call", {})
            
            call_id = call_data.get("id", f"unknown-{datetime.now().timestamp()}")
            logger.info(f"Call ID: {call_id}")
            logger.info(f"Artifact keys: {list(artifact.keys())}")
            
            # Check for structured outputs in artifact
            structured_outputs = artifact.get("structuredOutputs", {})
            if structured_outputs:
                logger.info(f"✅ FOUND structuredOutputs: {list(structured_outputs.keys())}")
            else:
                logger.warning("⚠️ No structuredOutputs in artifact")
            
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
            
            if transcript:
                logger.info(f"Built transcript: {len(transcript)} chars, {len(messages)} messages")
            
            # Run LLM evaluation on transcript using Groq
            parsed_outputs = {}
            
            if transcript:
                try:
                    evaluator = get_call_evaluator()
                    if evaluator.is_available():
                        logger.info("🤖 Running LLM evaluation on transcript...")
                        evaluation = evaluator.evaluate(transcript)
                        
                        if evaluation:
                            parsed_outputs = {
                                "user_sentiment": evaluation.user_sentiment.value,
                                "call_summary": evaluation.call_summary,
                                "query_category": evaluation.query_category.value,
                                "escalation_required": evaluation.escalation_required,
                                "query_resolved": evaluation.query_resolved
                            }
                            logger.info(f"  📊 Sentiment: {evaluation.user_sentiment.value}")
                            logger.info(f"  📊 Category: {evaluation.query_category.value}")
                            logger.info(f"  📊 Resolved: {evaluation.query_resolved}")
                            logger.info(f"  📊 Escalation: {evaluation.escalation_required}")
                        else:
                            logger.warning("LLM evaluation returned None")
                    else:
                        logger.warning("⚠️ GROQ_API_KEY not set - skipping LLM evaluation")
                except Exception as e:
                    logger.error(f"LLM evaluation failed: {e}")
            
            # Fallback: Use Vapi's built-in analysis if LLM eval failed
            if not parsed_outputs.get("call_summary"):
                analysis = message.get("analysis", {})
                if analysis.get("summary"):
                    parsed_outputs["call_summary"] = analysis["summary"]
                    logger.info(f"  📊 Using Vapi fallback summary")
            
            # Log the call to CSV
            try:
                call_logger = get_call_logger()
                
                # Handle boolean conversions for escalation/resolved
                escalation = parsed_outputs.get("escalation_required")
                if isinstance(escalation, str):
                    escalation = escalation.lower() == "true"
                
                resolved = parsed_outputs.get("query_resolved")
                if isinstance(resolved, str):
                    resolved = resolved.lower() == "true"
                
                # Get duration and cost from message level (end-of-call-report)
                duration = message.get("durationSeconds")
                cost = message.get("cost")
                recording_url = artifact.get("recordingUrl") or message.get("recordingUrl")
                
                entry = CallLogEntry(
                    call_id=call_id,
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=duration,
                    user_sentiment=parsed_outputs.get("user_sentiment"),
                    call_summary=parsed_outputs.get("call_summary"),
                    query_category=parsed_outputs.get("query_category"),
                    escalation_required=escalation,
                    query_resolved=resolved,
                    transcript=transcript[:5000] if transcript else None,
                    recording_url=recording_url,
                    cost=cost
                )
                
                logger.info(f"  Duration: {duration}s, Cost: ${cost}")
                
                success = call_logger.log_call(entry)
                if success:
                    logger.info(f"✅ Logged call {call_id} to CSV")
                else:
                    logger.error(f"❌ Failed to log call {call_id}")
                    
            except Exception as e:
                logger.error(f"Error logging call: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            return JSONResponse(
                content={"status": "ok", "message": f"Processed call {call_id}", "logged": True},
                status_code=200
            )
        
        # Handle other status updates
        elif event_type == "status-update":
            call_data = message.get("call", {})
            call_id = call_data.get("id", "unknown")
            logger.info(f"Call {call_id} status: {status}")
        
        # Handle transcript updates
        elif event_type == "transcript":
            pass  # Could log real-time transcripts
        
        # Always return 200 OK
        return JSONResponse(
            content={"status": "ok", "message": f"Received {event_type}", "event_status": status},
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Still return 200 to prevent Vapi from retrying
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=200
        )


@router.get("/call-logs")
async def get_call_logs(limit: int = 50):
    """
    Get recent call logs from the CSV file.
    
    Args:
        limit: Maximum number of entries to return (default 50)
    
    Returns:
        List of recent call log entries with structured outputs
    """
    try:
        call_logger = get_call_logger()
        logs = call_logger.get_recent_calls(limit)
        
        return {
            "status": "ok",
            "count": len(logs),
            "log_file": call_logger.get_log_file_path(),
            "calls": logs
        }
    except Exception as e:
        logger.error(f"Error fetching call logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/call-logs/download")
async def download_call_logs():
    """
    Download the full call logs CSV file.
    """
    from fastapi.responses import FileResponse
    
    call_logger = get_call_logger()
    file_path = call_logger.get_log_file_path()
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No call logs found")
    
    return FileResponse(
        path=file_path,
        filename="call_logs.csv",
        media_type="text/csv"
    )


@router.get("/call-logs/stats")
async def get_call_statistics():
    """
    Get statistics from call logs - sentiment distribution, categories, resolution rates.
    
    Useful for:
    - Monitoring customer satisfaction (sentiment trends)
    - Identifying common pain points (query categories)
    - Measuring AI effectiveness (resolution rate)
    - Tracking escalation needs
    """
    import csv
    from collections import Counter
    
    call_logger = get_call_logger()
    file_path = call_logger.get_log_file_path()
    
    if not os.path.exists(file_path):
        return {
            "status": "ok",
            "total_calls": 0,
            "message": "No call logs yet"
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return {"status": "ok", "total_calls": 0, "message": "No call logs yet"}
        
        # Calculate statistics
        total_calls = len(rows)
        
        # Sentiment distribution
        sentiments = Counter(row.get('user_sentiment', '') for row in rows if row.get('user_sentiment'))
        
        # Query categories
        categories = Counter(row.get('query_category', '') for row in rows if row.get('query_category'))
        
        # Resolution and escalation rates
        resolved_count = sum(1 for row in rows if row.get('query_resolved', '').lower() == 'true')
        escalated_count = sum(1 for row in rows if row.get('escalation_required', '').lower() == 'true')
        
        # Average duration
        durations = [float(row['duration_seconds']) for row in rows if row.get('duration_seconds')]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Total cost
        costs = [float(row['cost']) for row in rows if row.get('cost')]
        total_cost = sum(costs)
        
        return {
            "status": "ok",
            "total_calls": total_calls,
            "sentiment_distribution": dict(sentiments),
            "query_categories": dict(categories),
            "resolution_rate": f"{(resolved_count / total_calls * 100):.1f}%" if total_calls > 0 else "N/A",
            "escalation_rate": f"{(escalated_count / total_calls * 100):.1f}%" if total_calls > 0 else "N/A",
            "resolved_count": resolved_count,
            "escalated_count": escalated_count,
            "average_duration_seconds": round(avg_duration, 1),
            "total_cost_usd": round(total_cost, 4)
        }
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))



