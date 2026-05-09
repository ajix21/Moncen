"""
Structural checks — no server needed.
Validates file existence, forbidden imports, no hardcoded ports, and dependency hygiene.
"""

import pathlib
import re
import pytest

ROOT = pathlib.Path(__file__).parent.parent

REQUIRED_FILES = [
    "dashboard/main.py",
    "dashboard/config.py",
    "dashboard/database.py",
    "dashboard/models/__init__.py",
    "dashboard/models/cctv.py",
    "dashboard/models/event.py",
    "dashboard/routers/__init__.py",
    "dashboard/routers/cctv.py",
    "dashboard/routers/events.py",
    "dashboard/routers/cv_proxy.py",
    "dashboard/requirements.txt",
    "cv-engine/main.py",
    "cv-engine/config.py",
    "cv-engine/services/__init__.py",
    "cv-engine/services/cv_engine.py",
    "cv-engine/services/stream_manager.py",
    "cv-engine/services/alert_service.py",
    "cv-engine/routers/__init__.py",
    "cv-engine/routers/stream.py",
    "cv-engine/routers/control.py",
    "cv-engine/requirements.txt",
    "frontend/package.json",
    "frontend/vite.config.ts",
    "frontend/src/App.tsx",
    "start-dashboard.sh",
    "start-cv.sh",
    "stop-cv.sh",
    "setup.sh",
]

REQUIRED_DIRS = [
    "shared",
    "models",
    "frontend/src/components",
    "frontend/src/store",
]

# Imports forbidden in dashboard/ Python files (dashboard must stay lightweight)
DASHBOARD_FORBIDDEN_IMPORTS = ["cv2", "ultralytics", "import av", "import torch"]

# Cross-service imports forbidden in cv-engine/
CV_FORBIDDEN_CROSS_IMPORTS = ["from dashboard", "import dashboard"]

# Hardcoded backend ports forbidden in frontend TypeScript source
FRONTEND_FORBIDDEN_HARDCODE = [
    "localhost:8001",
    "127.0.0.1:8001",
    "localhost:8000",
    "127.0.0.1:8000",
]


# ── File/Directory existence ───────────────────────────────────────────────────

@pytest.mark.parametrize("filepath", REQUIRED_FILES)
def test_required_file_exists(filepath):
    target = ROOT / filepath
    assert target.exists(), f"File tidak ditemukan: {filepath}"


@pytest.mark.parametrize("dirpath", REQUIRED_DIRS)
def test_required_dir_exists(dirpath):
    target = ROOT / dirpath
    assert target.is_dir(), f"Directory tidak ditemukan: {dirpath}"


# ── Import isolation ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("forbidden", DASHBOARD_FORBIDDEN_IMPORTS)
def test_dashboard_no_heavy_imports(forbidden):
    """Dashboard Python files must never import heavy CV packages."""
    dashboard_dir = ROOT / "dashboard"
    if not dashboard_dir.exists():
        pytest.skip("dashboard/ directory tidak ditemukan")
    for py_file in dashboard_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert forbidden not in stripped, (
                f"CRITICAL: Import terlarang '{forbidden}' ditemukan di "
                f"{py_file.relative_to(ROOT)}:{i} — dashboard harus ringan!"
            )


@pytest.mark.parametrize("forbidden", CV_FORBIDDEN_CROSS_IMPORTS)
def test_cv_engine_no_dashboard_imports(forbidden):
    """CV engine must not import from dashboard package (services are independent)."""
    cv_dir = ROOT / "cv-engine"
    if not cv_dir.exists():
        pytest.skip("cv-engine/ directory tidak ditemukan")
    # Match only actual import lines, not log strings or comments
    import_re = re.compile(r'^\s*(import|from)\s+')
    for py_file in cv_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if not import_re.match(stripped):
                continue
            assert forbidden not in stripped, (
                f"Import silang terlarang '{forbidden}' di "
                f"{py_file.relative_to(ROOT)}:{i}"
            )


# ── Frontend hardcoded ports ───────────────────────────────────────────────────

@pytest.mark.parametrize("hardcode", FRONTEND_FORBIDDEN_HARDCODE)
def test_frontend_no_hardcoded_ports(hardcode):
    """Frontend TypeScript must use relative paths (/api, /cv) via Vite proxy."""
    src_dir = ROOT / "frontend" / "src"
    if not src_dir.exists():
        pytest.skip("frontend/src tidak ditemukan")
    ts_files = list(src_dir.rglob("*.ts")) + list(src_dir.rglob("*.tsx"))
    for ts_file in ts_files:
        content = ts_file.read_text(encoding="utf-8", errors="ignore")
        assert hardcode not in content, (
            f"WARNING: Hardcoded port '{hardcode}' di {ts_file.relative_to(ROOT)} "
            "— gunakan path relatif (/api, /cv) via Vite proxy"
        )


# ── Vite proxy config ──────────────────────────────────────────────────────────

def test_vite_proxy_config():
    vite_config = ROOT / "frontend" / "vite.config.ts"
    if not vite_config.exists():
        pytest.skip("vite.config.ts tidak ditemukan")
    content = vite_config.read_text(encoding="utf-8", errors="ignore")
    assert "'/api'" in content or '"/api"' in content, "Proxy /api tidak dikonfigurasi"
    assert "'/cv'" in content or '"/cv"' in content, "Proxy /cv tidak dikonfigurasi"
    assert "8000" in content, "Port dashboard 8000 tidak ditemukan di proxy config"
    assert "8001" in content, "Port cv-engine 8001 tidak ditemukan di proxy config"
    assert "ws: true" in content or "ws:true" in content, (
        "WebSocket proxy (ws:true) tidak dikonfigurasi di vite.config.ts"
    )


