from slowapi import Limiter
from slowapi.util import get_remote_address
from config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS

# Each request to /api/v1/research can trigger a multi-minute, real-money research pipeline
# run, so this exists to stop accidental/abusive loops - not to serve high request volume.
limiter = Limiter(key_func=get_remote_address)

RESEARCH_RATE_LIMIT: str = f"{RATE_LIMIT_MAX_REQUESTS}/{int(RATE_LIMIT_WINDOW_SECONDS)}second"
