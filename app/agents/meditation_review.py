from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class MeditationReviewAgent:
    """
    Agent for reviewing and improving meditation scripts.
    Reviews for repetition, structure, tone consistency, and clarity.
    """
    
    def __init__(self, model_name="gpt-3.5-turbo"):
        self.llm = ChatOpenAI(model_name=model_name)
        self.prompt_template = ChatPromptTemplate.from_template(
            """As a professional meditation script editor, review and improve the following 
            meditation script. Your goal is to make it natural, effective, and suited for audio narration.
            
            The original script was created for someone feeling {mood}.
            
            Original script:
            {script}
            
            Please review for:
            - Natural flow and pacing, with appropriate [pause] markers
            - Consistent tone that matches the stated mood
            - Clear structure with beginning, middle, and ending
            - Appropriate breathing instructions
            - No repetitive phrases or awkward wording
            - No timestamps or time markers
            
            Return only the improved script, without explanations or comments.
            Only make changes if they genuinely improve the script.
            """
        )
    
    async def review(self, script: str, mood: str) -> str:
        """
        Review and improve a meditation script.
        
        Args:
            script: The original meditation script
            mood: The mood the meditation script was based on
            
        Returns:
            A string containing the revised meditation script
        """
        prompt = self.prompt_template.format(script=script, mood=mood)
        response = await self.llm.ainvoke(prompt)
        
        # Extract just the improved script content from the response
        revised_script = response.content.strip()
        
        return revised_script 