# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Integration tests for AgentEngineApp (agent_runtime_app).

LLM calls and Vertex AI initialisation are mocked so these tests run
without billing or API quota. To run against the real backend set
LIVE_INTEGRATION_TEST=1.
"""

import logging
import os
from unittest.mock import patch

import pytest
from google.adk.events.event import Event
from google.adk.models.google_llm import LlmResponse
from google.genai import types

from app.agent_runtime_app import AgentEngineApp


# ---------------------------------------------------------------------------
# LLM mock (same helper as test_agent.py)
# ---------------------------------------------------------------------------

_CANNED_TEXT = (
    "Emergency response: Evacuate immediately to City Hall shelter (pet-friendly). "
    "General Hospital is 1 mile north. Stay calm and follow local authority guidance."
)


async def _mock_generate(self, llm_request, stream=False):
    """Async generator that yields one real LlmResponse with text content."""
    yield LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text=_CANNED_TEXT)],
        ),
        turn_complete=True,
        partial=False,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_app(monkeypatch: pytest.MonkeyPatch) -> AgentEngineApp:
    """Fixture to create and set up AgentEngineApp instance."""
    monkeypatch.setenv("INTEGRATION_TEST", "TRUE")

    from app.agent_runtime_app import agent_runtime

    # Prevent vertexai.init() from hitting Google Cloud (needs billing)
    with patch("vertexai.init"):
        agent_runtime.set_up()

    return agent_runtime


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_stream_query(agent_app: AgentEngineApp) -> None:
    """
    Integration test for the agent stream query functionality.

    Mocks LLM calls so no API quota or billing is consumed.
    Tests that the agent returns valid streaming responses.
    """
    message = "There is a flood, I have a pet dog."
    events = []

    with patch(
        "google.adk.models.google_llm.Gemini.generate_content_async",
        new=_mock_generate,
    ):
        async for event in agent_app.async_stream_query(message=message, user_id="test"):
            events.append(event)

    assert len(events) > 0, "Expected at least one chunk in response"

    has_text_content = False
    for event in events:
        validated_event = Event.model_validate(event)
        content = validated_event.content
        if (
            content is not None
            and content.parts
            and any(part.text for part in content.parts)
        ):
            has_text_content = True
            break

    assert has_text_content, "Expected at least one event with text content"


def test_agent_feedback(agent_app: AgentEngineApp) -> None:
    """
    Integration test for the agent feedback functionality.
    Tests that feedback can be registered successfully.
    """
    feedback_data = {
        "score": 5,
        "text": "Great response!",
        "user_id": "test-user-456",
        "session_id": "test-session-456",
    }

    # Should not raise any exceptions
    agent_app.register_feedback(feedback_data)

    # Test invalid feedback
    with pytest.raises(ValueError):
        invalid_feedback = {
            "score": "invalid",  # Score must be numeric
            "text": "Bad feedback",
            "user_id": "test-user-789",
            "session_id": "test-session-789",
        }
        agent_app.register_feedback(invalid_feedback)

    logging.info("All assertions passed for agent feedback test")


@pytest.mark.skipif(
    not os.environ.get("LIVE_INTEGRATION_TEST"),
    reason=(
        "Skipped by default — requires billing + API quota. "
        "Set LIVE_INTEGRATION_TEST=1 to enable."
    ),
)
@pytest.mark.asyncio
async def test_agent_stream_query_live(agent_app: AgentEngineApp) -> None:
    """Live version — hits the real Gemini API and Vertex AI."""
    message = "There is a flood, I have a pet dog."
    events = []
    async for event in agent_app.async_stream_query(message=message, user_id="test"):
        events.append(event)

    assert len(events) > 0, "Expected at least one chunk in response"

    has_text_content = any(
        Event.model_validate(e).content
        and Event.model_validate(e).content.parts
        and any(p.text for p in Event.model_validate(e).content.parts)
        for e in events
    )
    assert has_text_content, "Expected at least one event with text content"
