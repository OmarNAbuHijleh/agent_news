import logging
import time

logger = logging.getLogger("src.api.requests")


class RequestLoggingMiddleware:
    """Raw ASGI middleware (not Starlette's BaseHTTPMiddleware, which buffers the response body
    and breaks true streaming) that logs method, path, status, and total duration for every
    request - including streaming ones, where duration covers the whole stream rather than just
    time-to-first-byte.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.monotonic()
        method = scope["method"]
        path = scope["path"]
        status_code = None

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                duration_ms = (time.monotonic() - start_time) * 1000
                logger.info("method=%s path=%s status=%s duration_ms=%.1f", method, path, status_code, duration_ms)

        await self.app(scope, receive, send_wrapper)
