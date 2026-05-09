from pydantic_settings import BaseSettings
from typing import List, Dict, Any


DEFAULT_CCTV_STREAMS: List[Dict[str, Any]] = [
    {
        "id": "0e14deb6-0c55-4d42-9fa7-a192b5dce1dd",
        "name": "CCTV Titik 1",
        "location": "Semarang - Area 1",
        "stream_url": "https://livepantau.semarangkota.go.id/0e14deb6-0c55-4d42-9fa7-a192b5dce1dd/video1_stream.m3u8",
        "enabled": True,
    },
    {
        "id": "e2c7edd9-10d1-4bb6-897c-1a6b6fbc71ea",
        "name": "CCTV Titik 2",
        "location": "Semarang - Area 2",
        "stream_url": "https://livepantau.semarangkota.go.id/e2c7edd9-10d1-4bb6-897c-1a6b6fbc71ea/video1_stream.m3u8",
        "enabled": True,
    },
    {
        "id": "87d4863c-95f7-4676-8923-d6488d26fedf",
        "name": "CCTV Titik 3",
        "location": "Semarang - Area 3",
        "stream_url": "https://livepantau.semarangkota.go.id/87d4863c-95f7-4676-8923-d6488d26fedf/video1_stream.m3u8",
        "enabled": True,
    },
    {
        "id": "b23eb93b-a0ed-452b-a575-87027b1924cf",
        "name": "CCTV Titik 4",
        "location": "Semarang - Area 4",
        "stream_url": "https://livepantau.semarangkota.go.id/b23eb93b-a0ed-452b-a575-87027b1924cf/video1_stream.m3u8",
        "enabled": True,
    },
]


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///../shared/semar_watch.db"
    backend_port: int = 8000
    cv_engine_url: str = "http://localhost:8001"
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    cv_status_timeout: float = 2.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
