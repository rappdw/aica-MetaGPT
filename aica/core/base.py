"""Base classes for AICA implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    async def aask(self, prompt: str) -> str:
        """Send a prompt to the LLM and get a response."""
        pass


class BedrockProvider(LLMProvider):
    """AWS Bedrock provider for Claude."""

    def __init__(self, model_id: str, region: str, max_tokens: int = 32768):
        import boto3
        self.model_id = model_id
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.max_tokens = max_tokens

    async def aask(self, prompt: str) -> str:
        """Send a prompt to Claude via AWS Bedrock."""
        import json
        
        try:
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
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            raise Exception(f"Error calling Bedrock: {str(e)}")


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
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
