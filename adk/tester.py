from typing import AsyncGenerator, override, Optional, TypedDict
from pathlib import Path

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

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

    mock_response: str
    output_key: str
    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, *,
                 name: str = "mock_agent",
                 mock_response: str = "Mock Response",
                 output_key: str = "mock",
                 **kwargs,
                 ):
        super().__init__(
            name=name,
            mock_response=mock_response,  # type: ignore
            output_key=output_key,  # type: ignore
            **kwargs
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:

        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=self.mock_response)]),
        )