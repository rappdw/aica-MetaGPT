"""Base classes for AICA implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self):
        self.last_token_count = {"input_tokens": 0, "output_tokens": 0}
    
    @abstractmethod
    async def aask(self, prompt: str) -> str:
        """Send a prompt to the LLM and get a response."""
        pass


class BedrockProvider(LLMProvider):
    """AWS Bedrock provider for Claude."""

    def __init__(self, model_id: str, region: str, max_tokens: int = 32768):
        super().__init__()
        import boto3
        import tiktoken
        self.model_id = model_id
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Claude uses this encoding

    async def aask(self, prompt: str) -> str:
        """Send a prompt to Claude via AWS Bedrock."""
        import json
        
        try:
            # Count input tokens
            input_tokens = len(self.tokenizer.encode(prompt))
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.7,
                "top_p": 0.95,
            }
            
            # Call Bedrock
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            completion = response_body['content'][0]['text']
            
            # Count output tokens
            output_tokens = len(self.tokenizer.encode(completion))
            
            # Store token counts
            self.last_token_count = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
            
            return completion
            
        except Exception as e:
            raise Exception(f"Error calling Bedrock: {str(e)}")


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__()
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def aask(self, prompt: str) -> str:
        """Send a prompt to OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            
            # Store token counts from OpenAI's response
            self.last_token_count = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error calling OpenAI: {str(e)}")


class Action(BaseModel):
    """Base class for actions that can be performed by roles."""
    name: str
    llm: Optional[LLMProvider] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Run the action with the given parameters."""
        pass
    
    def set_llm(self, llm: LLMProvider) -> None:
        """Set the LLM provider for this action."""
        self.llm = llm
    
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call LLM with token tracking."""
        if not self.llm:
            raise ValueError("LLM provider not set")
        
        try:
            response = await self.llm.aask(prompt)
            
            # Get token counts from the LLM provider
            token_counts = {
                "input_tokens": 0,
                "output_tokens": 0
            }
            if hasattr(self.llm, 'last_token_count'):
                token_counts = self.llm.last_token_count
            
            # Parse the response
            result = self._parse_json_response(response)
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                result = {
                    "response": result,
                    "input_tokens": token_counts.get("input_tokens", 0),
                    "output_tokens": token_counts.get("output_tokens", 0)
                }
            else:
                result["input_tokens"] = token_counts.get("input_tokens", 0)
                result["output_tokens"] = token_counts.get("output_tokens", 0)
            
            return result
        except Exception as e:
            return {
                "error": str(e),
                "input_tokens": 0,
                "output_tokens": 0
            }
    
    def _parse_json_response(self, response: str) -> Any:
        """Parse JSON response from LLM, with error handling."""
        import json
        
        # If response is not a string, return as is
        if not isinstance(response, str):
            return response
        
        # Try to find JSON block if response contains markdown
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # If it's not JSON, return the raw response
            return response.strip()


class Role(BaseModel):
    """Base class for team roles."""
    name: str
    profile: str
    actions: List[Action] = []
    llm: Optional[LLMProvider] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize actions with LLM provider
        if self.llm:
            self.set_llm(self.llm)

    def set_llm(self, llm: LLMProvider) -> None:
        """Set the LLM provider for this role and all its actions."""
        self.llm = llm
        for action in self.actions:
            action.set_llm(llm)

    async def run(self, action_name: str, **kwargs) -> Dict[str, Any]:
        """Run an action by name with the given parameters."""
        if not self.llm:
            raise ValueError("LLM provider not set. Please set an LLM provider before running actions.")
            
        for action in self.actions:
            if action.name == action_name:
                return await action.run(**kwargs)
        raise ValueError(f"Action {action_name} not found")
