"""
Call Logger Service - Saves call data and structured outputs to CSV.

NMMC Property Tax Recovery Evaluation with 10 Dimensions:
- citizen_sentiment: cooperative | resistant | confused | hostile | indifferent
- call_summary: 2-3 sentence summary of the call
- call_outcome: payment_agreed | date_committed | partial_commitment | dispute_raised | refused | unreachable | call_dropped | already_paid
- consequence_level_reached: none | level_1_financial | level_2_administrative | level_3_legal | level_4_nuclear
- citizen_response_type: immediate_payment | requested_time | financial_hardship | disputed_amount | claimed_paid | abusive | disconnected | cooperative_inquiry
- payment_commitment: committed_with_date | vague_promise | refused | not_discussed
- proper_protocol_followed: true/false - agent followed proper call protocol
- escalation_required: true/false - needs supervisor/legal escalation
- compliance_score: 1-10 likelihood of payment
- amount_bracket: outstanding amount range
"""

import csv
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.domain.webhook import (
    CallLogEntry,
    VapiWebhookPayload,
    StructuredOutputs,
    StructuredOutputItem
)

logger = logging.getLogger(__name__)

# CSV file path - stored in project's data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CALL_LOG_FILE = DATA_DIR / "call_logs.csv"

# CSV columns for NMMC Property Tax evaluation (10 dimensions)
CSV_COLUMNS = [
    "call_id",                    # Unique Vapi call identifier
    "timestamp",                  # When the call ended (ISO format)
    "duration_seconds",           # Call duration in seconds
    "citizen_sentiment",          # cooperative | resistant | confused | hostile | indifferent
    "call_summary",               # 2-3 sentence summary
    "escalation_required",        # true/false - needs supervisor/legal escalation
    "call_outcome",               # Call outcome classification
    "citizen_response_type",      # How the citizen responded
    "payment_commitment",         # Payment commitment level
    "consequence_level_reached",  # Highest consequence level disclosed
    "proper_protocol_followed",   # true/false - agent followed protocol
    "compliance_score",           # 1-10 likelihood of payment
    "amount_bracket",             # Outstanding amount bracket
    "transcript",                 # Full call transcript
    "recording_url",              # URL to call recording
    "cost"                        # Call cost in USD
]


