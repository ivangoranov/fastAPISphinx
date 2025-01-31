import subprocess
import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.datastructures import State


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


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        logger.warning("Unauthorized access attempt with API key: %s", api_key)
        raise HTTPException(status_code=403, detail="Unauthorized")
    logger.info("API key verified: %s", api_key)
    return api_key


def run_indexer(index="all"):
    logger.info("Starting indexer with index: %s", index)
    try:
        result = subprocess.run(
            [os.getenv("SPHINX_INDEXER_PATH"), "--rotate", f"--{index}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            logger.info("Indexer completed successfully")
        else:
            logger.error("Indexer failed with return code: %d", result.returncode)
    except FileNotFoundError:
        logger.error("indexer is not found on the system")
        logger.warning("skipping subprocess.run")
    except Exception as e:
        logger.warning(f"Preeba se:{e}")


@app.post("/reindex")
@limiter.limit("5 per minute")
def reindex(request: Request, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    index = request.headers.get("index")
    if not index:
        logger.error("No index provided, skipping...")
        return HTTPException(status_code=666, detail="Missing index in request")
    logger.info(f"Reindexing requested for {index}")
    try:
        background_tasks.add_task(run_indexer, index=index)
    except Exception as e:
        logger.warning(f"Preebase e: {e}")
    return {"status": "indexing started"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPISphinx application")
    uvicorn.run(app, host="0.0.0.0", port=5001)
