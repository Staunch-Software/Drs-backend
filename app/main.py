from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_models
from app.api.v1.api import api_router 

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Maritime DRS Backend...")
    await init_models()
    yield

app = FastAPI(title="Maritime DRS API", lifespan=lifespan)

# ✅ FIXED: Enhanced CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",  # ✅ Added backend URL
    "http://localhost:8000",   # ✅ Added backend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # ✅ Added to expose response headers
)

# Register Routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Maritime DRS API is Online 🟢"}