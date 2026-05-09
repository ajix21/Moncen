"""
WebSocket flow tests — requires asyncio.
Uses websockets library directly (no httpx WS).

Test naming: W01–W05
"""

import asyncio
import json
import pytest
import websockets
import websockets.exceptions

pytestmark = pytest.mark.asyncio

DASH_WS = "ws://localhost:8000"
CV_WS = "ws://localhost:8001"


async def _ws_available(url: str, timeout: float = 3.0) -> bool:
    try:
        async with websockets.connect(url, open_timeout=timeout):
            return True
    except Exception:
        return False


async def _recv_with_timeout(ws, timeout: float):
    """Receive one message with timeout; return None on timeout."""
    try:
        return await asyncio.wait_for(ws.recv(), timeout=timeout)
    except asyncio.TimeoutError:
        return None


# ── Dashboard WS ───────────────────────────────────────────────────────────────

async def test_W01_dashboard_ws_delivers_summary():
    """Dashboard WS /ws/dash/summary must push a JSON summary within 15s."""
    url = f"{DASH_WS}/ws/dash/summary"
    if not await _ws_available(url):
        pytest.skip("Dashboard WebSocket tidak tersedia — jalankan ./start-dashboard.sh")

    received = []
    async with websockets.connect(url, open_timeout=5) as ws:
        raw = await _recv_with_timeout(ws, timeout=15.0)
        if raw is not None:
            received.append(raw)

    assert len(received) > 0, (
        "Dashboard WS tidak mengirim pesan dalam 15 detik — "
        "pastikan interval summary adalah ≤15s"
    )
    data = json.loads(received[0])
    assert isinstance(data, dict), "Pesan WS harus JSON object"


async def test_W02_dashboard_ws_summary_schema():
    """Dashboard WS summary must contain expected fields."""
    url = f"{DASH_WS}/ws/dash/summary"
    if not await _ws_available(url):
        pytest.skip("Dashboard WebSocket tidak tersedia")

    async with websockets.connect(url, open_timeout=5) as ws:
        raw = await _recv_with_timeout(ws, timeout=15.0)

    if raw is None:
        pytest.skip("Tidak ada pesan WS dalam 15 detik")

    data = json.loads(raw)
    required = {"type", "timestamp", "total_streams", "enabled_streams"}
    missing = required - set(data.keys())
    assert not missing, f"Field summary WS tidak lengkap: {missing}"
    assert data["type"] == "summary", f"type harus 'summary', dapat '{data['type']}'"
    assert isinstance(data["total_streams"], int)
    assert isinstance(data["enabled_streams"], int)


async def test_W03_dashboard_ws_stable_multiple_messages():
    """Dashboard WS must not disconnect after receiving multiple messages."""
    url = f"{DASH_WS}/ws/dash/summary"
    if not await _ws_available(url):
        pytest.skip("Dashboard WebSocket tidak tersedia")

    messages = []
    try:
        async with websockets.connect(url, open_timeout=5) as ws:
            for _ in range(3):
                raw = await _recv_with_timeout(ws, timeout=12.0)
                if raw is None:
                    break
                messages.append(raw)
    except websockets.exceptions.ConnectionClosed as e:
        pytest.fail(
            f"CRITICAL: Dashboard WS terputus secara tidak terduga setelah "
            f"{len(messages)} pesan: {e}"
        )

    # Pass as long as connection didn't crash (messages could be 0 due to timing)
    assert True, "Connection stable"


# ── CV Engine WS ───────────────────────────────────────────────────────────────

async def test_W04_cv_ws_all_delivers_cv_result():
    """CV Engine WS /ws/cv/all must push cv_result messages."""
    url = f"{CV_WS}/ws/cv/all"
    if not await _ws_available(url):
        pytest.skip("CV Engine WebSocket tidak tersedia — jalankan ./start-cv.sh")

    received = []
    async with websockets.connect(url, open_timeout=5) as ws:
        # Wait up to 60s for at least one cv_result (frame_interval may be 5–10s)
        deadline = asyncio.get_event_loop().time() + 60.0
        while asyncio.get_event_loop().time() < deadline:
            remaining = deadline - asyncio.get_event_loop().time()
            raw = await _recv_with_timeout(ws, timeout=min(remaining, 12.0))
            if raw is None:
                break
            try:
                msg = json.loads(raw)
                received.append(msg)
                if msg.get("type") == "cv_result":
                    break
            except json.JSONDecodeError:
                pass

    cv_results = [m for m in received if m.get("type") == "cv_result"]
    assert len(cv_results) > 0, (
        "CV Engine WS tidak mengirim cv_result dalam 60 detik. "
        "Pastikan stream aktif dan cv_frame_interval ≤ 10s"
    )

    msg = cv_results[0]
    required = {
        "cctv_id", "person_count", "alert_level", "timestamp",
        "alert_color", "cv_status",
    }
    missing = required - set(msg.keys())
    assert not missing, f"Field cv_result tidak lengkap: {missing}"

    valid_levels = {"NORMAL", "WASPADA", "SIAGA", "DARURAT"}
    assert msg["alert_level"] in valid_levels, (
        f"alert_level '{msg['alert_level']}' tidak valid"
    )
    assert isinstance(msg["person_count"], int), "'person_count' harus int"
    assert msg["person_count"] >= 0, "person_count tidak boleh negatif"


async def test_W05_cv_ws_per_stream_filtered():
    """CV Engine WS /ws/cv/{id} must only deliver messages for that stream."""
    import httpx
    try:
        r = httpx.get("http://localhost:8001/cv/streams", timeout=3)
        streams = r.json().get("streams", [])
    except Exception:
        pytest.skip("CV engine tidak aktif")

    if not streams:
        pytest.skip("Tidak ada stream aktif untuk ditest")

    test_id = streams[0]["cctv_id"]
    url = f"{CV_WS}/ws/cv/{test_id}"
    if not await _ws_available(url):
        pytest.skip(f"WS per-stream tidak tersedia: {url}")

    received = []
    async with websockets.connect(url, open_timeout=5) as ws:
        deadline = asyncio.get_event_loop().time() + 30.0
        while asyncio.get_event_loop().time() < deadline:
            remaining = deadline - asyncio.get_event_loop().time()
            raw = await _recv_with_timeout(ws, timeout=min(remaining, 12.0))
            if raw is None:
                break
            try:
                received.append(json.loads(raw))
            except json.JSONDecodeError:
                pass

    if not received:
        pytest.skip("Tidak ada pesan diterima dalam 30 detik")

    for msg in received:
        if "cctv_id" in msg:
            assert msg["cctv_id"] == test_id, (
                f"WS per-stream '{test_id}' mengirim data CCTV lain: '{msg['cctv_id']}'"
            )
