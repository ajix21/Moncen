"""
Dashboard API tests — requires dashboard running on port 8000.
All tests auto-skip if dashboard is unreachable.

Actual response shapes (from dashboard/routers/):
  GET /api/cctvs        → list[CCTVStreamResponse]
  POST /api/cctvs       → CCTVStreamResponse  (201)
  GET /api/events       → EventsPage {items, total, page, limit, pages}
  GET /api/stats/summary → {total_streams, enabled_streams, total_events, level_counts, latest_events}
  GET /api/cv/status    → {running: bool, streams_active: int, uptime_seconds: int}
  GET /health           → {status: "ok"}
"""

import pytest
import httpx

DASH = "http://localhost:8000"


def _skip_if_down():
    try:
        httpx.get(f"{DASH}/health", timeout=2.0)
    except Exception:
        pytest.skip("Dashboard tidak berjalan di port 8000 — jalankan ./start-dashboard.sh")


@pytest.fixture(autouse=True)
def require_dashboard():
    _skip_if_down()


@pytest.fixture
def client():
    with httpx.Client(base_url=DASH, timeout=5.0) as c:
        yield c


@pytest.fixture
def created_cctv(client):
    """Creates a test CCTV record and cleans it up after the test."""
    payload = {
        "name": "TEST_QA_CCTV",
        "location": "QA Lokasi",
        "stream_url": "https://example.com/qa.m3u8",
    }
    r = client.post("/api/cctvs", json=payload)
    assert r.status_code in (200, 201), f"Gagal membuat test CCTV: {r.text}"
    cctv_id = r.json()["id"]
    yield cctv_id
    client.delete(f"/api/cctvs/{cctv_id}")


# ── Health ─────────────────────────────────────────────────────────────────────

def test_D01_health_check(client):
    r = client.get("/health")
    assert r.status_code == 200, f"/health return {r.status_code}"
    data = r.json()
    assert "status" in data, "Response /health tidak mengandung field 'status'"
    assert data["status"] == "ok", f"Expected status='ok', dapat '{data['status']}'"


# ── CCTV list ──────────────────────────────────────────────────────────────────

def test_D02_cctv_list_returns_defaults(client):
    r = client.get("/api/cctvs")
    assert r.status_code == 200, f"GET /api/cctvs return {r.status_code}"
    data = r.json()
    assert isinstance(data, list), "GET /api/cctvs harus return list"
    assert len(data) >= 4, f"Harus ada minimal 4 default CCTV, dapat {len(data)}"
    required_fields = {"id", "name", "location", "stream_url", "enabled"}
    for item in data:
        missing = required_fields - set(item.keys())
        assert not missing, f"Field tidak lengkap di CCTV item: {missing}"


# ── CCTV CRUD ──────────────────────────────────────────────────────────────────

def test_D03_add_cctv(client):
    payload = {
        "name": "TEST_QA_ADD",
        "location": "QA",
        "stream_url": "https://example.com/add.m3u8",
    }
    r = client.post("/api/cctvs", json=payload)
    assert r.status_code in (200, 201), f"Gagal tambah CCTV: {r.text}"
    data = r.json()
    assert "id" in data, "Response POST /api/cctvs harus mengandung 'id'"
    assert data["name"] == "TEST_QA_ADD", "Nama CCTV tidak sesuai"
    # cleanup
    client.delete(f"/api/cctvs/{data['id']}")


def test_D04_update_cctv(client, created_cctv):
    r = client.put(f"/api/cctvs/{created_cctv}", json={"name": "TEST_QA_UPDATED"})
    assert r.status_code == 200, f"PUT /api/cctvs/{created_cctv} return {r.status_code}: {r.text}"
    updated = r.json()
    assert updated.get("name") == "TEST_QA_UPDATED", (
        f"Nama tidak terupdate: {updated.get('name')}"
    )


def test_D05_toggle_cctv(client, created_cctv):
    r_list = client.get("/api/cctvs")
    original = next((c for c in r_list.json() if c["id"] == created_cctv), None)
    assert original is not None, "CCTV yang baru dibuat tidak ditemukan di list"
    original_state = original["enabled"]

    r_toggle = client.patch(f"/api/cctvs/{created_cctv}/toggle")
    assert r_toggle.status_code == 200, f"PATCH toggle return {r_toggle.status_code}"

    r_list2 = client.get("/api/cctvs")
    updated = next((c for c in r_list2.json() if c["id"] == created_cctv), None)
    assert updated is not None, "CCTV tidak ditemukan setelah toggle"
    assert updated["enabled"] != original_state, (
        f"Toggle tidak mengubah status: masih {updated['enabled']}"
    )


