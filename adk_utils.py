import asyncio
from typing import Optional, cast, AsyncGenerator, Callable, Any, TypedDict
from pydantic import BaseModel, Field, PrivateAttr
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import Session, InMemorySessionService
from google.genai import types


def get_output_key(agent: BaseAgent) -> str:
    key = None
    if hasattr(agent, 'output_key'):
        key = agent.output_key  # type: ignore
    elif isinstance(agent, SequentialAgent):
        key = get_output_key(agent.sub_agents[-1])
    else:
        raise NotImplementedError(f"{get_output_key.__name__} is only valid for Agents with an output key")
    if key is None:
        raise ValueError("Agent does not have an output key")
    return key


class UserSession(TypedDict):
    user_id: str
    session_id: str


class AgentTester(BaseModel):
    agent: BaseAgent
    initial_state: Optional[dict] = Field(default_factory=dict)
    check: Callable = lambda e: e.is_final_response()
    extract: Callable = lambda e: e.content.parts[0].text if e.content else e.actions.state_delta
    _session: Optional[Session] = PrivateAttr(default=None)

    def model_post_init(self, context: Any) -> None:
        super().model_post_init(context)
        self._s = UserSession(user_id="0", session_id="0")
        self._r = Runner(agent=self.agent, app_name="0", session_service=InMemorySessionService())
        self._t = asyncio.create_task(self._r.session_service.create_session(app_name=self._r.app_name, state=self.initial_state, **self._s))
    
    def is_done(self):
        return self._session is not None

    async def run(self, prompt: str) -> AsyncGenerator:
        if not self._t.done():
            await self._t

        async for ev in self._r.run_async(**self._s, new_message=types.Content(role="user", parts=[types.Part(text=prompt)])):
            if self.check(ev):
                yield self.extract(ev)

        self._session = cast(Session, await self._r.session_service.get_session(app_name=self._r.app_name, **self._s))

    def get_last_output(self):
        return self.session.state.get(get_output_key(self.agent))

    @property
    def session(self) -> Session:
        if self._session is None:
            raise ValueError("Call is_done to ensure the session was properly returned after the agent ran")
        return self._session


class SingleValue[T](BaseModel):
    """
    Workaround for RootModel bugs (e.g. doesn't work with dict).
    Also has a nicer serialization.
    """
    value: T

    def __init__(self, value: Optional[T] = None, *args):
        if len(args) < 1:
            if value is None:
                raise ValueError(f"No arg given -> value cannot be None!, got {value=}")
        else:
            if len(args) > 1:
                raise ValueError(f"arg must be a single value, got {args}")
            if value is not None:
                raise ValueError(f"arg given - value must be None!, got {value=}")
            
            value = args[0]

        super().__init__(value=value)

    def model_dump(self, *args, **kwargs) -> T:
        return self.value
    

def should_run_agent(keys: list[str], callback_context: CallbackContext) -> Optional[types.Content]:
    f"""
    USAGE
    -----
    before_agent_callback=functools.partial({should_run_agent.__name__}, key=expected_key_to_be_in_session)
    """
    for key in keys:
        if key not in callback_context.state:
            return types.Content(role="model", parts=[types.Part(text=f"Agent {callback_context.agent_name} skipped: {key} not in state!")])