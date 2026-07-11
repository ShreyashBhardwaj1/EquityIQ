"""
ReportStreamingService — Server-Sent Events (SSE) payload builders
and async generator for streaming report generation events.
"""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

logger = logging.getLogger("equityiq.application.report_streaming_service")

# SSE event type constants
EVENT_QUEUED = "queued"
EVENT_PROGRESS = "progress"
EVENT_SECTION_STARTED = "section_started"
EVENT_TOKEN = "token"
EVENT_SECTION_COMPLETED = "section_completed"
EVENT_COMPLETED = "completed"
EVENT_FAILED = "failed"
EVENT_HEARTBEAT = "heartbeat"


def _sse_line(event_type: str, data: dict[str, Any]) -> str:
    """
    Format a single SSE message in the standard SSE wire format.

    Output format:
        event: <event_type>
        data: <json_payload>
        (blank line)
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def build_queued_event(report_id: str, company_id: str) -> str:
    """Build the initial 'queued' SSE event payload."""
    return _sse_line(EVENT_QUEUED, {"report_id": report_id, "company_id": company_id})


def build_progress_event(percentage: float, status_msg: str) -> str:
    """Build a 'progress' SSE event with percentage and message."""
    return _sse_line(
        EVENT_PROGRESS, {"percentage": round(percentage, 1), "status": status_msg}
    )


def build_section_started_event(section_name: str) -> str:
    """Build a 'section_started' event announcing the beginning of a section."""
    return _sse_line(EVENT_SECTION_STARTED, {"section_name": section_name})


def build_token_event(text: str) -> str:
    """Build a 'token' streaming event with a text fragment."""
    return _sse_line(EVENT_TOKEN, {"text": text})


def build_section_completed_event(section_name: str, content: str) -> str:
    """Build a 'section_completed' event with the finalized section content."""
    return _sse_line(
        EVENT_SECTION_COMPLETED,
        {"section_name": section_name, "content": content},
    )


def build_completed_event(report_id: str, duration_seconds: float) -> str:
    """Build the terminal 'completed' event."""
    return _sse_line(
        EVENT_COMPLETED,
        {"report_id": report_id, "duration_seconds": round(duration_seconds, 2)},
    )


def build_failed_event(error: str, code: int = 500) -> str:
    """Build a terminal 'failed' event."""
    return _sse_line(EVENT_FAILED, {"error": error, "code": code})


def build_heartbeat_event() -> str:
    """Build a heartbeat keepalive SSE comment."""
    return ": heartbeat\n\n"


class ReportSSEStreamingService:
    """
    Manages SSE stream delivery for completed or in-progress reports.

    For completed reports: streams the full content word-by-word from DB.
    Maintains the same SSE protocol as live generation streams.
    """

    CHUNK_WORD_SIZE = 5  # words per token event for replay streaming

    async def stream_completed_report(
        self,
        report_id: str,
        company_id: str,
        content: str,
        duration_seconds: float,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completed report's content from the database via SSE.

        Splits the content into word-level token events for a live-replay feel.
        Yields SSE-formatted strings for each event.
        """
        yield build_queued_event(report_id, company_id)
        yield build_progress_event(50.0, "Loading completed report")

        # Stream content word-by-word
        words = content.split()
        total_words = len(words)

        for i in range(0, total_words, self.CHUNK_WORD_SIZE):
            chunk_words = words[i : i + self.CHUNK_WORD_SIZE]
            token_text = " ".join(chunk_words)
            if i > 0:
                token_text = " " + token_text
            yield build_token_event(token_text)

        yield build_completed_event(report_id, duration_seconds)

    async def stream_section_content(
        self,
        section_name: str,
        section_content: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a single section's content token-by-token.
        Yields SSE-formatted strings.
        """
        yield build_section_started_event(section_name)

        words = section_content.split()
        for i in range(0, len(words), self.CHUNK_WORD_SIZE):
            chunk_words = words[i : i + self.CHUNK_WORD_SIZE]
            token_text = " ".join(chunk_words)
            if i > 0:
                token_text = " " + token_text
            yield build_token_event(token_text)

        yield build_section_completed_event(section_name, section_content)
