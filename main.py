import subprocess
import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.datastructures import State
from starlette.responses import JSONResponse

# Load .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key Authentication
API_KEY = os.getenv("SPHINX_API_KEY", "your-secure-api-key")  # Change this to a secure key
api_key_header = APIKeyHeader(name="X-API-Key")

app = FastAPI()
app.state = State()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# List of Cloudflare IPs
CLOUDFLARE_IPS = [
    "173.245.48.0/20",
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/12",
    "172.64.0.0/13",
    "131.0.72.0/22"
]


def get_client_ip(request: Request):
    for ip in CLOUDFLARE_IPS:
        if request.client.host in ip:
            return request.headers.get("CF-Connecting-IP", request.client.host)
    return request.client.host


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    client_ip = get_client_ip(request)
    if api_key != API_KEY:
        return JSONResponse(status_code=403, content={"message": "Forbidden: Invalid or missing API key"})
    if request.method == "POST" and request.url.path == "/reindex":
        index = request.headers.get("index")
        if not index:
            return JSONResponse(status_code=666, content={"message": "Missing index in request"})
    if request.method != "POST":
        return JSONResponse(status_code=403, content={"message": "Forbidden: Invalid method"})
    response = await call_next(request)
    return response


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        logger.warning("Unauthorized access attempt with API key: %s", api_key)
        raise HTTPException(status_code=403, detail="Unauthorized")
    logger.info("API key verified")
    return api_key


def run_indexer(index="all"):
    logger.info("Starting indexer with index: %s", index)
    try:
        result = subprocess.run(
            [os.getenv("SPHINX_INDEXER_PATH"), "--rotate", index],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Indexer completed successfully")
            logger.info(result.stdout)
        else:
            logger.error("Indexer failed with return code: %d", result.returncode)
            logger.error(result.stderr)
    except FileNotFoundError:
        logger.error("indexer is not found on the system")
        logger.warning("skipping subprocess.run")
    except Exception as e:
        logger.warning(f"Preeba se:{e}")


@app.post("/reindex")
@limiter.limit("5 per minute")
def reindex(request: Request, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    index = request.headers.get("index")
    client_ip = get_client_ip(request)
    if not index:
        logger.error("No index provided, skipping...")
        raise HTTPException(status_code=666, detail="Missing index in request")
    logger.info(f"Reindexing requested for {index} from IP: {client_ip}")
    try:
        background_tasks.add_task(run_indexer, index=index)
    except Exception as e:
        logger.warning(f"Preebase e: {e}")
    return {"status": "indexing started"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPISphinx application")
    uvicorn.run(app, host=os.getenv("FAST_API_SPHINX_HOST"), port=int(os.getenv("FAST_API_SPHINX_PORT")))
