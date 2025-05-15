#!/usr/bin/env python
"""
Test script to verify the YouTube video validation functionality.
"""
import asyncio
import logging
from app.agents.openai_meditation_agent import OpenAIMeditationAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_validation")

async def test_validate_youtube_url():
    """Test the YouTube URL validation function."""
    agent = OpenAIMeditationAgent()
    
    # Test URLs
    valid_url = "https://www.youtube.com/watch?v=ZToicYcHIOU"  # Should be valid
    invalid_url = "https://www.youtube.com/watch?v=K9q9YzS0uGA"  # Known invalid video
    
    # Test valid URL
    logger.info(f"Testing valid URL: {valid_url}")
    valid_result = await agent._validate_youtube_url(valid_url)
    logger.info(f"Valid URL result: {valid_result}")
    
    # Test invalid URL
    logger.info(f"Testing invalid URL: {invalid_url}")
    invalid_result = await agent._validate_youtube_url(invalid_url)
    logger.info(f"Invalid URL result: {invalid_result}")
    
    # Test full meditation finding with validation
    logger.info("Testing find_meditation with validation")
    url, info = await agent.find_meditation("calm", "english")
    logger.info(f"Found meditation: {url}")
    
    return {
        "valid_url_test": valid_result,
        "invalid_url_test": not invalid_result,  # Should be False
        "find_meditation_test": url is not None
    }

if __name__ == "__main__":
    results = asyncio.run(test_validate_youtube_url())
    
    # Print summary
    print("\nTest Results:")
    print("-------------")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall status
    if all(results.values()):
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!") 