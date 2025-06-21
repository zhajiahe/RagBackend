import asyncio
import os

import pytest

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest.fixture(scope="session")
def event_loop():
    """Create a single asyncio event loop for the entire test session,
    and only close it once at the very end.
    This overrides pytest-asyncio's default event_loop fixture.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
