from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware # <--- IMPORT THIS
from app.core.database import init_models

# Import your routers (We will create this file next)
from app.api.v1.api import api_router 

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Maritime DRS Backend...")
    await init_models()
    yield

app = FastAPI(title="Maritime DRS API", lifespan=lifespan)

# --- CORS CONFIGURATION (Crucial for Frontend connection) ---
origins = [
    "http://localhost:3000",  # Your Vite Frontend
    "http://localhost:5173",  # Alternate Vite Port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Allow all headers
)

# Register Routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Maritime DRS API is Online 🟢"}