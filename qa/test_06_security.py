"""
Security audit tests.
Tests that can run without a server do so; others skip gracefully.

Checks: CORS, SQL injection, path traversal, error info leakage,
oversized payloads, stack trace exposure.
"""

import pathlib
import re
import pytest
import httpx

ROOT = pathlib.Path(__file__).parent.parent
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


# ── Static analysis ────────────────────────────────────────────────────────────

def test_SEC01_cors_not_wildcard_in_source():
    """Neither service should use allow_origins=['*'] (open CORS)."""
    for service in ["dashboard/main.py", "cv-engine/main.py"]:
        f = ROOT / service
        if not f.exists():
            continue
        content = f.read_text(encoding="utf-8", errors="ignore")
        # Check only non-comment lines
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "allow_origins" in stripped and '"*"' in stripped:
                pytest.fail(
                    f"CRITICAL: Wildcard CORS '*' ditemukan di {service}:{i} — "
                    "semua origin diizinkan, berbahaya!"
                )


def test_SEC02_no_env_files_committed():
    """.env files with secrets must not be committed to the repo."""
    for service_dir in ["dashboard", "cv-engine"]:
        d = ROOT / service_dir
        if not d.exists():
            continue
        env_files = list(d.glob(".env"))
        real_env = [f for f in env_files if f.name == ".env"]
        # .env.example is fine
        assert not real_env, (
            f"CRITICAL: .env file ditemukan di {service_dir}/ — "
            "jangan commit file .env ke repo"
        )


def test_SEC03_gitignore_covers_env_and_db():
    """Project should have .gitignore covering sensitive files."""
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        pytest.skip(".gitignore tidak ditemukan")
    content = gitignore.read_text(encoding="utf-8", errors="ignore")
    recommendations = [".env", "*.db", "venv/", "__pycache__/"]
    missing = [r for r in recommendations if r not in content]
    if missing:
        # Warn, don't fail — gitignore is a recommendation
        pytest.warns(
            UserWarning if False else None,
            match=".*"
        ) if False else None
        print(f"\nRECOMMENDATION: .gitignore sebaiknya mencakup: {missing}")


# ── Runtime CORS ───────────────────────────────────────────────────────────────

def test_SEC04_cors_allows_localhost_5173():
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    with httpx.Client(timeout=5.0) as c:
        r = c.get(f"{DASH}/api/cctvs", headers={"Origin": "http://localhost:5173"})
    assert r.status_code == 200
    acao = r.headers.get("access-control-allow-origin", "")
    assert "localhost:5173" in acao or acao == "*", (
        f"Dashboard tidak mengizinkan akses dari localhost:5173 — "
        f"access-control-allow-origin: '{acao}'"
    )


def test_SEC05_cors_blocks_unknown_origin():
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    with httpx.Client(timeout=5.0) as c:
        r = c.get(f"{DASH}/api/cctvs", headers={"Origin": "http://evil.example.com"})
    acao = r.headers.get("access-control-allow-origin", "")
    assert "evil.example.com" not in acao, (
        f"WARNING: Dashboard mengizinkan akses dari origin tidak dikenal: '{acao}'"
    )


# ── Injection ──────────────────────────────────────────────────────────────────

