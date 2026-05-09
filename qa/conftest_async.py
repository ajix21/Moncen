"""Async-only fixtures — imported explicitly in async test files."""

import pytest
import httpx

DASHBOARD_URL = "http://localhost:8000"
CV_URL = "http://localhost:8001"


@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client