def test_D06_delete_cctv(client):
    payload = {
        "name": "TEST_QA_DELETE",
        "location": "QA",
        "stream_url": "https://example.com/del.m3u8",
    }
    r_create = client.post("/api/cctvs", json=payload)
    assert r_create.status_code in (200, 201), f"Gagal buat CCTV: {r_create.text}"
    cctv_id = r_create.json()["id"]

    r_delete = client.delete(f"/api/cctvs/{cctv_id}")
    assert r_delete.status_code in (200, 204), f"DELETE return {r_delete.status_code}"

    r_list = client.get("/api/cctvs")
    ids_after = [c["id"] for c in r_list.json()]
    assert cctv_id not in ids_after, "CCTV yang sudah dihapus masih muncul di list"


# ── Events ─────────────────────────────────────────────────────────────────────

def test_D07_events_paginated(client):
    """GET /api/events returns EventsPage with items, total, page, limit, pages."""
    r = client.get("/api/events?page=1&limit=10")
    assert r.status_code == 200, f"GET /api/events return {r.status_code}"
    data = r.json()
    assert isinstance(data, dict), "GET /api/events harus return dict (EventsPage)"
    assert "items" in data, "EventsPage harus mengandung field 'items'"
    assert "total" in data, "EventsPage harus mengandung field 'total'"
    assert "page" in data, "EventsPage harus mengandung field 'page'"
    assert "limit" in data, "EventsPage harus mengandung field 'limit'"
    assert isinstance(data["items"], list), "'items' harus berupa list"
    assert len(data["items"]) <= 10, (
        f"Dengan limit=10, items tidak boleh lebih dari 10, dapat {len(data['items'])}"
    )


def test_D08_events_filter_by_level(client):
    """Events dapat difilter berdasarkan level."""
    for level in ["NORMAL", "WASPADA", "SIAGA", "DARURAT"]:
        r = client.get(f"/api/events?level={level}&limit=5")
        assert r.status_code == 200, f"Filter level={level} return {r.status_code}"
        data = r.json()
        for evt in data.get("items", []):
            assert evt["alert_level"] == level, (
                f"Filter level={level} mengembalikan event dengan level {evt['alert_level']}"
            )


# ── CV status proxy ────────────────────────────────────────────────────────────

def test_D09_cv_status_always_200(client):
    """CRITICAL: /api/cv/status harus selalu return 200, bahkan saat CV engine mati."""
    r = client.get("/api/cv/status")
    assert r.status_code == 200, (
        f"CRITICAL: /api/cv/status return {r.status_code} — "
        "harus selalu 200 bahkan saat CV engine tidak berjalan"
    )
    data = r.json()
    assert "running" in data, "Response /api/cv/status harus mengandung field 'running'"
    assert isinstance(data["running"], bool), f"'running' harus bool, dapat {type(data['running'])}"
    assert "streams_active" in data, "Response harus mengandung 'streams_active'"


# ── Stats ──────────────────────────────────────────────────────────────────────

def test_D10_stats_summary_schema(client):
    r = client.get("/api/stats/summary")
    assert r.status_code == 200, f"GET /api/stats/summary return {r.status_code}"
    data = r.json()
    required = {"total_streams", "enabled_streams", "total_events", "level_counts"}
    missing = required - set(data.keys())
    assert not missing, f"Field stats summary tidak lengkap: {missing}"
    assert isinstance(data["total_streams"], int), "'total_streams' harus int"
    assert isinstance(data["enabled_streams"], int), "'enabled_streams' harus int"
    assert data["enabled_streams"] <= data["total_streams"], (
        "enabled_streams tidak boleh lebih besar dari total_streams"
    )
    level_counts = data["level_counts"]
    for level in ["normal", "waspada", "siaga", "darurat"]:
        assert level in level_counts, f"level_counts tidak mengandung '{level}'"


# ── Error handling ─────────────────────────────────────────────────────────────

def test_D11_invalid_uuid_returns_404_not_500(client):
    r = client.get("/api/cctvs/invalid-uuid-format")
    assert r.status_code in (404, 422), (
        f"UUID tidak valid harus return 404/422, bukan {r.status_code}"
    )
    assert r.status_code != 500, (
        f"CRITICAL: Server error 500 pada input tidak valid — harus ditangani dengan 4xx"
    )


def test_D12_missing_required_fields_returns_422(client):
    """POST tanpa field wajib harus return 422 Unprocessable Entity."""
    r = client.post("/api/cctvs", json={"name": "Only Name"})
    assert r.status_code == 422, (
        f"Request tanpa field wajib harus return 422, dapat {r.status_code}"
    )


def test_D13_delete_nonexistent_returns_404(client):
    r = client.delete("/api/cctvs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404, (
        f"Delete ID tidak ada harus return 404, dapat {r.status_code}"
    )
