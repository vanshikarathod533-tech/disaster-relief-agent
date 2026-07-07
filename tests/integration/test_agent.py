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
Integration tests for the disaster-relief agent workflow.

LLM calls are mocked so these tests run without consuming any API quota.
To run against the live API, set the env var LIVE_INTEGRATION_TEST=1.
"""

import os
from unittest.mock import patch

import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.models.google_llm import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


# ---------------------------------------------------------------------------
# Helpers
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
# Tests
# ---------------------------------------------------------------------------

def test_agent_stream() -> None:
    """
    Integration test for the agent workflow.

    Patches the LLM so no real API calls are made. The test verifies that
    the workflow executes end-to-end and returns at least one event with
    text content.
    """
    with patch(
        "google.adk.models.google_llm.Gemini.generate_content_async",
        new=_mock_generate,
    ):
        session_service = InMemorySessionService()
        session = session_service.create_session_sync(
            user_id="test_user", app_name="test"
        )
        runner = Runner(
            agent=root_agent,
            session_service=session_service,
            app_name="test",
        )

        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text="There is a flood, I have a pet dog.")],
        )

        events = list(
            runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )
        )

        assert len(events) > 0, "Expected at least one event from the workflow"

        has_text_content = any(
            event.content
            and event.content.parts
            and any(part.text for part in event.content.parts)
            for event in events
        )
        assert has_text_content, "Expected at least one event with text content"


@pytest.mark.skipif(
    not os.environ.get("LIVE_INTEGRATION_TEST"),
    reason=(
        "Skipped by default to avoid quota consumption. "
        "Set LIVE_INTEGRATION_TEST=1 to run against the real API."
    ),
)
def test_agent_stream_live() -> None:
    """
    Live integration test — hits the real Gemini API.
    Only runs when LIVE_INTEGRATION_TEST=1 is set.
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="There is a flood, I have a pet dog.")],
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0, "Expected at least one message"

    has_text_content = any(
        event.content
        and event.content.parts
        and any(part.text for part in event.content.parts)
        for event in events
    )
    assert has_text_content, "Expected at least one message with text content"
