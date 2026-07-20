import pytest


@pytest.mark.asyncio
async def test_create_and_fetch_backtest(client):
    create_resp = await client.post(
        "/api/v1/backtests", json={"strategy_name": "mean_reversion_v1"}
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["status"] == "pending"

    get_resp = await client.get(f"/api/v1/backtests/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["strategy_name"] == "mean_reversion_v1"


@pytest.mark.asyncio
async def test_get_missing_backtest_404(client):
    resp = await client.get(
        "/api/v1/backtests/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404
