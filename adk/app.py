from typing import Any, AsyncGenerator, Callable, Optional, TypedDict, Unpack, ClassVar
import typing
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from aiohttp.client_exceptions import ClientConnectionError

from google.adk.agents import BaseAgent
from google.adk.runners import Runner
from google.adk.events import Event, EventActions
from google.adk.sessions import Session, BaseSessionService, InMemorySessionService, DatabaseSessionService
from google.adk.memory import BaseMemoryService, InMemoryMemoryService, VertexAiRagMemoryService
from google.adk.artifacts import BaseArtifactService, InMemoryArtifactService
from google.genai import types

from utils.common.adk.artifacts import FileSystemArtifactService
from utils.common.adk.schema import Message
from utils.common.text.printing import prettify


class UserSession(TypedDict):
    user_id: str
    session_id: str


class RunSession(BaseModel):
    app: "AdkApp"
    us: UserSession
    session: Session

    def model_post_init(self, context: Any) -> None:
        super().model_post_init(context)
        self._session_service: BaseSessionService = typing.cast(BaseSessionService, self.app._runner.session_service)
        self._artifact_service: BaseArtifactService = typing.cast(BaseArtifactService, self.app._runner.artifact_service)
        self._memory_service: BaseMemoryService = typing.cast(BaseMemoryService, self.app._runner.memory_service)

    async def refresh(self) -> None:
        session = await self._session_service.get_session(app_name=self.app.name, **self.us)
        if session is None:
            raise ValueError("Session Invalidated")
        self.session = session

    async def run(self, prompt: str) -> AsyncGenerator:
        err = None
        for i in range(1, AdkApp.N_RETRIES + 1):
            try:
                async for ev in self.app._runner.run_async(**self.us, new_message=types.Content(role="user", parts=[types.Part(text=prompt)])):
                    if self.app.check(ev):
                        yield self.app.extract(ev)
            except ClientConnectionError as e:
                err = e
                yield self.app.extract(Event(author="system", error_code=e.__class__.__name__, error_message=repr(err) + f"\nRetrying... ({i}/{AdkApp.N_RETRIES})"))
            else:
                break
        else:
            raise OSError from err


        await self.refresh()
        
    async def update_state(self, new_data: dict[str, Any], tell_agent: bool = True, message: str = "") -> None:
        if not new_data:
            return
        
        event = Event(
            author="user",
            actions=EventActions(
                state_delta=new_data
            )
        )
        await self._session_service.append_event(self.session, event=event)
        if tell_agent:
            await self.append_message(f"State updated:\n{message + '\n' if message else ""}{prettify(new_data)}\n")
        await self.refresh()

    @property
    def state(self) -> dict[str, Any]:
        return self.session.state
    
    @property
    def history(self) -> list[Message]:
        return [
            Message(
                id=e.id,
                sender="user" if e.author == "user" else "agent",
                content=e.content.parts[0].text,
                timestamp=datetime.fromtimestamp(e.timestamp, timezone.utc).isoformat()
            )
            for e in self.session.events
            if e.content and e.content.parts and e.content.parts[0].text
            and e.author != "system"
        ]

    async def save_artifact(self, name: str, artifact: bytes, mime_type: Optional[str] = None) -> None:
        await self._artifact_service.save_artifact(
            app_name=self.app.name,
            filename=name,
            artifact=types.Part.from_bytes(data=artifact, mime_type=mime_type or "application/octet-stream"),
            **self.us,
        )
        await self.refresh()

    async def load_artifact(self, name: str, version: Optional[int] = None) -> Optional[bytes]:
        part = await self._artifact_service.load_artifact(
            app_name=self.app.name,
            filename=name,
            version=version,
            **self.us,
        )

        return part.inline_data.data if part and part.inline_data else None
        
    async def save_memory(self) -> None:
        await self._memory_service.add_session_to_memory(self.session)
        await self.refresh()
        
    async def load_memory(self, query: str) -> list[str]:
        memory_contents = await self._memory_service.search_memory(
            app_name=self.app.name,
            user_id=self.us["user_id"],
            query=query
        )

        return [m.content.parts[0].text for m in memory_contents.memories if m.content and m.content.parts and m.content.parts[0].text]

    async def append_message(self, message: str, author: str = "system") -> None:
        await self.app._runner.session_service.append_event(
            self.session,
            Event(
                author=author,
                content=types.Content(
                    role="user" if author == "user" else "model",
                    parts=[types.Part(text=message)]
                )
            )
        )


def check_event(ev: Event) -> bool:
    return ev.partial or ev.is_final_response()

def extract_event(ev: Event) -> Any:
    if ev.content and ev.content.parts and ev.content.parts[0]:
        return ev.content.parts[0].text
    elif ev.error_message:
        return ev.error_message
    else:
        return ev.actions.state_delta

class AdkApp(BaseModel):
    name: str
    agent: BaseAgent
    initial_state: dict = Field(default_factory=dict)
    check: Callable[[Event], bool] = check_event
    extract: Callable[[Event], Any] = extract_event
    db_url: str = ""
    artifact_path: str = ""

    N_RETRIES: ClassVar = 10

    def model_post_init(self, context: Any) -> None:
        super().model_post_init(context)
        self._runner = Runner(
            agent=self.agent,
            app_name=self.name,
            session_service=DatabaseSessionService(self.db_url) if self.db_url else InMemorySessionService(),
            artifact_service=FileSystemArtifactService(self.artifact_path) if self.artifact_path else InMemoryArtifactService(),
        )
    
    async def get_session(self, **us: Unpack[UserSession]) -> RunSession:
        session = await self._runner.session_service.get_session(
            app_name=self.name, **us
        )

        if session is None:
            raise KeyError(f"Session {us["session_id"]} does not exist")
        
        return RunSession(app=self, us=us, session=session)

        
    async def create_session(self, state: Optional[dict[str, Any]] = None, **us: Unpack[UserSession]) -> RunSession:
        return RunSession(
            app=self, us=us,
            session=await self._runner.session_service.create_session(
                app_name=self.name, **us, state=self.initial_state | (state or {})
            )
        )
    
    async def delete_session(self, **us: Unpack[UserSession]) -> None:
        await self._runner.session_service.delete_session(
            app_name=self.name, **us
        )
    
    async def list_sessions(self, user_id: str) -> list[str]:
        response = await self._runner.session_service.list_sessions(
            app_name=self.name,
            user_id=user_id
        )
        return [s.id for s in response.sessions]
    
    def clear_artifacts(self) -> None:
        if isinstance(self._runner.artifact_service, (InMemoryArtifactService, FileSystemArtifactService)):
            self._runner.artifact_service.artifacts.clear()
        else:
            raise NotImplementedError()
