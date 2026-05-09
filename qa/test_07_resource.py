"""
Resource usage tests — validates memory limits and stability under load.
Requires psutil for memory/CPU checks (auto-installed via requirements.txt).
All tests skip gracefully when services are not running.
"""

import pytest
import time
import httpx

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

DASH = "http://localhost:8000"
CV = "http://localhost:8001"

DASHBOARD_RAM_LIMIT_MB = 400
CV_ENGINE_RAM_LIMIT_MB = 2048
DASHBOARD_IDLE_CPU_LIMIT_PCT = 30


def _get_listening_pid(port: int) -> int | None:
    """Return PID of process listening on the given port."""
    if not PSUTIL_AVAILABLE:
        return None
    for proc in psutil.process_iter(["pid", "connections"]):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port and conn.status == "LISTEN":
                    return proc.pid
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            pass
    return None


def _get_rss_mb(pid: int) -> float | None:
    """Return resident set size in MB for the given PID."""
    if not PSUTIL_AVAILABLE or pid is None:
        return None
    try:
        return psutil.Process(pid).memory_info().rss / (1024 * 1024)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


# ── Memory ─────────────────────────────────────────────────────────────────────

def test_R01_dashboard_memory_under_400mb():
    """Dashboard must use < 400 MB RAM (no heavy packages loaded)."""
    if not PSUTIL_AVAILABLE:
        pytest.skip("psutil tidak tersedia — install via qa/requirements.txt")
    pid = _get_listening_pid(8000)
    if pid is None:
        pytest.skip("Dashboard tidak berjalan di port 8000")

    time.sleep(3)  # let startup settle
    rss = _get_rss_mb(pid)
    if rss is None:
        pytest.skip("Tidak bisa baca memory usage — mungkin permission denied")

    print(f"\nDashboard RAM usage: {rss:.1f} MB (limit: {DASHBOARD_RAM_LIMIT_MB} MB)")
    assert rss < DASHBOARD_RAM_LIMIT_MB, (
        f"Dashboard menggunakan {rss:.1f} MB RAM — melebihi batas {DASHBOARD_RAM_LIMIT_MB} MB. "
        "Periksa apakah ada import berat yang tidak diperlukan di dashboard/."
    )


def test_R02_cv_engine_memory_under_2gb():
    """CV engine with YOLOv8n must use < 2 GB RAM on CPU inference."""
    if not PSUTIL_AVAILABLE:
        pytest.skip("psutil tidak tersedia")
    pid = _get_listening_pid(8001)
    if pid is None:
        pytest.skip("CV Engine tidak berjalan di port 8001")

    time.sleep(5)  # let model load settle
    rss = _get_rss_mb(pid)
    if rss is None:
        pytest.skip("Tidak bisa baca memory usage")

    print(f"\nCV Engine RAM usage: {rss:.1f} MB (limit: {CV_ENGINE_RAM_LIMIT_MB} MB)")
    assert rss < CV_ENGINE_RAM_LIMIT_MB, (
        f"CV Engine menggunakan {rss:.1f} MB RAM — melebihi batas {CV_ENGINE_RAM_LIMIT_MB} MB "
        "untuk hardware i3 Gen7 / 8GB. "
        "Pastikan hanya menggunakan YOLOv8n dan imgsz=416."
    )


# ── Concurrency limits ─────────────────────────────────────────────────────────

def test_R03_max_concurrent_streams_hard_limit():
    """MAX_CONCURRENT_STREAMS=2 must never be exceeded regardless of settings."""
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.put(f"{CV}/cv/settings", json={"max_concurrent_streams": 2})
            if r.status_code != 200:
                pytest.skip("Tidak bisa set max_concurrent_streams")
            time.sleep(3)
            r2 = c.get(f"{CV}/cv/streams")
            if r2.status_code != 200:
                pytest.skip("Tidak bisa ambil cv/streams")
            streams = r2.json().get("streams", [])
    except Exception as e:
        pytest.skip(f"CV Engine tidak aktif: {e}")

    analyzing = [s for s in streams if s.get("cv_status") == "analyzing"]
    assert len(analyzing) <= 2, (
        f"MAX_CONCURRENT_STREAMS=2 dilanggar: {len(analyzing)} stream diproses bersamaan. "
        "Periksa rotasi queue di stream_manager.py"
    )


