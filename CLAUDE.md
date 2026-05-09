# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Semar Watch v2** — CCTV monitoring + crowd analysis system for Kota Semarang. Split-service architecture: a lightweight always-on dashboard (port 8000) and an on-demand CV engine (port 8001), connected via shared SQLite in WAL mode. Target hardware: Intel i3 Gen 7, 8GB RAM.

## Commands

### Setup (first time)
```bash
bash setup.sh          # creates venvs, installs deps, seeds DB
```

### Running services
```bash
bash start-dashboard.sh   # Dashboard API (8000) + Vite frontend (5173)
bash start-cv.sh          # CV Engine (8001) — on-demand, resource-intensive
bash start-all.sh         # Both services together
bash stop-cv.sh           # Stop CV Engine via PID file
bash stop-all.sh          # Stop all services via PID files
```

Logs: `/tmp/semar-dashboard.log`, `/tmp/semar-cv.log`, `/tmp/semar-frontend.log`

### Frontend development
```bash
cd frontend
npm run dev      # Vite dev server (port 5173)
npm run build    # tsc + vite build
npm run lint     # ESLint
```

### QA tests
```bash
cd qa
bash setup_qa.sh                   # install QA venv (once)
bash run_qa.sh --structure-only    # 51 structural tests, no server needed
bash run_qa.sh --security-only     # security checks
bash run_qa.sh                     # full suite (requires bash start-all.sh first)
```

To run a single test file from the repo root:
```bash
cd qa && source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
python -m pytest test_01_structure.py::test_name -v
```

### Windows Git Bash notes
- Venv activation: `source venv/Scripts/activate 2>/dev/null || source venv/bin/activate`
- Use `python`/`pip` (not `python3`/`pip3`)
- `pkill` is not available — all stop scripts use PID files (`/tmp/semar-*.pid`)
- FFmpeg must be in PATH for CV engine HLS capture (`cv2.CAP_FFMPEG`)

## Architecture

```
Frontend (React/Vite :5173)
    │ /api/*  ──────────────→ Dashboard (:8000)  ─── shared/semar_watch.db
    │ /cv/*   ──────────────→ CV Engine (:8001)  ───╯  (SQLite WAL mode)
    │ /ws/dash/* ──────────→ Dashboard WS
    │ /ws/cv/*  ───────────→ CV Engine WS
```

Vite proxies all `/api`, `/cv`, `/ws/dash`, `/ws/cv` paths — the frontend never directly references backend ports.

### Dashboard (`dashboard/`)
- FastAPI with SQLAlchemy async + aiosqlite
- Routers: `cctv.py` (CRUD), `events.py` (paginated log), `cv_proxy.py` (proxies `/api/cv/status` to CV engine, always returns HTTP 200)
- WebSocket `/ws/dash/summary` — broadcasts stats to all clients every 10s; one DB query per broadcast cycle (not per client)
- DB path computed from `Path(__file__).parent.parent / "shared" / "semar_watch.db"` — never relative CWD

### CV Engine (`cv-engine/`)
- Loads CCTV list from Dashboard API at startup; falls back to direct SQLite query if dashboard unreachable
- `StreamManager` maintains `_active_ids` (max 2) and `_queue`, rotates every 60s via asyncio task
- `_write_event()` uses a shared async SQLAlchemy engine (lazy-initialized once, disposed on shutdown)
- `cv_engine.py`: `extract_frame_from_hls()` → OpenCV/FFmpeg → `run_inference()` → YOLOv8n on 416×234 downscaled frame → bounding boxes scaled back to original size
- `check_ffmpeg_available()` runs at startup and logs WARNING if FFmpeg not found
- `PUT /cv/settings` mutates `settings` object directly and calls `restart_with_settings()`; validated with Pydantic `Field(gt=0, le=60)` etc.

### Frontend (`frontend/src/`)
- **Stores** (Zustand): `cctvStore` (stream list, fetched once), `alertStore` (per-stream CV results with `bounding_boxes`), `cvStore` (engine running state)
- **`useCVEngine` hook**: polls `/api/cv/status` every 10s, connects WebSocket to `/ws/cv/all` only when `running === true`, dispatches `updateAlert()` on each `cv_result` message
- **`useWebSocket` hook**: manages WS lifecycle, reconnects on close
- Path alias `@/` maps to `frontend/src/`

### Shared database
Both services read/write the same SQLite file. WAL mode (`PRAGMA journal_mode=WAL`) allows concurrent reads. CV engine writes to `events` table; dashboard reads it. Dashboard writes/reads `cctv_streams`.

### Alert levels
Defined in `cv-engine/config.py`:

| Level    | Person count | Hex color |
|----------|-------------|-----------|
| NORMAL   | 0–49        | `#10b981` |
| WASPADA  | 50–199      | `#f59e0b` |
| SIAGA    | 200–999     | `#f97316` |
| DARURAT  | ≥1000       | `#ef4444` |

## Key constraints

- **YOLO model**: only `yolov8n.pt` (nano). Never use medium/large — i3 Gen 7 CPU cannot handle them
- `cv_frame_interval` valid range: `(0, 60]` seconds; `max_concurrent_streams` valid range: `[1, 10]`
- `models_dir` and `database_url` in both `config.py` files use absolute paths derived from `Path(__file__).parent.parent` — do not change to relative paths
- CV engine settings mutations are not protected by a lock — avoid concurrent `PUT /cv/settings` calls
- Docker: CV engine is in the `cv` profile (`docker compose --profile cv up`)
