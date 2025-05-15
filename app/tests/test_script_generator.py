import os
import pytest
from app.agents.script_generator import ScriptGeneratorAgent

@pytest.mark.asyncio
async def test_script_generator():
    """Test that the script generator produces a valid meditation script."""
    # Skip this test if no OpenAI API key is available (for CI environments)
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("Skipping test: No OpenAI API key available")
    
    agent = ScriptGeneratorAgent()
    script = await agent.generate("calm")
    
    # Check that we got a non-empty string
    assert isinstance(script, str)
    assert len(script) > 100
    
    # Check for some expected content in a meditation script
    assert "breath" in script.lower()
    assert "[pause]" in script 