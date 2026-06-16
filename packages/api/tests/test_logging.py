"""Cover the request-id middleware behavior."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient


def test_request_id_echoed_when_supplied(client: TestClient):
    response = client.get("/healthz", headers={"X-Request-ID": "abc-123"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "abc-123"


def test_request_id_generated_when_missing(client: TestClient):
    response = client.get("/healthz")
    assert response.status_code == 200
    minted = response.headers["x-request-id"]
    assert re.fullmatch(r"[0-9a-f]{32}", minted), minted
