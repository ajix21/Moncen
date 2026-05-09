# SEMAR WATCH v2 — CCTV Monitoring + Computer Vision

Sistem monitoring CCTV Kota Semarang dengan analisis kerumunan berbasis AI (YOLOv8n).
Arsitektur split service: dashboard ringan always-on + CV engine on-demand hemat daya.

Target hardware: Intel Core i3 Gen 7, 8GB RAM.

---

## Arsitektur

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite) — port 5173                        │
│  - CCTV Grid (HLS player)                                   │
│  - CV Engine panel (ON/OFF indicator)                       │
│  - Alert system, Event log, Analytics                       │
└────────────┬──────────────────────┬────────────────────────┘
             │ /api/*               │ /ws/cv/*, /cv/*
             ▼                      ▼
┌────────────────────┐   ┌──────────────────────────────────┐
│ Dashboard          │   │ CV Engine                        │
│ port 8000          │   │ port 8001 (on-demand)            │
│ - CCTV CRUD        │   │ - YOLOv8n inference              │
│ - Event log        │   │ - HLS frame extraction           │
│ - CV status proxy  │   │ - WebSocket push results         │
│ - SQLite (R/W)     │   │ - SQLite writes events           │
└────────────────────┘   └──────────────────────────────────┘
             │                      │
             └──────────┬───────────┘
                        ▼
               shared/semar_watch.db (WAL mode)
```

---

## Quick Start

### 1. Setup (sekali saja)

```bash
chmod +x setup.sh start-*.sh stop-*.sh
./setup.sh
```

### 2. Jalankan Dashboard Saja (hemat daya)

```bash
./start-dashboard.sh
```

Buka: http://localhost:5173

Dashboard berjalan — video stream tetap tampil, tapi analisis CV tidak aktif.
Semua CCTV card menampilkan `--` untuk jumlah orang.

### 3. Aktifkan CV Engine (analisis massa)

```bash
./start-cv.sh
```

CV Engine akan:
- Load model YOLOv8n (auto-download ~6MB jika belum ada)
- Fetch daftar CCTV dari dashboard API
- Mulai proses max 2 stream secara bersamaan (rotasi setiap 60s)

### 4. Stop CV Engine

```bash
./stop-cv.sh
```

### 5. Stop Semua

```bash
./stop-all.sh
```

---

## Port & Service

| Service         | Port  | Command                   |
|-----------------|-------|---------------------------|
| Dashboard API   | 8000  | ./start-dashboard.sh      |
| CV Engine API   | 8001  | ./start-cv.sh             |
| Frontend (Vite) | 5173  | (dijalankan oleh dashboard script) |

---

## Level Alert

| Level    | Rentang      | Warna   |
|----------|-------------|---------|
| NORMAL   | 0–49 orang  | Hijau   |
| WASPADA  | 50–199 orang | Kuning  |
| SIAGA    | 200–999 orang | Oranye |
| DARURAT  | ≥1000 orang | Merah   |

---

## Konfigurasi CV Engine

Edit `cv-engine/config.py`:

```python
CV_FRAME_INTERVAL = 5      # detik antar frame (default 5s)
MAX_CONCURRENT_STREAMS = 2  # max stream diproses bersamaan
YOLO_MODEL_NAME = "yolov8n.pt"  # HANYA nano — jangan medium/large
```

Atau ubah via UI Settings → Pengaturan CV Engine (berlaku langsung tanpa restart).

---

## Log Files

```
/tmp/semar-dashboard.log   # Dashboard backend
/tmp/semar-cv.log          # CV Engine
/tmp/semar-frontend.log    # Vite dev server
```

---

## Struktur Database (SQLite WAL)

Shared antara dashboard dan CV engine:

- `cctv_streams` — daftar kamera
- `events` — log alert (ditulis oleh CV engine, dibaca oleh dashboard)

---

## Docker (Opsional)

```bash
# Dashboard + Frontend saja:
docker compose up dashboard frontend

# Semua termasuk CV:
docker compose --profile cv up
```

---

## Optimasi untuk i3 Gen 7

- Model: YOLOv8n (nano) saja — 6MB, tercepat
- Input didownscale ke 416×234 sebelum inference
- `device=cpu`, `half=False` (no FP16 on CPU)
- `conf=0.4` — threshold lebih tinggi = lebih cepat
- Max 2 stream bersamaan
- Interval default 5s (bukan real-time)
- Rotasi otomatis jika stream > max concurrent
