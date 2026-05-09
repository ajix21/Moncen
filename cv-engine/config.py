from pathlib import Path as _Path
from pydantic_settings import BaseSettings
from typing import Dict, Any

_BASE_DIR = _Path(__file__).parent.parent

ALERT_LEVELS: Dict[str, Dict[str, Any]] = {
    "NORMAL":  {"min": 0,    "max": 49,    "color": "#10b981"},
    "WASPADA": {"min": 50,   "max": 199,   "color": "#f59e0b"},
    "SIAGA":   {"min": 200,  "max": 999,   "color": "#f97316"},
    "DARURAT": {"min": 1000, "max": 99999, "color": "#ef4444"},
}


class Settings(BaseSettings):
    database_url: str = f"sqlite+aiosqlite:///{(_BASE_DIR / 'shared' / 'semar_watch.db').as_posix()}"
    dashboard_url: str = "http://localhost:8000"
    cv_engine_port: int = 8001
    cv_frame_interval: int = 5
    max_concurrent_streams: int = 2
    rotation_interval: int = 60

    # Model — bisa diisi nama file (dicari di models_dir)
    # atau path absolut/relatif ke model custom hasil fine-tuning
    # Contoh: YOLO_MODEL_NAME=../models/training/semar_crowd_v1/weights/best.pt
    yolo_model_name: str = "yolov8n.pt"
    models_dir: str = str(_BASE_DIR / "models")

    # Inference params
    # yolo_imgsz: lebih besar = lebih akurat untuk orang kecil/jauh, lebih lambat
    #   416 → default/hemat, 640 → direkomendasikan setelah fine-tune
    yolo_imgsz: int = 416
    # yolo_conf: threshold confidence
    #   0.4 → default (base model), 0.25 → setelah fine-tune (model lebih presisi)
    yolo_conf: float = 0.4
    # yolo_iou: NMS IoU threshold — rendah = lebih toleran box overlap (crowd)
    #   0.7 → default YOLO, 0.35 → optimal untuk crowd padat
    yolo_iou: float = 0.45
    # yolo_max_det: batas deteksi per frame
    yolo_max_det: int = 300

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
