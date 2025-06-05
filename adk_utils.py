from typing import Optional, cast, AsyncGenerator, Callable, Any, TypedDict
from google.adk.agents import BaseAgent
from google.adk.runners import Runner
from google.adk.sessions import Session
from google.adk.sessions import InMemorySessionService
from google.genai import types

class UserSession(TypedDict):
    user_id: str
    session_id: str


async def run_agent(
    agent: BaseAgent, prompt: str, *,
    initial_state: Optional[dict] = None,
    check: Callable = lambda e: e.is_final_response(),
    func: Callable = lambda e: e.content.parts[0].text
) -> AsyncGenerator[Any, None]:
    s = UserSession(user_id="admin", session_id="1")
    runner = Runner(agent=agent, app_name="demo", session_service=InMemorySessionService())
    await runner.session_service.create_session(app_name=runner.app_name, state=initial_state or {}, **s)
    async for ev in runner.run_async(**s, new_message=types.Content(role="user", parts=[types.Part(text=prompt)])):
        if check(ev):
            yield func(ev)

    session = cast(Session, await runner.session_service.get_session(app_name=runner.app_name, **s))
    yield session
