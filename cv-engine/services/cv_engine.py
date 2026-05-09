import os
import time
import logging
from pathlib import Path
from typing import Optional
import cv2
import numpy as np

logger = logging.getLogger(__name__)

_model = None
_model_loaded_at: float = 0.0


def get_model():
    global _model, _model_loaded_at
    if _model is not None:
        return _model

    from config import settings
    from ultralytics import YOLO

    model_path = Path(settings.models_dir) / settings.yolo_model_name
    model_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading YOLO model from {model_path} ...")
    _model = YOLO(str(model_path))
    _model.overrides["device"] = "cpu"
    _model.overrides["half"] = False
    _model.overrides["imgsz"] = settings.yolo_imgsz
    _model.overrides["conf"] = settings.yolo_conf
    _model_loaded_at = time.time()
    logger.info("YOLO model loaded successfully")
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

    small = cv2.resize(frame, (416, 234))
    model = get_model()
    results = model(small, classes=[0], verbose=False)

    boxes = []
    confidences = []

    if results and len(results) > 0:
        result = results[0]
        if result.boxes is not None:
            orig_h, orig_w = frame.shape[:2]
            scale_x = orig_w / 416
            scale_y = orig_h / 234
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
