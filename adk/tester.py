from typing import AsyncGenerator, override, Optional, TypedDict, Callable
from pathlib import Path

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from google.genai import types

from .app import AdkApp, RunSession

class ArtifactData(TypedDict):
    name: str
    path: Path | str
    type: str | None

async def create_test_session(app: AdkApp, artifacts: Optional[list[ArtifactData]] = None) -> RunSession:
    artifacts = artifacts or []
    app.clear_artifacts()
    session = await app.create_session(user_id="0", session_id="0")
    for artifact_data in artifacts:
        with open(artifact_data["path"], 'rb') as f:
            await session.save_artifact(artifact_data["name"], f.read(), artifact_data["type"])
    
    return session


class MockAgent(BaseAgent):
    """A minimal agent that always returns `mock_response` and stores it under `output_key`."""

    name: str = "mock_agent"
    mock_response: str | Callable[[InvocationContext], str] = "Mock Response"
    output_key: Optional[str] = None

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        response = f"{self.name} says: {self.mock_response(ctx) if callable(self.mock_response) else self.mock_response}"

        if self.output_key:
            await ctx.session_service.append_event(
                ctx.session, Event(author=self.name, actions=EventActions(state_delta={self.output_key: response}))
            )
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=response)]),
        )
