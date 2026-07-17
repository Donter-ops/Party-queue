from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from core.dependencies import validate_spotify_oauth_config
from core.database import init_db
from routers.auth import router as auth_router
from routers.debug import router as debug_router
from routers.playback import router as playback_router
from routers.rooms import router as rooms_router
from routers.search import router as search_router

load_dotenv()
validate_spotify_oauth_config()
init_db()

app = FastAPI(title="PartyQueue API")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms_router)
app.include_router(search_router)
app.include_router(auth_router)
app.include_router(debug_router)
app.include_router(playback_router)