# ── Dependency hygiene ─────────────────────────────────────────────────────────

def test_dashboard_requirements_is_lightweight():
    req_file = ROOT / "dashboard" / "requirements.txt"
    if not req_file.exists():
        pytest.skip("dashboard/requirements.txt tidak ditemukan")
    content = req_file.read_text().lower()
    heavy_packages = ["opencv", "ultralytics", "torch", "av=="]
    for pkg in heavy_packages:
        assert pkg not in content, (
            f"CRITICAL: Package berat '{pkg}' ada di dashboard/requirements.txt — "
            "dashboard harus ringan!"
        )
    required_packages = ["fastapi", "uvicorn", "sqlalchemy", "aiosqlite", "httpx"]
    for required in required_packages:
        assert required in content, (
            f"Package wajib '{required}' tidak ada di dashboard/requirements.txt"
        )


def test_cv_requirements_has_cv_packages():
    req_file = ROOT / "cv-engine" / "requirements.txt"
    if not req_file.exists():
        pytest.skip("cv-engine/requirements.txt tidak ditemukan")
    content = req_file.read_text().lower()
    required_packages = ["ultralytics", "opencv", "av==", "fastapi", "sqlalchemy"]
    for required in required_packages:
        assert required in content, (
            f"Package '{required}' tidak ada di cv-engine/requirements.txt"
        )


# ── Shared database config ─────────────────────────────────────────────────────

def test_both_services_use_same_database():
    dash_config = ROOT / "dashboard" / "config.py"
    cv_config = ROOT / "cv-engine" / "config.py"
    if not dash_config.exists() or not cv_config.exists():
        pytest.skip("config.py tidak ditemukan")
    dash_content = dash_config.read_text(encoding="utf-8", errors="ignore")
    cv_content = cv_config.read_text(encoding="utf-8", errors="ignore")
    assert "shared" in dash_content.lower(), (
        "Dashboard tidak menggunakan folder shared/ untuk DB"
    )
    assert "shared" in cv_content.lower(), (
        "CV engine tidak menggunakan folder shared/ untuk DB"
    )


# ── Secret detection ───────────────────────────────────────────────────────────

def test_no_hardcoded_secrets():
    search_dirs = [ROOT / "dashboard", ROOT / "cv-engine"]
    findings = []
    # Match: password = "somevalue" / secret = 'value' (not in comments)
    pattern = re.compile(
        r'^[^#]*(?:password|secret|api_key|private_key)\s*=\s*["\'][^"\']{4,}["\']',
        re.IGNORECASE,
    )
    for d in search_dirs:
        if not d.exists():
            continue
        for py_file in d.rglob("*.py"):
            if ".env" in str(py_file) or "test" in str(py_file).lower():
                continue
            for i, line in enumerate(
                py_file.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
            ):
                if pattern.search(line):
                    findings.append(
                        f"{py_file.relative_to(ROOT)}:{i}: {line.strip()}"
                    )
    assert not findings, (
        "Potensi secret hardcoded ditemukan:\n" + "\n".join(findings)
    )


# ── Shell scripts ──────────────────────────────────────────────────────────────

def test_start_scripts_are_executable_or_exist():
    scripts = ["start-dashboard.sh", "start-cv.sh", "stop-cv.sh", "start-all.sh"]
    for script in scripts:
        path = ROOT / script
        assert path.exists(), f"Script tidak ditemukan: {script}"
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert "#!/bin/bash" in content or "#!/usr/bin/env bash" in content, (
            f"{script} tidak memiliki shebang line"
        )


# ── CV proxy endpoint ──────────────────────────────────────────────────────────

def test_cv_proxy_endpoint_exists_in_dashboard():
    cv_proxy = ROOT / "dashboard" / "routers" / "cv_proxy.py"
    if not cv_proxy.exists():
        pytest.skip("cv_proxy.py tidak ditemukan")
    content = cv_proxy.read_text(encoding="utf-8", errors="ignore")
    assert "/cv/status" in content or "cv_status" in content, (
        "Endpoint /api/cv/status tidak ditemukan di cv_proxy.py"
    )
    assert "except" in content, (
        "cv_proxy.py harus handle Exception saat CV engine tidak berjalan"
    )


# ── YOLO model config ──────────────────────────────────────────────────────────

def test_cv_engine_model_config_uses_nano_only():
    cv_config = ROOT / "cv-engine" / "config.py"
    if not cv_config.exists():
        pytest.skip("cv-engine/config.py tidak ditemukan")
    content = cv_config.read_text(encoding="utf-8", errors="ignore")
    assert "yolov8n" in content.lower(), (
        "Model default harus yolov8n (nano) — hanya model paling ringan"
    )
    for heavy_model in ["yolov8m", "yolov8l", "yolov8x"]:
        # heavy models should not be the DEFAULT — warn but don't fail
        # (they may appear in comments or option lists)
        default_line = next(
            (ln for ln in content.splitlines()
             if "yolo_model_name" in ln and heavy_model in ln and "=" in ln),
            None,
        )
        assert default_line is None, (
            f"CRITICAL: Model berat '{heavy_model}' set sebagai default di config.py: "
            f"{default_line}"
        )


# ── WAL mode configured ────────────────────────────────────────────────────────

def test_wal_mode_configured_in_both_services():
    """Both services must configure SQLite WAL for concurrent access."""
    for service_dir in ["dashboard", "cv-engine"]:
        py_files = list((ROOT / service_dir).rglob("*.py"))
        wal_found = any(
            "WAL" in f.read_text(encoding="utf-8", errors="ignore")
            for f in py_files
        )
        assert wal_found, (
            f"PRAGMA journal_mode=WAL tidak ditemukan di {service_dir}/ "
            "— wajib untuk shared SQLite"
        )
