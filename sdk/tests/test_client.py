import json
from unittest.mock import MagicMock, patch

import pytest

from agentops_hub import AgentOps


def test_ingest_trace_payload():
    client = AgentOps(api_key="aoh_test", base_url="http://example/api/v1")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"execution_id": "abc", "status": "created"}

    with patch.object(client._client, "post", return_value=mock_response) as post:
        result = client.ingest_trace(
            agent="ResearchAgent",
            model="gpt-4o",
            input="hello",
            output="world",
            framework="langgraph",
        )
        assert result["execution_id"] == "abc"
        post.assert_called_once()
        body = post.call_args.kwargs["json"]
        assert body["agent"]["name"] == "ResearchAgent"
        assert body["input"] == "hello"


def test_trace_context_manager():
    client = AgentOps(api_key="aoh_test", base_url="http://example/api/v1")
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"execution_id": "xyz"}

    with patch.object(client._client, "post", return_value=mock_response):
        with client.trace(agent="Bot", model="gpt-4o") as span:
            span.set_input("in")
            span.set_output("out")
        assert span.result["execution_id"] == "xyz"
