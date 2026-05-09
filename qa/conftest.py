"""Synchronous fixtures and session-level configuration."""

import pathlib
import pytest
import httpx

DASHBOARD_URL = "http://localhost:8000"
CV_URL = "http://localhost:8001"

PROJECT_ROOT: pathlib.Path | None = None


def pytest_configure(config):
    global PROJECT_ROOT
    qa_dir = pathlib.Path(__file__).parent
    PROJECT_ROOT = qa_dir.parent


def pytest_collection_modifyitems(config, items):
    """Auto-apply asyncio marker to all async test functions."""
    import asyncio
    for item in items:
        if asyncio.iscoroutinefunction(getattr(item, "function", None)):
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture(scope="session")
def project_root() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent


@pytest.fixture(scope="session")
def dashboard_url() -> str:
    return DASHBOARD_URL


@pytest.fixture(scope="session")
def cv_url() -> str:
    return CV_URL


@pytest.fixture
def sync_client():
    with httpx.Client(timeout=5.0) as client:
        yield client


@pytest.fixture
def dashboard_available(sync_client) -> bool:
    try:
        r = sync_client.get(f"{DASHBOARD_URL}/health")
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture
def cv_available(sync_client) -> bool:
    try:
        r = sync_client.get(f"{CV_URL}/health")
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture
def sample_cctv() -> dict:
    return {
        "name": "TEST_QA_CCTV",
        "location": "QA Test Lokasi",
        "stream_url": "https://example.com/qa_test_stream.m3u8",
    }
