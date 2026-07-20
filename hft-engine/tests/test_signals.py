import pytest


@pytest.mark.asyncio
async def test_record_and_list_signal(client):
    payload = {
        "signal_key": "obi",
        "channel_code": "IN",
        "order_throughput": 4200,
        "latency_ms": 1.35,
        "load_percentage": 62,
    }
    create_resp = await client.post("/api/v1/signals", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["signal_key"] == "obi"

    list_resp = await client.get("/api/v1/signals", params={"channel_code": "IN"})
    assert list_resp.status_code == 200
    rows = list_resp.json()
    assert len(rows) == 1
    assert rows[0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_list_signals_empty(client):
    resp = await client.get("/api/v1/signals")
    assert resp.status_code == 200
    assert resp.json() == []
