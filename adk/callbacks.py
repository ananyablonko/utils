from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.genai import types


def should_run_agent(keys: list[str], callback_context: CallbackContext) -> Optional[types.Content]:
    f"""
    USAGE
    -----
    before_agent_callback=functools.partial({should_run_agent.__name__}, key=expected_key_to_be_in_session)
    """
    for key in keys:
        if key not in callback_context.state:
            return types.Content(role="model", parts=[types.Part(text=f"Agent {callback_context.agent_name} skipped: {key} not in state!")])
