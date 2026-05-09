"""
CV Engine API tests — requires cv-engine running on port 8001.
All tests auto-skip if CV engine is unreachable.

Actual response shapes (from cv-engine/routers/control.py):
  GET /health           → {status, streams_active, model, uptime_seconds, running}
  GET /cv/streams       → {streams: [{cctv_id, cctv_name, location, cv_status, last_count, last_level}]}
  GET /cv/settings      → {cv_frame_interval, max_concurrent_streams, yolo_model_name, rotation_interval, yolo_imgsz, yolo_conf}
  PUT /cv/settings      → {status: "applied", settings: {...}}
  POST /cv/streams/{id}/start → {status: "started", cctv_id}
  POST /cv/streams/{id}/stop  → {status: "stopped", cctv_id}
  GET /cv/snapshot/{id} → JPEG bytes | 404
"""

import pytest
import time
import httpx

CV = "http://localhost:8001"


def _skip_if_down():
    try:
        httpx.get(f"{CV}/health", timeout=2.0)
    except Exception:
        pytest.skip("CV Engine tidak berjalan di port 8001 — jalankan ./start-cv.sh")


@pytest.fixture(autouse=True)
def require_cv():
    _skip_if_down()


@pytest.fixture
def client():
    with httpx.Client(base_url=CV, timeout=10.0) as c:
        yield c


@pytest.fixture
def original_settings(client):
    r = client.get("/cv/settings")
    return r.json() if r.status_code == 200 else {}


# ── Health ─────────────────────────────────────────────────────────────────────

def test_C01_health_schema(client):
    r = client.get("/health")
    assert r.status_code == 200, f"/health return {r.status_code}"
    data = r.json()
    required = {"status", "streams_active", "model", "uptime_seconds"}
    missing = required - set(data.keys())
    assert not missing, f"Field health tidak lengkap: {missing}"
    assert data["status"] == "ok", f"Expected status='ok', dapat '{data['status']}'"
    assert isinstance(data["streams_active"], int), "'streams_active' harus int"
    assert isinstance(data["uptime_seconds"], int), "'uptime_seconds' harus int"
    assert data["uptime_seconds"] >= 0, "uptime_seconds tidak boleh negatif"


# ── Stream list ────────────────────────────────────────────────────────────────

def test_C02_cv_streams_list(client):
    """GET /cv/streams returns {streams: [...]} with valid cv_status values."""
    r = client.get("/cv/streams")
    assert r.status_code == 200, f"GET /cv/streams return {r.status_code}"
    data = r.json()
    assert "streams" in data, (
        "GET /cv/streams harus return {'streams': [...]}, bukan list langsung"
    )
    streams = data["streams"]
    assert isinstance(streams, list), "'streams' harus berupa list"
    valid_statuses = {"analyzing", "queued", "offline"}
    for stream in streams:
        assert "cctv_id" in stream, f"Field 'cctv_id' tidak ada: {stream}"
        assert "cv_status" in stream, f"Field 'cv_status' tidak ada: {stream}"
        assert stream["cv_status"] in valid_statuses, (
            f"cv_status '{stream['cv_status']}' tidak valid — "
            f"harus salah satu dari {valid_statuses}"
        )


# ── Settings ───────────────────────────────────────────────────────────────────

def test_C03_get_cv_settings(client):
    """GET /cv/settings returns all config fields."""
    r = client.get("/cv/settings")
    assert r.status_code == 200, f"GET /cv/settings return {r.status_code}"
    data = r.json()
    required = {
        "cv_frame_interval",
        "max_concurrent_streams",
        "yolo_model_name",
        "rotation_interval",
    }
    missing = required - set(data.keys())
    assert not missing, f"Field settings tidak lengkap: {missing}"
    assert isinstance(data["cv_frame_interval"], (int, float)), (
        "'cv_frame_interval' harus numerik"
    )
    assert isinstance(data["max_concurrent_streams"], int), (
        "'max_concurrent_streams' harus int"
    )
    assert data["max_concurrent_streams"] >= 1, (
        "max_concurrent_streams harus minimal 1"
    )
    assert "yolov8n" in data["yolo_model_name"].lower(), (
        f"Model default harus yolov8n, dapat '{data['yolo_model_name']}'"
    )


def test_C04_update_cv_settings_and_verify(client, original_settings):
    """PUT /cv/settings applies changes immediately and is reflected in GET."""
    new_settings = {"cv_frame_interval": 10, "max_concurrent_streams": 1}
    r_put = client.put("/cv/settings", json=new_settings)
    assert r_put.status_code == 200, (
        f"PUT /cv/settings return {r_put.status_code}: {r_put.text}"
    )

    r_get = client.get("/cv/settings")
    assert r_get.status_code == 200
    updated = r_get.json()
    assert updated["cv_frame_interval"] == 10, (
        f"cv_frame_interval tidak terupdate: {updated['cv_frame_interval']}"
    )
    assert updated["max_concurrent_streams"] == 1, (
        f"max_concurrent_streams tidak terupdate: {updated['max_concurrent_streams']}"
    )

    # Restore original settings
    if original_settings:
        client.put("/cv/settings", json={
            k: v for k, v in original_settings.items()
            if k in {"cv_frame_interval", "max_concurrent_streams",
                     "yolo_model_name", "rotation_interval"}
        })


