import os
import time
import logging
import subprocess
from pathlib import Path
from typing import Optional
import cv2
import numpy as np

logger = logging.getLogger(__name__)


def check_ffmpeg_available() -> bool:
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

_model = None
_model_loaded_at: float = 0.0


def _resolve_model_path(settings) -> Path:
    """
    Resolve path model: jika yolo_model_name adalah path absolut atau mengandung
    separator, gunakan langsung. Jika hanya nama file, cari di models_dir.
    """
    name = settings.yolo_model_name
    p = Path(name)
    if p.is_absolute() or "/" in name or "\\" in name:
        return p
    return Path(settings.models_dir) / name


def get_model():
    global _model, _model_loaded_at
    if _model is not None:
        return _model

    from config import settings
    from ultralytics import YOLO

    model_path = _resolve_model_path(settings)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading YOLO model from {model_path} ...")
    _model = YOLO(str(model_path))
    _model.overrides["device"] = "cpu"
    _model.overrides["half"] = False
    _model_loaded_at = time.time()
    logger.info(f"Model loaded: {model_path.name}")
    return _model


def extract_frame_from_hls(stream_url: str, timeout: int = 10) -> Optional[np.ndarray]:
    """Open an HLS stream via OpenCV and grab a single frame."""
    cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)

    frame = None
    try:
        if cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                frame = None
    finally:
        cap.release()

    return frame


def run_inference(frame: np.ndarray) -> dict:
    """Run YOLOv8 person detection on a single frame."""
    from config import settings

    t0 = time.perf_counter()

    imgsz = settings.yolo_imgsz
    # Pertahankan aspect ratio: hitung tinggi proporsional dari lebar target
    orig_h, orig_w = frame.shape[:2]
    target_h = int(imgsz * orig_h / orig_w)
    small = cv2.resize(frame, (imgsz, target_h))

    model = get_model()
    results = model(
        small,
        classes=[0],        # hanya kelas person
        conf=settings.yolo_conf,
        iou=settings.yolo_iou,
        max_det=settings.yolo_max_det,
        imgsz=imgsz,
        verbose=False,
        half=False,
    )

    boxes = []
    confidences = []

    if results and len(results) > 0:
        result = results[0]
        if result.boxes is not None:
            orig_h, orig_w = frame.shape[:2]
            scale_x = orig_w / imgsz
            scale_y = orig_h / target_h
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                boxes.append([
                    int(x1 * scale_x),
                    int(y1 * scale_y),
                    int(x2 * scale_x),
                    int(y2 * scale_y),
                ])
                confidences.append(conf)

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    avg_conf = float(np.mean(confidences)) if confidences else 0.0

    h, w = frame.shape[:2]
    return {
        "person_count": len(boxes),
        "confidence_avg": round(avg_conf, 3),
        "bounding_boxes": boxes,
        "processing_time_ms": elapsed_ms,
        "frame_width": w,
        "frame_height": h,
    }


def encode_frame_jpeg(frame: np.ndarray, quality: int = 70) -> bytes:
    """Encode a numpy frame to JPEG bytes."""
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()
