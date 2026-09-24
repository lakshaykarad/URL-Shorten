import socket
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse
import asyncpg
from schemas import URLRequest
from utils import generate_short_code

router = APIRouter()

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

@router.get("/")    
async def root(request: Request):
    return {
        "status": "System Online",
        "hostname": socket.gethostname(),
        "postgres": "Connecting" if hasattr(request.app.state, 'db_pool') else "Disconnected",
        "redis": "Connecting" if hasattr(request.app.state, 'redis_client') else "Disconnected"
    }

@router.post("/shorten", status_code=status.HTTP_201_CREATED)
async def shorten_url(request_url: URLRequest, request: Request):
    redis_client = request.app.state.redis_client
    db_pool = request.app.state.db_pool

    client_ip = get_client_ip(request)
    redis_key = f"rate_limit:{client_ip}"

    requests_made = await redis_client.incr(redis_key)
    if requests_made == 1:
        await redis_client.expire(redis_key, 60)
    if requests_made > 5:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")

    max_retries = 3
    short_code = None
    for attempt in range(max_retries):
        short_code = generate_short_code()
        try:
            async with db_pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO urls (original_url, short_code) VALUES ($1, $2)",
                    str(request_url.url), short_code
                )
            break
        except asyncpg.exceptions.UniqueViolationError:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail="Could not generate unique URL. Try again.")
            continue

    base_url = str(request.base_url)
    return {
        "original_url": str(request_url.url),
        "short_url": f"{base_url}{short_code}"
    }

@router.get("/{short_code}")
async def redirect_to_original(short_code: str, request: Request):
    redis_client = request.app.state.redis_client
    db_pool = request.app.state.db_pool

    cached_url = await redis_client.get(short_code)

    if cached_url == "__NOT_FOUND__":
        print(f"CACHE HIT (404) — {short_code}")
        raise HTTPException(status_code=404, detail="Short URL not found")

    if cached_url:
        print(f"CACHE HIT — {short_code}")
        return RedirectResponse(url=cached_url)

    print(f"CACHE MISS — {short_code}")
    try:
        async with db_pool.acquire() as connection:
            record = await connection.fetchrow(
                "SELECT original_url FROM urls WHERE short_code = $1",
                short_code
            )
    except Exception:
        raise HTTPException(status_code=500, detail="Database connection error.")

    if record:
        original_url = record['original_url']
        await redis_client.set(short_code, original_url, ex=600)
        return RedirectResponse(url=original_url)

    await redis_client.set(short_code, "__NOT_FOUND__", ex=60)
    raise HTTPException(status_code=404, detail="Short URL not found")