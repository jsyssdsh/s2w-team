"""Tests for the shared tool-execution helper."""

from app.llm.tools import execute_tool_call


class TestExecuteToolCall:
    async def test_success(self):
        async def create_trade_request(**kwargs):
            return {"request_id": "req-1", **kwargs}

        outcome = await execute_tool_call(
            "create_trade_request",
            {"crop_name": "토마토", "quantity_kg": 500},
            {"create_trade_request": create_trade_request},
        )
        assert outcome.error is None
        assert outcome.result == {"request_id": "req-1", "crop_name": "토마토", "quantity_kg": 500}

    async def test_missing_executor(self):
        outcome = await execute_tool_call("create_trade_request", {}, {})
        assert outcome.result is None
        assert "No executor registered" in outcome.error

    async def test_executor_raises(self):
        async def broken(**kwargs):
            raise ValueError("boom")

        outcome = await execute_tool_call("create_trade_request", {}, {"create_trade_request": broken})
        assert outcome.result is None
        assert outcome.error == "boom"
