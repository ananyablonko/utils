import re
from typing import Optional, Callable

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.genai import types

def create_should_run_agent_callback(
        prerequisites: Optional[list[str | Callable[[CallbackContext], str]]] = None,
        cached: Optional[list[str | Callable[[CallbackContext], str]]] = None,
) -> Callable[[CallbackContext], Optional[types.Content]]:
    def should_run_agent(callback_context: CallbackContext) -> Optional[types.Content]:
        """
        RETURNS
        -------
        Content with a message if the agent should NOT run, None otherwise.
        """
        extracted_prereqs: list[str] = [x(callback_context) if isinstance(x, Callable) else x for x in prerequisites] if prerequisites else []
        extracted_cached: list[str] = [x(callback_context) if isinstance(x, Callable) else x for x in cached] if cached else []

        if cached and all(key in callback_context.state for key in extracted_cached):
            return types.Content(role="model", parts=[types.Part(text=f"Agent {callback_context.agent_name} skipped: {cached} already in state!")])
        
        for key in extracted_prereqs:
            if key not in callback_context.state:
                return types.Content(role="model", parts=[types.Part(text=f"Agent {callback_context.agent_name} skipped: {key} not in state!")])
        
    return should_run_agent


def last_input_only(callback_context: CallbackContext, llm_request: LlmRequest) -> None:
    llm_request.contents[:] = [llm_request.contents[-1]]


def create_purge_request_callback(*,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None
) -> Callable[[CallbackContext, LlmRequest], None]:
    def purge_request(callback_context: CallbackContext, llm_request: LlmRequest) -> None:
        llm_request.contents[:] = [c for c in llm_request.contents if True
                                and (include_pattern is None or re.search(include_pattern, str(c)))
                                and (exclude_pattern is None or not re.search(exclude_pattern, str(c)))]
    
    return purge_request