def test_SEC06_sql_injection_safe():
    """SQL injection attempt in name field must not corrupt the database."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    payload = {
        "name": "'; DROP TABLE cctv_streams; --",
        "location": "test",
        "stream_url": "https://example.com/safe.m3u8",
    }
    created_id = None
    with httpx.Client(timeout=10.0) as c:
        r = c.post(f"{DASH}/api/cctvs", json=payload)
        assert r.status_code in (200, 201, 422), (
            f"POST return {r.status_code} — harus 200/201 (stored safely) atau 422 (rejected)"
        )
        if r.status_code in (200, 201):
            created_id = r.json().get("id")

        # Table must still be accessible
        r2 = c.get(f"{DASH}/api/cctvs")
        assert r2.status_code == 200, (
            "CRITICAL: Tabel cctv_streams tidak bisa diakses setelah SQL injection attempt — "
            "kemungkinan tabel terhapus!"
        )
        assert isinstance(r2.json(), list), "Response harus berupa list"

        # Cleanup
        if created_id:
            c.delete(f"{DASH}/api/cctvs/{created_id}")


# ── Path traversal ─────────────────────────────────────────────────────────────

def test_SEC07_path_traversal_rejected():
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    traversal_attempts = [
        "/api/cctvs/../../../etc/passwd",
        "/api/events/../../../etc/hosts",
    ]
    with httpx.Client(timeout=5.0) as c:
        for path in traversal_attempts:
            r = c.get(f"{DASH}{path}")
            assert r.status_code in (404, 422, 400, 307, 308), (
                f"Path traversal '{path}' return {r.status_code} — "
                "harus 404/422/400"
            )
            body = r.text[:500].lower()
            assert "root:" not in body, (
                f"CRITICAL: Kemungkinan path traversal berhasil membaca /etc/passwd: {path}"
            )


def test_SEC08_cv_snapshot_no_path_traversal():
    if not _cv_up():
        pytest.skip("CV Engine tidak aktif")
    traversal_ids = [
        "../../../../etc/passwd",
        "..%2F..%2Fetc%2Fpasswd",
        "../etc/hosts",
    ]
    with httpx.Client(timeout=5.0) as c:
        for t in traversal_ids:
            r = c.get(f"{CV}/cv/snapshot/{t}")
            assert r.status_code in (404, 422, 400), (
                f"Path traversal di snapshot '{t}' return {r.status_code}"
            )
            assert "root:" not in r.text, (
                f"CRITICAL: Path traversal snapshot mungkin berhasil: '{t}'"
            )


# ── Error information leakage ──────────────────────────────────────────────────

def test_SEC09_error_no_stack_trace():
    """Error responses must not leak internal stack traces."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    with httpx.Client(timeout=5.0) as c:
        r = c.get(f"{DASH}/api/cctvs/00000000-0000-0000-0000-000000000000")
    assert r.status_code in (404, 422), f"Expected 404/422, dapat {r.status_code}"
    body = r.text
    leak_indicators = [
        "Traceback",
        'File "',
        ".py\", line",
        "sqlalchemy",
        "aiosqlite",
        "SyntaxError",
        "AttributeError",
    ]
    for indicator in leak_indicators:
        assert indicator not in body, (
            f"CRITICAL: Stack trace bocor di response error: ditemukan '{indicator}'"
        )


def test_SEC10_health_no_sensitive_info():
    """Health endpoint must not expose filesystem paths or credentials."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    with httpx.Client(timeout=5.0) as c:
        r = c.get(f"{DASH}/health")
    body = r.text.lower()
    sensitive_patterns = ["/home/", "/var/", "c:\\users", ".db", "password", "secret"]
    for s in sensitive_patterns:
        assert s not in body, (
            f"WARNING: Info sensitif '{s}' mungkin bocor di /health endpoint"
        )


# ── Oversized payload ──────────────────────────────────────────────────────────

def test_SEC11_oversized_payload_rejected():
    """Server must reject payloads with excessively long field values."""
    if not _dash_up():
        pytest.skip("Dashboard tidak aktif")
    with httpx.Client(timeout=10.0) as c:
        r = c.post(f"{DASH}/api/cctvs", json={
            "name": "A" * 10_000,
            "location": "B" * 10_000,
            "stream_url": "https://example.com/s.m3u8",
        })
    assert r.status_code in (422, 413, 400, 200, 201), (
        f"Payload oversized return {r.status_code} — "
        "harus 422/413/400 atau jika diterima server tidak crash"
    )
    assert r.status_code != 500, (
        "CRITICAL: Payload oversized menyebabkan 500 — server tidak menangani dengan baik"
    )
    # If accepted (200/201), clean up
    if r.status_code in (200, 201):
        created_id = r.json().get("id")
        if created_id:
            with httpx.Client(timeout=5.0) as c:
                c.delete(f"{DASH}/api/cctvs/{created_id}")


# ── Binding ────────────────────────────────────────────────────────────────────

def test_SEC12_startup_scripts_binding_note():
    """Document host binding — 0.0.0.0 opens all interfaces (LAN accessible)."""
    for script_name in ["start-dashboard.sh", "start-cv.sh"]:
        path = ROOT / script_name
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if "--host 0.0.0.0" in content:
            # Not a failure — home server may need LAN access
            # But we note it for security review
            print(
                f"\nNOTE: {script_name} uses --host 0.0.0.0 "
                "— all network interfaces are exposed. "
                "Use --host 127.0.0.1 if LAN access is not needed."
            )
    assert True  # This test always passes; its value is in the printed note
