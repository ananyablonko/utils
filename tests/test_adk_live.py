import __init__
import asyncio

from google.adk.agents import LlmAgent

from adk.app import AdkApp
from adk.tester import create_test_session
from adk.schema import LiveMessage

agent = LlmAgent(
    name="talker",
    model="gemini-2.0-flash-exp",
)

async def test_adk_live() -> None:

    with await create_test_session(AdkApp(
        name="talker",
        agent=agent,
    )) as session:
        session.live_send(LiveMessage(content="Hi, How are you?"))
        async for msg in session.live_recv():
            print(msg)
            if msg.done:
                break
    

async def main() -> None:
    await test_adk_live()


if __name__ == '__main__':
    asyncio.run(main())