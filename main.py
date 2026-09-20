import socket
from fastapi import FastAPI
from databse import lifespan
from router import router 

app = FastAPI(title="Secure URL Shortener", lifespan=lifespan)
 
app.include_router(router)