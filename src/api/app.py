import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from config import CORS_ALLOWED_ORIGINS
from .rate_limiter import limiter
from .request_logging_middleware import RequestLoggingMiddleware
from .routes.research import router as research_router
from .routes.ask import router as ask_router

app = FastAPI(title="Agentic News Research API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestLoggingMiddleware)
# Added after RequestLoggingMiddleware so it wraps outermost (Starlette treats the
# most-recently-added middleware as outermost) - it needs to see every request first to
# short-circuit CORS preflight (OPTIONS) before the rate limiter or routes ever run, and to
# add its headers to every response, including 429s. No-op until CORS_ALLOWED_ORIGINS is set -
# today's frontend is served from the same origin as the API, so nothing needs it yet.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

app.include_router(research_router, prefix="/api/v1")
app.include_router(ask_router, prefix="/api/v1")

# Mounted last (and at "/") so it only catches requests the routes above didn't already match.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    uvicorn.run(app, host="127.0.0.1", port=8000)
