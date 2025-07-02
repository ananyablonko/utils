import re
from typing import Optional, Callable

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


def should_run_agent(
    callback_context: CallbackContext, *, prerequisites: Optional[list[str | Callable[[CallbackContext], str]]] = None, cached: Optional[list[str | Callable[[CallbackContext], str]]] = None
) -> Optional[types.Content]:
    f"""
    USAGE
    -----
    before_agent_callback=functools.partial({should_run_agent.__name__}, key=expected_key_to_be_in_session)
    """
    extracted_prereqs: list[str] = [func_or_str(callback_context) if isinstance(func_or_str, Callable) else func_or_str for func_or_str in prerequisites] if prerequisites else []
    extracted_cached: list[str] = [func_or_str(callback_context) if isinstance(func_or_str, Callable) else func_or_str for func_or_str in cached] if cached else []

    if cached and all(key in callback_context.state for key in extracted_cached):
        return types.Content(role="model", parts=[types.Part(text=f"Agent {callback_context.agent_name} skipped: {cached} already in state!")])
    
    for key in extracted_prereqs:
        if key not in callback_context.state:
            return types.Content(role="model", parts=[types.Part(text=f"Agent {callback_context.agent_name} skipped: {key} not in state!")])


def last_input_only(callback_context: CallbackContext, llm_request: LlmRequest) -> None:
    llm_request.contents[:] = [llm_request.contents[-1]]


def purge_request(callback_context: CallbackContext, llm_request: LlmRequest, *,
                  include_pattern: Optional[str] = None,
                  exclude_pattern: Optional[str] = None
                  ) -> Optional[LlmResponse]:
    
    llm_request.contents[:] = [c for c in llm_request.contents if
                               (include_pattern is None or re.search(include_pattern, str(c)))
                               and
                               (exclude_pattern is None or not re.search(exclude_pattern, str(c)))]