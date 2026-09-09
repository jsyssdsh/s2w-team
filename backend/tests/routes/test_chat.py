"""Tests for /api/chat, using LLM_MOCK's keyword-driven tool calling."""


class TestChat:
    async def test_plain_question_gets_greeting_with_no_tool_calls(self, client):
        resp = await client.post("/api/chat", json={"message": "안녕하세요"})
        assert resp.status_code == 200
        body = resp.json()
        assert "message" in body
        assert body["tool_calls"] == []

    async def test_create_trade_request_via_chat_creates_a_transaction(self, client):
        resp = await client.post(
            "/api/chat",
            json={"message": "토마토 1000kg 도매처B에게 거래 요청해줘", "user_id": "user-farmer-kim"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["tool_calls"]) == 1
        outcome = body["tool_calls"][0]
        assert outcome["name"] == "create_trade_request"
        assert outcome["error"] is None
        assert outcome["result"]["wholesaler_id"] == "wholesaler-b"
        assert outcome["result"]["quantity_kg"] == 1000

    async def test_unknown_crop_reports_error_without_crashing(self, client):
        resp = await client.post(
            "/api/chat",
            json={"message": "감귤 100kg 도매처A에게 거래 요청해줘", "user_id": "user-farmer-kim"},
        )
        assert resp.status_code == 200
        outcome = resp.json()["tool_calls"][0]
        assert outcome["error"] is not None

    async def test_chat_history_persists_across_calls(self, client):
        await client.post("/api/chat", json={"message": "안녕하세요", "session_id": "session-a"})
        resp = await client.get("/api/chat/history", params={"session_id": "session-a"})
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) == 2  # user + assistant
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "안녕하세요"
        assert messages[1]["role"] == "assistant"

    async def test_chat_history_is_isolated_per_session(self, client):
        """Two browser tabs (different session_id) must not see each other's history."""
        await client.post("/api/chat", json={"message": "세션 A 메시지", "session_id": "session-a"})
        await client.post("/api/chat", json={"message": "세션 B 메시지", "session_id": "session-b"})

        resp_a = await client.get("/api/chat/history", params={"session_id": "session-a"})
        resp_b = await client.get("/api/chat/history", params={"session_id": "session-b"})

        contents_a = {m["content"] for m in resp_a.json()}
        contents_b = {m["content"] for m in resp_b.json()}
        assert "세션 A 메시지" in contents_a
        assert "세션 A 메시지" not in contents_b
        assert "세션 B 메시지" in contents_b
        assert "세션 B 메시지" not in contents_a

    async def test_response_echoes_session_id(self, client):
        resp = await client.post("/api/chat", json={"message": "안녕하세요", "session_id": "session-c"})
        assert resp.json()["session_id"] == "session-c"

    async def test_list_trade_requests_via_chat(self, client):
        resp = await client.post(
            "/api/chat", json={"message": "거래 요청 목록 보여줘", "user_id": "user-farmer-kim"}
        )
        assert resp.status_code == 200
        outcome = resp.json()["tool_calls"][0]
        assert outcome["name"] == "list_trade_requests"
        assert outcome["error"] is None
