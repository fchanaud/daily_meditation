from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class ScriptGeneratorAgent:
    """
    Agent for generating meditation scripts based on a given mood.
    Uses OpenAI to create a unique, natural-sounding 10-minute meditation script.
    """
    
    def __init__(self, model_name="gpt-3.5-turbo"):
        self.llm = ChatOpenAI(model_name=model_name)
        self.prompt_template = ChatPromptTemplate.from_template(
            """You are a professional meditation instructor crafting a 10-minute guided meditation script.
            Create a meditation script for someone feeling {mood}.
            
            The meditation should:
            - Be approximately 10 minutes long when read aloud at a slow, calming pace
            - Have a clear beginning, middle, and end structure
            - Include appropriate breathing instructions
            - Use natural, soothing language
            - Be specific to the mood "{mood}"
            - Include pauses (indicated by [pause] notations)
            - Not include any timestamps or time indicators
            
            Format the meditation script as plain text without additional explanations or summaries.
            """
        )
    
    async def generate(self, mood: str) -> str:
        """
        Generate a meditation script based on the provided mood.
        
        Args:
            mood: The mood to base the meditation script on
            
        Returns:
            A string containing the generated meditation script
        """
        prompt = self.prompt_template.format(mood=mood)
        response = await self.llm.ainvoke(prompt)
        
        # Extract just the script content from the response
        script = response.content.strip()
        
        return script 