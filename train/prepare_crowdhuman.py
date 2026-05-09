"""
Konverter CrowdHuman → YOLO format untuk fine-tuning YOLOv8n.

Dataset CrowdHuman: https://www.crowdhuman.org/download.html
  Butuh daftar akun, lalu download:
    - annotation_train.odgt
    - annotation_val.odgt
    - CrowdHuman_train01.zip ... CrowdHuman_train03.zip
    - CrowdHuman_val.zip

Setelah extract, struktur yang diharapkan:
  train/raw/
  ├── annotation_train.odgt
  ├── annotation_val.odgt
  └── images/
      ├── 000001.jpg
      └── ...

Jalankan:
  python prepare_crowdhuman.py

Output → train/data/{images,labels}/{train,val}/
"""

import json
import shutil
import argparse
from pathlib import Path
from PIL import Image

RAW_DIR = Path(__file__).parent / "raw"
OUT_DIR = Path(__file__).parent / "data"

# Gunakan "vbox" (visible body) bukan "fbox" (full body).
# Visible body lebih cocok untuk CCTV karena bagian yang
# tidak terlihat (di balik tembok/orang lain) tidak dianotasi.
BOX_KEY = "vbox"


def odgt_to_yolo(odgt_path: Path, img_src_dir: Path, split: str, max_samples: int = 0):
    img_dst = OUT_DIR / "images" / split
    lbl_dst = OUT_DIR / "labels" / split
    img_dst.mkdir(parents=True, exist_ok=True)
    lbl_dst.mkdir(parents=True, exist_ok=True)

    skipped = 0
    converted = 0

    with open(odgt_path, "r") as f:
        lines = f.readlines()

    if max_samples > 0:
        lines = lines[:max_samples]

    for line in lines:
        record = json.loads(line.strip())
        img_id = record["ID"]
        img_file = img_src_dir / f"{img_id}.jpg"

        if not img_file.exists():
            skipped += 1
            continue

        try:
            with Image.open(img_file) as im:
                W, H = im.size
        except Exception:
            skipped += 1
            continue

        yolo_lines = []
        for ann in record.get("gtboxes", []):
            if ann.get("tag") != "person":
                continue
            extra = ann.get("extra", {})
            # Abaikan anotasi ignore (orang di belakang kerumunan, blur, dll)
            if extra.get("ignore", 0) == 1:
                continue

            box = ann.get(BOX_KEY)
            if not box or len(box) < 4:
                continue

            x, y, w, h = box
            # Clamp ke batas gambar
            x = max(0, x)
            y = max(0, y)
            w = min(w, W - x)
            h = min(h, H - y)

            if w <= 2 or h <= 2:
                continue

            cx = (x + w / 2) / W
            cy = (y + h / 2) / H
            nw = w / W
            nh = h / H

            # YOLO class 0 = person
            yolo_lines.append(f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        if not yolo_lines:
            skipped += 1
            continue

        shutil.copy(img_file, img_dst / f"{img_id}.jpg")
        (lbl_dst / f"{img_id}.txt").write_text("\n".join(yolo_lines))
        converted += 1

    print(f"[{split}] Converted: {converted}, Skipped: {skipped}")
    return converted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DIR,
        help="Direktori berisi annotation_*.odgt dan images/",
    )
    parser.add_argument(
        "--max-train",
        type=int,
        default=0,
        help="Batas jumlah gambar train (0 = semua ~15k)",
    )
    parser.add_argument(
        "--max-val",
        type=int,
        default=0,
        help="Batas jumlah gambar val (0 = semua ~4.4k)",
    )
    args = parser.parse_args()

    raw_dir: Path = args.raw_dir
    img_dir = raw_dir / "images"

    train_odgt = raw_dir / "annotation_train.odgt"
    val_odgt = raw_dir / "annotation_val.odgt"

    if not train_odgt.exists():
        print(f"ERROR: {train_odgt} tidak ditemukan.")
        print("Download dari https://www.crowdhuman.org/download.html")
        print("lalu extract ke train/raw/")
        return

    print("Konversi CrowdHuman → YOLO format ...")
    n_train = odgt_to_yolo(train_odgt, img_dir, "train", args.max_train)
    n_val = odgt_to_yolo(val_odgt, img_dir, "val", args.max_val)
    print(f"\nSelesai: {n_train} train, {n_val} val")
    print(f"Output: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