class CallLogger:
    """Service to log call data to CSV file."""
    
    def __init__(self):
        self._ensure_data_dir()
        self._ensure_csv_headers()
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Data directory: {DATA_DIR}")
    
    def _ensure_csv_headers(self):
        """Create CSV file with headers if it doesn't exist."""
        if not CALL_LOG_FILE.exists():
            with open(CALL_LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
            logger.info(f"Created call log CSV: {CALL_LOG_FILE}")
    
    def log_call(self, entry: CallLogEntry) -> bool:
        """
        Append a call log entry to the CSV file.
        
        Args:
            entry: CallLogEntry with NMMC evaluation (10 dimensions)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(CALL_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                
                # Helper to convert bool to string
                def bool_to_str(val):
                    return str(val) if val is not None else ""
                
                # Helper to convert int to string
                def int_to_str(val):
                    return str(val) if val is not None else ""
                
                # Convert entry to dict, handling None values
                row = {
                    "call_id": entry.call_id,
                    "timestamp": entry.timestamp,
                    "duration_seconds": entry.duration_seconds or "",
                    "citizen_sentiment": entry.citizen_sentiment or "",
                    "call_summary": self._clean_text(entry.call_summary),
                    "escalation_required": bool_to_str(entry.escalation_required),
                    "call_outcome": entry.call_outcome or "",
                    "citizen_response_type": entry.citizen_response_type or "",
                    "payment_commitment": entry.payment_commitment or "",
                    "consequence_level_reached": entry.consequence_level_reached or "",
                    "proper_protocol_followed": bool_to_str(entry.proper_protocol_followed),
                    "compliance_score": int_to_str(entry.compliance_score),
                    "amount_bracket": entry.amount_bracket or "",
                    "transcript": self._clean_text(entry.transcript),
                    "recording_url": entry.recording_url or "",
                    "cost": entry.cost or ""
                }
                
                writer.writerow(row)
            
            logger.info(f"Logged call {entry.call_id} to CSV")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log call to CSV: {e}")
            return False
    
    def _clean_text(self, text: Optional[str]) -> str:
        """Clean text for CSV storage (remove newlines, limit length)."""
        if not text:
            return ""
        # Replace newlines with spaces, limit to 5000 chars
        cleaned = text.replace('\n', ' ').replace('\r', ' ')
        return cleaned[:5000] if len(cleaned) > 5000 else cleaned
    
    def process_webhook(self, payload: VapiWebhookPayload) -> Optional[CallLogEntry]:
        """
        Process a Vapi webhook payload and extract call data.
        
        Handles both formats:
        1. call.artifact.structuredOutputs (newer format)
        2. message.analysis.structuredData (legacy format)
        
        Args:
            payload: VapiWebhookPayload from Vapi's end-of-call-report
            
        Returns:
            CallLogEntry if successful, None otherwise
        """
        try:
            # Get call data - could be in 'call' or 'message.call'
            call = payload.call
            if not call:
                logger.warning("No call data in webhook payload - trying to extract from raw data")
                return None
            
            call_id = call.id
            logger.info(f"Processing call: {call_id}")
            
            # Parse timestamps from call object
            timestamp = datetime.now().isoformat()
            if call.endedAt:
                timestamp = call.endedAt
            
            # Calculate duration
            duration = None
            if call.startedAt and call.endedAt:
                try:
                    start = datetime.fromisoformat(call.startedAt.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(call.endedAt.replace('Z', '+00:00'))
                    duration = (end - start).total_seconds()
                except Exception as e:
                    logger.warning(f"Could not parse call duration: {e}")
            
            # Extract structured outputs from call.artifact.structuredOutputs
            structured = self._parse_structured_outputs(call)
            
            # Get transcript and recording from artifact
            transcript = None
            recording_url = None
            if call.artifact:
                transcript = call.artifact.transcript
                recording_url = call.artifact.recordingUrl
            
            # Fallback to legacy fields if not in artifact
            if not transcript and payload.transcript:
                transcript = payload.transcript
            if not recording_url and payload.recordingUrl:
                recording_url = payload.recordingUrl
            
            # Create log entry
            entry = CallLogEntry(
                call_id=call_id,
                timestamp=timestamp,
                duration_seconds=duration,
                citizen_sentiment=structured.citizen_sentiment if structured else None,
                call_summary=structured.call_summary if structured else None,
                call_outcome=structured.call_outcome if structured else None,
                escalation_required=structured.escalation_required if structured else None,
                compliance_score=structured.compliance_score if structured else None,
                transcript=transcript,
                recording_url=recording_url,
                cost=call.cost
            )
            
            return entry
            
        except Exception as e:
            logger.error(f"Failed to process webhook payload: {e}")
            return None
    
    def _parse_structured_outputs(self, call) -> Optional[StructuredOutputs]:
        """
        Parse structured outputs from Vapi call artifact.
        
        Vapi format: call.artifact.structuredOutputs = {
            "<uuid>": { "name": "citizen_sentiment", "result": "cooperative" },
            "<uuid>": { "name": "call_summary", "result": "..." },
            ...
        }
        """
        try:
            if not call.artifact or not call.artifact.structuredOutputs:
                return None
            
            outputs = call.artifact.structuredOutputs
            
            # Map name -> result
            result_map = {}
            for uuid, item in outputs.items():
                if isinstance(item, dict):
                    name = item.get("name")
                    result = item.get("result")
                    if name:
                        result_map[name] = result
                elif hasattr(item, "name") and hasattr(item, "result"):
                    result_map[item.name] = item.result
            
            logger.info(f"Parsed structured outputs: {list(result_map.keys())}")
            
            # Map to our StructuredOutputs model
            return StructuredOutputs(
                citizen_sentiment=result_map.get("citizen_sentiment"),
                call_summary=result_map.get("call_summary"),
                call_outcome=result_map.get("call_outcome"),
                escalation_required=self._parse_bool(result_map.get("escalation_required")),
                compliance_score=self._parse_int(result_map.get("compliance_score"))
            )
            
        except Exception as e:
            logger.error(f"Failed to parse structured outputs: {e}")
            return None
    
    def _parse_bool(self, value) -> Optional[bool]:
        """Parse boolean value from various formats."""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1")
        return bool(value)
    
    def _parse_int(self, value) -> Optional[int]:
        """Parse integer value from various formats."""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, (float, str)):
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        return None
    
    def get_log_file_path(self) -> str:
        """Return the path to the CSV log file."""
        return str(CALL_LOG_FILE)
    
    def get_recent_calls(self, limit: int = 10) -> list[dict]:
        """
        Get the most recent call logs.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of call log entries as dicts
        """
        try:
            if not CALL_LOG_FILE.exists():
                return []
            
            with open(CALL_LOG_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Return most recent entries
            return rows[-limit:] if len(rows) > limit else rows
            
        except Exception as e:
            logger.error(f"Failed to read call logs: {e}")
            return []


# Singleton instance
_call_logger: Optional[CallLogger] = None


def get_call_logger() -> CallLogger:
    """Get the call logger singleton."""
    global _call_logger
    if _call_logger is None:
        _call_logger = CallLogger()
    return _call_logger
