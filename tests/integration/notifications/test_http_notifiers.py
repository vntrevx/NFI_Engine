from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar

from nfi_engine.events import EventCode, EventSeverity, TradingEvent
from nfi_engine.notifications import NotificationErrorCode, WebhookNotifier


def test_webhook_notifier_posts_to_local_fake_server_and_retries() -> None:
    # Given
    server = _start_server(failures_before_success=1, delay_seconds=0)
    notifier = WebhookNotifier(url=server.url, max_attempts=2)

    try:
        # When
        result = notifier.send(_event("retry-smoke"))

        # Then
        assert result.success is True
        assert result.attempts == 2
        assert CapturingHandler.request_count == 2
        assert "retry-smoke" in CapturingHandler.bodies[-1]
    finally:
        server.close()


def test_webhook_notifier_timeout_returns_nonfatal_failure() -> None:
    # Given
    server = _start_server(failures_before_success=0, delay_seconds=0.05)
    notifier = WebhookNotifier(url=server.url, timeout_seconds=0.001, max_attempts=1)

    try:
        # When
        result = notifier.send(_event("timeout-smoke"))

        # Then
        assert result.success is False
        assert result.failure_code is NotificationErrorCode.NOTIFICATION_TIMEOUT
        assert result.attempts == 1
    finally:
        server.close()


class CapturingHandler(BaseHTTPRequestHandler):
    request_count: ClassVar[int] = 0
    failures_before_success: ClassVar[int] = 0
    delay_seconds: ClassVar[float] = 0.0
    bodies: ClassVar[list[str]] = []

    def do_POST(self) -> None:
        type(self).request_count += 1
        content_length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        type(self).bodies.append(body)
        if type(self).delay_seconds > 0:
            time.sleep(type(self).delay_seconds)
            return
        if type(self).request_count <= type(self).failures_before_success:
            self.send_response(503)
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()


@dataclass(frozen=True, slots=True)
class LocalServer:
    url: str
    server: ThreadingHTTPServer
    thread: threading.Thread

    def close(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()


def _start_server(*, failures_before_success: int, delay_seconds: float) -> LocalServer:
    CapturingHandler.request_count = 0
    CapturingHandler.failures_before_success = failures_before_success
    CapturingHandler.delay_seconds = delay_seconds
    CapturingHandler.bodies = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), CapturingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return LocalServer(
        url=f"http://127.0.0.1:{server.server_port}/notify",
        server=server,
        thread=thread,
    )


def _event(summary: str) -> TradingEvent:
    return TradingEvent(
        at=datetime(2026, 1, 1, tzinfo=UTC),
        severity=EventSeverity.WARNING,
        code=EventCode.BOT_STARTED,
        correlation_id="corr-http-notify",
        command="integration",
        route=None,
        safe_summary=summary,
        report_hint="attach local fake server transcript",
    )