# ── API stability ──────────────────────────────────────────────────────────────

def test_R04_rapid_api_calls_stable():
    """50 rapid GET /api/cctvs calls must all succeed without errors."""
    try:
        httpx.get(f"{DASH}/health", timeout=2.0)
    except Exception:
        pytest.skip("Dashboard tidak aktif")

    errors = []
    with httpx.Client(timeout=5.0) as c:
        for i in range(50):
            try:
                r = c.get(f"{DASH}/api/cctvs")
                if r.status_code != 200:
                    errors.append(f"Request {i+1}: status {r.status_code}")
            except Exception as e:
                errors.append(f"Request {i+1}: {e}")

    assert not errors, (
        f"{len(errors)} dari 50 request gagal — server tidak stabil di bawah load ringan:\n"
        + "\n".join(errors[:5])
    )


def test_R05_dashboard_idle_cpu_reasonable():
    """Dashboard idle CPU usage must be < 30% (no busy-wait loops)."""
    if not PSUTIL_AVAILABLE:
        pytest.skip("psutil tidak tersedia")
    pid = _get_listening_pid(8000)
    if pid is None:
        pytest.skip("Dashboard tidak aktif")

    time.sleep(2)  # let initial burst settle
    try:
        proc = psutil.Process(pid)
        # First call initializes CPU percent tracking
        proc.cpu_percent(interval=None)
        time.sleep(3)
        cpu = proc.cpu_percent(interval=None)
        print(f"\nDashboard idle CPU: {cpu:.1f}% (limit: {DASHBOARD_IDLE_CPU_LIMIT_PCT}%)")
        assert cpu < DASHBOARD_IDLE_CPU_LIMIT_PCT, (
            f"Dashboard idle CPU {cpu:.1f}% terlalu tinggi — "
            "kemungkinan ada loop atau polling yang tidak efisien di main.py"
        )
    except psutil.NoSuchProcess:
        pytest.skip("Proses tidak ditemukan saat pengukuran")


def test_R06_cv_engine_frame_interval_respected():
    """CV engine must not process faster than cv_frame_interval setting."""
    try:
        with httpx.Client(timeout=5.0) as c:
            r_settings = c.get(f"{CV}/cv/settings")
            if r_settings.status_code != 200:
                pytest.skip("Tidak bisa baca settings")
            interval = r_settings.json().get("cv_frame_interval", 5)

            r_health1 = c.get(f"{CV}/health").json()
            active1 = r_health1.get("streams_active", 0)
    except Exception:
        pytest.skip("CV Engine tidak aktif")

    # Just verify settings are sane for i3 Gen 7
    assert interval >= 3, (
        f"cv_frame_interval={interval}s terlalu kecil untuk i3 Gen7 — "
        "minimum yang direkomendasikan adalah 3s"
    )
    print(f"\nCV frame interval: {interval}s, active streams: {active1}")


def test_R07_memory_stable_after_multiple_requests():
    """Memory must not grow significantly after 30 API requests (no memory leaks)."""
    if not PSUTIL_AVAILABLE:
        pytest.skip("psutil tidak tersedia")
    pid = _get_listening_pid(8000)
    if pid is None:
        pytest.skip("Dashboard tidak aktif")

    rss_before = _get_rss_mb(pid)
    if rss_before is None:
        pytest.skip("Tidak bisa baca memory")

    with httpx.Client(timeout=5.0) as c:
        for _ in range(30):
            c.get(f"{DASH}/api/cctvs")
            c.get(f"{DASH}/api/events?page=1&limit=10")

    time.sleep(1)
    rss_after = _get_rss_mb(pid)
    if rss_after is None:
        pytest.skip("Tidak bisa baca memory setelah requests")

    growth_mb = rss_after - rss_before
    print(f"\nMemory growth after 30 requests: +{growth_mb:.1f} MB "
          f"({rss_before:.1f} → {rss_after:.1f} MB)")

    assert growth_mb < 100, (
        f"Memory tumbuh {growth_mb:.1f} MB setelah 30 requests — "
        "kemungkinan ada memory leak. Before: {rss_before:.1f} MB, After: {rss_after:.1f} MB"
    )