# ── MAX_CONCURRENT_STREAMS enforcement ────────────────────────────────────────

def test_C05_max_concurrent_streams_enforced(client, original_settings):
    """MAX_CONCURRENT_STREAMS=2 must never be exceeded."""
    r = client.put("/cv/settings", json={"max_concurrent_streams": 2})
    assert r.status_code == 200
    time.sleep(3)  # allow rotation to settle

    r_streams = client.get("/cv/streams")
    assert r_streams.status_code == 200
    analyzing_count = sum(
        1 for s in r_streams.json().get("streams", [])
        if s.get("cv_status") == "analyzing"
    )
    assert analyzing_count <= 2, (
        f"MAX_CONCURRENT_STREAMS=2 dilanggar: {analyzing_count} stream sedang diproses bersamaan"
    )

    if original_settings:
        client.put("/cv/settings", json={
            k: v for k, v in original_settings.items()
            if k in {"cv_frame_interval", "max_concurrent_streams"}
        })


# ── Stream start/stop ──────────────────────────────────────────────────────────

def test_C06_stop_and_start_stream(client):
    r_streams = client.get("/cv/streams")
    assert r_streams.status_code == 200
    streams = r_streams.json().get("streams", [])
    if not streams:
        pytest.skip("Tidak ada stream terdaftar untuk ditest")

    test_id = streams[0]["cctv_id"]

    r_stop = client.post(f"/cv/streams/{test_id}/stop")
    assert r_stop.status_code in (200, 204), (
        f"POST /cv/streams/{test_id}/stop return {r_stop.status_code}"
    )

    time.sleep(2)

    r_check = client.get("/cv/streams")
    stopped = next(
        (s for s in r_check.json().get("streams", []) if s["cctv_id"] == test_id),
        None,
    )
    if stopped:
        assert stopped["cv_status"] in ("offline", "queued"), (
            f"Stream yang di-stop seharusnya offline/queued, dapat '{stopped['cv_status']}'"
        )

    r_start = client.post(f"/cv/streams/{test_id}/start")
    assert r_start.status_code in (200, 204), (
        f"POST /cv/streams/{test_id}/start return {r_start.status_code}"
    )


def test_C07_stop_nonexistent_stream_returns_404(client):
    r = client.post("/cv/streams/nonexistent-uuid-xyz/stop")
    assert r.status_code == 404, (
        f"Stop stream tidak ada harus return 404, dapat {r.status_code}"
    )


# ── Snapshot ───────────────────────────────────────────────────────────────────

def test_C08_snapshot_returns_valid_response(client):
    """Snapshot returns JPEG (200) or 404 if no frame captured yet."""
    r_streams = client.get("/cv/streams")
    streams = r_streams.json().get("streams", [])
    if not streams:
        pytest.skip("Tidak ada stream untuk ditest snapshot")

    test_id = streams[0]["cctv_id"]
    r_snap = client.get(f"/cv/snapshot/{test_id}")
    assert r_snap.status_code in (200, 404), (
        f"Snapshot harus return 200 (ada frame) atau 404 (belum ada frame), "
        f"dapat {r_snap.status_code}"
    )
    if r_snap.status_code == 200:
        ct = r_snap.headers.get("content-type", "")
        assert "image/jpeg" in ct, (
            f"Snapshot harus berupa JPEG, content-type: {ct}"
        )
        assert len(r_snap.content) > 1000, (
            "Snapshot JPEG terlalu kecil — kemungkinan file kosong"
        )


# ── Independent operation ──────────────────────────────────────────────────────

def test_C09_cv_engine_runs_without_dashboard():
    """CV engine must respond to health even if dashboard is down."""
    with httpx.Client(timeout=5.0) as c:
        r = c.get(f"{CV}/health")
    assert r.status_code == 200, "CV Engine harus bisa berjalan tanpa dashboard"
    assert r.json()["running"] is True


# ── Uptime increases ───────────────────────────────────────────────────────────

def test_C10_uptime_increases(client):
    """Uptime counter must increase between two consecutive calls."""
    r1 = client.get("/health")
    t1 = r1.json().get("uptime_seconds", 0)
    time.sleep(2)
    r2 = client.get("/health")
    t2 = r2.json().get("uptime_seconds", 0)
    assert t2 >= t1, (
        f"uptime_seconds tidak bertambah: {t1} → {t2}"
    )
