"""
Fine-tuning YOLOv8n untuk deteksi kerumunan (crowd detection).

Persiapan:
  1. Download dataset CrowdHuman → train/raw/
     Lihat instruksi di prepare_crowdhuman.py
  2. Jalankan konverter:
        python train/prepare_crowdhuman.py
  3. Jalankan training dari repo root:
        python train/train.py

Rekomendasi hardware untuk training:
  - GPU NVIDIA (CUDA) — jauh lebih cepat (1–3 jam vs 1–2 hari di CPU)
  - RAM minimal 8GB
  - Jika hanya CPU (i3 Gen 7): gunakan --max-samples 2000 untuk percobaan cepat

Model output akan tersimpan di:
  models/training/semar_crowd_v1/weights/best.pt

Setelah selesai, update cv-engine/.env atau cv-engine/config.py:
  YOLO_MODEL_NAME=../models/training/semar_crowd_v1/weights/best.pt
"""

import argparse
import sys
from pathlib import Path

# Tambahkan repo root ke path agar bisa import config
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "cv-engine"))


def check_dataset():
    data_dir = REPO_ROOT / "train" / "data"
    train_imgs = data_dir / "images" / "train"
    val_imgs = data_dir / "images" / "val"

    if not train_imgs.exists() or not any(train_imgs.iterdir()):
        print("ERROR: Dataset belum siap.")
        print("Jalankan dulu: python train/prepare_crowdhuman.py")
        sys.exit(1)

    n_train = len(list(train_imgs.glob("*.jpg")))
    n_val = len(list(val_imgs.glob("*.jpg"))) if val_imgs.exists() else 0
    return n_train, n_val


def main():
    parser = argparse.ArgumentParser(description="Fine-tune YOLOv8n untuk crowd detection")
    parser.add_argument(
        "--epochs", type=int, default=50,
        help="Jumlah epoch training (default: 50)"
    )
    parser.add_argument(
        "--imgsz", type=int, default=640,
        help="Ukuran input training (default: 640, lebih besar = lebih akurat + lebih lambat)"
    )
    parser.add_argument(
        "--batch", type=int, default=8,
        help="Batch size (default: 8, kurangi jika OOM)"
    )
    parser.add_argument(
        "--device", type=str, default="cpu",
        help="Device: 'cpu' atau '0' untuk GPU pertama (default: cpu)"
    )
    parser.add_argument(
        "--workers", type=int, default=2,
        help="Jumlah data loader workers (default: 2)"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Lanjut dari checkpoint terakhir"
    )
    parser.add_argument(
        "--name", type=str, default="semar_crowd_v1",
        help="Nama run output (default: semar_crowd_v1)"
    )
    args = parser.parse_args()

    n_train, n_val = check_dataset()
    print(f"Dataset: {n_train} train, {n_val} val")

    from ultralytics import YOLO

    model_path = REPO_ROOT / "models" / "yolov8n.pt"
    if not model_path.exists():
        print("Mendownload YOLOv8n base model ...")
    model = YOLO(str(model_path) if model_path.exists() else "yolov8n.pt")

    dataset_yaml = str(REPO_ROOT / "train" / "dataset.yaml")
    output_dir = str(REPO_ROOT / "models" / "training")

    print(f"\nMemulai fine-tuning:")
    print(f"  Device  : {args.device}")
    print(f"  Epochs  : {args.epochs}")
    print(f"  Imgsz   : {args.imgsz}")
    print(f"  Batch   : {args.batch}")
    print(f"  Output  : {output_dir}/{args.name}/weights/best.pt")
    print()

    model.train(
        data=dataset_yaml,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        resume=args.resume,
        project=output_dir,
        name=args.name,

        # Optimizer — AdamW lebih stabil untuk fine-tuning
        optimizer="AdamW",
        lr0=0.001,        # learning rate awal (rendah karena fine-tuning)
        lrf=0.01,         # learning rate final (lr0 * lrf)
        weight_decay=0.0005,
        warmup_epochs=3,
        patience=15,      # early stopping jika tidak ada improvement

        # Augmentasi — dioptimasi untuk CCTV statis (kamera tetap, angle tetap)
        degrees=0.0,      # tidak ada rotasi (CCTV angle tetap)
        flipud=0.0,       # tidak ada flip vertikal
        fliplr=0.5,       # flip horizontal tetap berguna
        scale=0.5,        # scale jitter untuk variasi jarak orang
        translate=0.1,
        shear=0.0,
        perspective=0.0,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        mosaic=1.0,       # mosaic sangat efektif untuk crowd (gabung 4 gambar)
        mixup=0.1,
        copy_paste=0.1,   # copy-paste augmentation: bagus untuk crowd padat

        # Deteksi crowd — parameter kritis
        # iou rendah = lebih toleran terhadap overlap bounding box orang
        # (orang berdesakan wajar punya box yang overlap banyak)
        iou=0.4,

        # Simpan checkpoint setiap epoch (untuk resume jika gagal)
        save=True,
        save_period=10,
        plots=True,

        # Tidak pakai half precision di CPU
        half=False,
        amp=False if args.device == "cpu" else True,

        # Log verbose per epoch
        verbose=True,
        close_mosaic=10,  # matikan mosaic di 10 epoch terakhir untuk stabilitas
    )

    best_model = Path(output_dir) / args.name / "weights" / "best.pt"
    if best_model.exists():
        print(f"\nTraining selesai!")
        print(f"Model terbaik: {best_model}")
        print(f"\nUntuk menggunakannya, tambahkan ke cv-engine/.env:")
        print(f"  YOLO_MODEL_NAME={best_model.relative_to(REPO_ROOT)}")
    else:
        print("\nTraining selesai tapi best.pt tidak ditemukan. Cek log di atas.")


if __name__ == "__main__":
    main()
