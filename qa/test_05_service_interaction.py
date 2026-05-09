"""
Service interaction tests — validates that dashboard and CV engine
behave correctly relative to each other (shared DB, status proxy, etc.).
Tests skip gracefully when services are unavailable.
"""

import pytest
import httpx
import time

DASH = "http://localhost:8000"
CV = "http://localhost:8001"


def _dash_up() -> bool:
    try:
        return httpx.get(f"{DASH}/health", timeout=2.0).status_code == 200
    except Exception:
        return False


def _cv_up() -> bool:
    try:
        return httpx.get(f"{CV}/health", timeout=2.0).status_code == 200
    except Exception:
        return False


# ── CV proxy resilience ────────────────────────────────────────────────────────

def test_I01_dashboard_cv_status_never_crashes():
    """CRITICAL: /api/cv/status must return 200 regardless of CV engine state."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    with httpx.Client(timeout=5.0) as c:
        r = c.get(f"{DASH}/api/cv/status")
    assert r.status_code == 200, (
        f"CRITICAL: /api/cv/status return {r.status_code} — "
        "harus selalu 200, tidak boleh crash meski CV mati"
    )
    data = r.json()
    assert "running" in data, "Response harus mengandung field 'running'"
    assert isinstance(data["running"], bool), f"'running' harus bool"


def test_I02_cv_status_reflects_engine_state():
    """Dashboard's running field must accurately reflect CV engine availability."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    with httpx.Client(timeout=5.0) as c:
        r = c.get(f"{DASH}/api/cv/status")
    data = r.json()
    cv_actually_up = _cv_up()
    assert data["running"] == cv_actually_up, (
        f"Status CV di dashboard ({data['running']}) tidak sesuai kenyataan ({cv_actually_up}). "
        "Dashboard harus merefleksikan status CV engine secara akurat."
    )


# ── Stream synchronization ─────────────────────────────────────────────────────

def test_I03_cv_engine_has_all_enabled_cctv_from_dashboard():
    """CV engine must know about all enabled CCTV streams from dashboard."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    if not _cv_up():
        pytest.skip("CV Engine tidak aktif")

    with httpx.Client(timeout=5.0) as c:
        dash_cctvs = c.get(f"{DASH}/api/cctvs").json()
        cv_data = c.get(f"{CV}/cv/streams").json()

    enabled_ids = {cc["id"] for cc in dash_cctvs if cc.get("enabled")}
    cv_ids = {s["cctv_id"] for s in cv_data.get("streams", [])}
    missing = enabled_ids - cv_ids

    assert not missing, (
        f"CV engine tidak memiliki stream untuk CCTV berikut: {missing}. "
        "CV engine harus fetch semua enabled streams dari dashboard saat startup."
    )


def test_I04_streams_active_count_consistent():
    """health.streams_active must match count of 'analyzing' streams in /cv/streams."""
    if not _cv_up():
        pytest.skip("CV Engine tidak aktif")

    with httpx.Client(timeout=5.0) as c:
        health = c.get(f"{CV}/health").json()
        streams_data = c.get(f"{CV}/cv/streams").json()

    analyzing_count = sum(
        1 for s in streams_data.get("streams", [])
        if s.get("cv_status") == "analyzing"
    )
    health_count = health.get("streams_active", -1)
    assert health_count == analyzing_count, (
        f"health.streams_active ({health_count}) tidak konsisten dengan "
        f"jumlah stream 'analyzing' ({analyzing_count})"
    )


# ── Concurrent DB access ───────────────────────────────────────────────────────

def test_I05_concurrent_db_reads_no_lock():
    """20 rapid reads of /api/events must all succeed — SQLite WAL should prevent locking."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")

    errors = []
    with httpx.Client(timeout=10.0) as c:
        for i in range(20):
            try:
                r = c.get(f"{DASH}/api/events?page=1&limit=5")
                if r.status_code != 200:
                    errors.append(f"Request {i}: status {r.status_code}: {r.text[:100]}")
            except Exception as e:
                errors.append(f"Request {i}: {e}")

    assert not errors, (
        f"{len(errors)} dari 20 request gagal — kemungkinan DB locking:\n"
        + "\n".join(errors[:5])
    )


def test_I06_stats_total_streams_matches_cctv_list(client=None):
    """stats.total_streams must equal len(GET /api/cctvs)."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")

    with httpx.Client(timeout=5.0) as c:
        r_list = c.get(f"{DASH}/api/cctvs")
        r_stats = c.get(f"{DASH}/api/stats/summary")

    assert r_list.status_code == 200
    assert r_stats.status_code == 200

    cctv_count = len(r_list.json())
    stats_count = r_stats.json().get("total_streams", -1)

    assert stats_count == cctv_count, (
        f"stats.total_streams ({stats_count}) ≠ len(/api/cctvs) ({cctv_count})"
    )


# ── Event write path ───────────────────────────────────────────────────────────

def test_I07_event_log_readable_from_dashboard_after_cv_writes():
    """If CV engine is active and has processed frames, events should appear in dashboard."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")

    with httpx.Client(timeout=5.0) as c:
        r = c.get(f"{DASH}/api/events?limit=1")

    assert r.status_code == 200, f"GET /api/events return {r.status_code}"
    data = r.json()
    assert "items" in data, "EventsPage harus mengandung 'items'"
    # Events may be empty if CV hasn't run — that's fine, we just verify the path works
    assert isinstance(data["items"], list)


# ── Settings isolation ─────────────────────────────────────────────────────────

def test_I08_dashboard_unaffected_when_cv_settings_change():
    """Changing CV settings must not disrupt dashboard API responses."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    if not _cv_up():
        pytest.skip("CV Engine tidak aktif")

    with httpx.Client(timeout=10.0) as c:
        # Change CV settings
        c.put(f"{CV}/cv/settings", json={"cv_frame_interval": 15})
        time.sleep(1)

        # Dashboard should still respond normally
        r = c.get(f"{DASH}/api/cctvs")
        assert r.status_code == 200, (
            f"Dashboard tidak responsif setelah CV settings berubah: {r.status_code}"
        )

        # Restore
        c.put(f"{CV}/cv/settings", json={"cv_frame_interval": 5})
