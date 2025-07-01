from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.genai import types


def should_run_agent(
    callback_context: CallbackContext, *, prerequisites: Optional[list[str]] = None, cached: Optional[list[str]] = None
) -> Optional[types.Content]:
    f"""
    USAGE
    -----
    before_agent_callback=functools.partial({should_run_agent.__name__}, key=expected_key_to_be_in_session)
    """
    prerequisites = prerequisites or []
    cached = cached or []

    if cached and all(key in callback_context.state for key in cached):
        return types.Content(role="model", parts=[types.Part(text=f"Agent {callback_context.agent_name} skipped: {cached} already in state!")])
    
    for key in prerequisites:
        if key not in callback_context.state:
            return types.Content(role="model", parts=[types.Part(text=f"Agent {callback_context.agent_name} skipped: {key} not in state!")])
