import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI
from contextlib import asynccontextmanager

#lifecycle management for postgres & redis 
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up connections...")
    # Initialize the PostgreSQL connection pool
    app.state.db_pool = await asyncpg.create_pool(
        user='postgres',
        password='1234',
        database='url_db',
        host='db',
        port=5432
    )
    # build table if not exist
    async with app.state.db_pool.acquire() as connection:
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id SERIAL PRIMARY KEY,
                original_url TEXT NOT NULL,
                short_code VARCHAR(10) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    # connect to redis so we can reduse DB load 
    app.state.redis_client = redis.Redis(
        host='cache',
        port=6379,
        decode_responses=True 
    )    
    
    print("Successfully connected to Postgres and Redis!")
    
    yield # Hand over control to FastAPI 
    # close teh connection from redis & DB after work 
    print("Closing connections...")
    await app.state.db_pool.close()
    await app.state.redis_client.aclose()