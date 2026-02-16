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
from src.services.nmmc_call_evaluator import get_nmmc_call_evaluator
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
                    speaker = "Citizen" if role == "user" else "Agent"
                    transcript_parts.append(f"{speaker}: {content}")
            transcript = "\n".join(transcript_parts)
            
            if transcript:
                logger.info(f"Built transcript: {len(transcript)} chars, {len(messages)} messages")
            
            # Run NMMC LLM evaluation on transcript using Groq
            parsed_outputs = {}
            
            if transcript:
                try:
                    evaluator = get_nmmc_call_evaluator()
                    if evaluator.is_available():
                        logger.info("🤖 Running NMMC Property Tax LLM evaluation on transcript...")
                        evaluation = evaluator.evaluate(transcript)
                        
                        if evaluation:
                            # NMMC evaluation has 10 dimensions
                            parsed_outputs = {
                                "citizen_sentiment": evaluation.citizen_sentiment.value,
                                "call_summary": evaluation.call_summary,
                                "call_outcome": evaluation.call_outcome.value,
                                "consequence_level_reached": evaluation.consequence_level_reached.value,
                                "citizen_response_type": evaluation.citizen_response_type.value,
                                "payment_commitment": evaluation.payment_commitment.value,
                                "proper_protocol_followed": evaluation.proper_protocol_followed,
                                "escalation_required": evaluation.escalation_required,
                                "compliance_score": evaluation.compliance_score,
                                "amount_bracket": evaluation.amount_bracket.value
                            }
                            logger.info(f"  📊 Sentiment: {evaluation.citizen_sentiment.value}")
                            logger.info(f"  📊 Outcome: {evaluation.call_outcome.value}")
                            logger.info(f"  📊 Consequence Level: {evaluation.consequence_level_reached.value}")
                            logger.info(f"  📊 Response: {evaluation.citizen_response_type.value}")
                            logger.info(f"  📊 Commitment: {evaluation.payment_commitment.value}")
                            logger.info(f"  📊 Compliance: {evaluation.compliance_score}/10")
                            logger.info(f"  📊 Protocol: {evaluation.proper_protocol_followed}")
                            logger.info(f"  📊 Escalation: {evaluation.escalation_required}")
                            logger.info(f"  📊 Amount: {evaluation.amount_bracket.value}")
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
                
                # Handle boolean conversions
                def to_bool(val):
                    if isinstance(val, bool):
                        return val
                    if isinstance(val, str):
                        return val.lower() == "true"
                    return None
                
                # Handle int conversions
                def to_int(val):
                    if isinstance(val, int):
                        return val
                    if isinstance(val, (float, str)):
                        try:
                            return int(val)
                        except (ValueError, TypeError):
                            return None
                    return None
                
                # Get duration and cost from message level (end-of-call-report)
                duration = message.get("durationSeconds")
                cost = message.get("cost")
                recording_url = artifact.get("recordingUrl") or message.get("recordingUrl")
                
                # NMMC CallLogEntry with 10 dimensions
                entry = CallLogEntry(
                    call_id=call_id,
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=duration,
                    citizen_sentiment=parsed_outputs.get("citizen_sentiment"),
                    call_summary=parsed_outputs.get("call_summary"),
                    escalation_required=to_bool(parsed_outputs.get("escalation_required")),
                    call_outcome=parsed_outputs.get("call_outcome"),
                    citizen_response_type=parsed_outputs.get("citizen_response_type"),
                    payment_commitment=parsed_outputs.get("payment_commitment"),
                    consequence_level_reached=parsed_outputs.get("consequence_level_reached"),
                    proper_protocol_followed=to_bool(parsed_outputs.get("proper_protocol_followed")),
                    compliance_score=to_int(parsed_outputs.get("compliance_score")),
                    amount_bracket=parsed_outputs.get("amount_bracket"),
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
        filename="nmmc_call_logs.csv",
        media_type="text/csv"
    )


@router.get("/call-logs/stats")
async def get_call_statistics():
    """
    Get statistics from NMMC property tax recovery call logs.
    
    Useful for:
    - Monitoring citizen sentiment trends
    - Tracking call outcomes (payment agreed, refused, etc.)
    - Measuring compliance scores and recovery effectiveness
    - Tracking escalation and consequence levels
    - Zone-wise analysis
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
        
        # Citizen sentiment distribution
        sentiments = Counter(row.get('citizen_sentiment', '') for row in rows if row.get('citizen_sentiment'))
        
        # Call outcome distribution
        outcomes = Counter(row.get('call_outcome', '') for row in rows if row.get('call_outcome'))
        
        # Payment commitment distribution
        commitments = Counter(row.get('payment_commitment', '') for row in rows if row.get('payment_commitment'))
        
        # Consequence level distribution
        consequence_levels = Counter(row.get('consequence_level_reached', '') for row in rows if row.get('consequence_level_reached'))
        
        # Escalation rate
        escalated_count = sum(1 for row in rows if row.get('escalation_required', '').lower() == 'true')
        
        # Protocol compliance rate
        protocol_count = sum(1 for row in rows if row.get('proper_protocol_followed', '').lower() == 'true')
        
        # Average compliance score
        scores = [int(row['compliance_score']) for row in rows if row.get('compliance_score')]
        avg_compliance = sum(scores) / len(scores) if scores else 0
        
        # Amount bracket distribution
        amount_brackets = Counter(row.get('amount_bracket', '') for row in rows if row.get('amount_bracket'))
        
        # Average duration
        durations = [float(row['duration_seconds']) for row in rows if row.get('duration_seconds')]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Total cost
        costs = [float(row['cost']) for row in rows if row.get('cost')]
        total_cost = sum(costs)
        
        # Recovery success rate (payment_agreed + date_committed)
        recovery_success = sum(1 for row in rows if row.get('call_outcome') in ('payment_agreed', 'date_committed'))
        
        return {
            "status": "ok",
            "total_calls": total_calls,
            "citizen_sentiment_distribution": dict(sentiments),
            "call_outcome_distribution": dict(outcomes),
            "payment_commitment_distribution": dict(commitments),
            "consequence_level_distribution": dict(consequence_levels),
            "amount_bracket_distribution": dict(amount_brackets),
            "recovery_success_rate": f"{(recovery_success / total_calls * 100):.1f}%" if total_calls > 0 else "N/A",
            "escalation_rate": f"{(escalated_count / total_calls * 100):.1f}%" if total_calls > 0 else "N/A",
            "protocol_compliance_rate": f"{(protocol_count / total_calls * 100):.1f}%" if total_calls > 0 else "N/A",
            "average_compliance_score": round(avg_compliance, 1),
            "recovery_success_count": recovery_success,
            "escalated_count": escalated_count,
            "average_duration_seconds": round(avg_duration, 1),
            "total_cost_usd": round(total_cost, 4)
        }
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
