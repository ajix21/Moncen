from pydantic_settings import BaseSettings
from typing import Dict, Any


ALERT_LEVELS: Dict[str, Dict[str, Any]] = {
    "NORMAL":  {"min": 0,    "max": 49,    "color": "#10b981"},
    "WASPADA": {"min": 50,   "max": 199,   "color": "#f59e0b"},
    "SIAGA":   {"min": 200,  "max": 999,   "color": "#f97316"},
    "DARURAT": {"min": 1000, "max": 99999, "color": "#ef4444"},
}


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///../shared/semar_watch.db"
    dashboard_url: str = "http://localhost:8000"
    cv_engine_port: int = 8001
    cv_frame_interval: int = 5
    max_concurrent_streams: int = 2
    rotation_interval: int = 60
    yolo_model_name: str = "yolov8n.pt"
    models_dir: str = "../models"
    yolo_imgsz: int = 416
    yolo_conf: float = 0.4
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
