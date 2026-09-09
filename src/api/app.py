import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .rate_limiter import limiter
from .request_logging_middleware import RequestLoggingMiddleware
from .routes.research import router as research_router

app = FastAPI(title="Agentic News Research API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(research_router, prefix="/api/v1")

# Mounted last (and at "/") so it only catches requests the routes above didn't already match.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    uvicorn.run(app, host="127.0.0.1", port=8000)
