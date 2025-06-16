from google.adk.agents import BaseAgent, SequentialAgent


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