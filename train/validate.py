"""
Validasi model (base atau fine-tuned) pada val set CrowdHuman.

Jalankan dari repo root:
  python train/validate.py                           # validasi yolov8n.pt (base)
  python train/validate.py --model models/training/semar_crowd_v1/weights/best.pt

Metrik yang diperhatikan:
  - mAP50     : mean Average Precision @ IoU=0.5 (utama)
  - mAP50-95  : lebih ketat, multi-threshold
  - Recall    : seberapa banyak orang yang berhasil terdeteksi (target: tinggi)
  - Precision : seberapa sedikit false positive (target: tinggi)

Untuk crowd detection, prioritas:
  Recall > Precision (lebih baik over-count sedikit daripada miss banyak)
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default=str(REPO_ROOT / "models" / "yolov8n.pt"),
        help="Path ke model .pt yang ingin divalidasi",
    )
    parser.add_argument(
        "--imgsz", type=int, default=640,
        help="Ukuran input (harus sama dengan saat training)"
    )
    parser.add_argument(
        "--conf", type=float, default=0.25,
        help="Confidence threshold untuk validasi"
    )
    parser.add_argument(
        "--iou", type=float, default=0.35,
        help="NMS IoU threshold"
    )
    parser.add_argument(
        "--device", type=str, default="cpu",
    )
    args = parser.parse_args()

    data_dir = REPO_ROOT / "train" / "data" / "images" / "val"
    if not data_dir.exists() or not any(data_dir.iterdir()):
        print("Val set belum ada. Jalankan dulu: python train/prepare_crowdhuman.py")
        sys.exit(1)

    from ultralytics import YOLO

    model = YOLO(args.model)
    dataset_yaml = str(REPO_ROOT / "train" / "dataset.yaml")

    print(f"Validasi: {args.model}")
    metrics = model.val(
        data=dataset_yaml,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        device=args.device,
        verbose=True,
    )

    print("\n=== Hasil Validasi ===")
    print(f"  mAP50    : {metrics.box.map50:.4f}")
    print(f"  mAP50-95 : {metrics.box.map:.4f}")
    print(f"  Precision: {metrics.box.mp:.4f}")
    print(f"  Recall   : {metrics.box.mr:.4f}")


if __name__ == "__main__":
    main()
