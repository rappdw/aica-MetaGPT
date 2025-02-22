"""Configuration management for AICA."""

from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, Field

from aica.core.base import BedrockProvider, LLMProvider, OpenAIProvider


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    provider: str = Field("bedrock", description="LLM provider to use (openai or bedrock)")
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_model: str = Field("gpt-4-turbo", description="OpenAI model to use")
    
    # Bedrock settings
    bedrock_model_id: str = Field(
        "anthropic.claude-3-sonnet-20240229-v2:0",  # Updated to V2
        description="Bedrock model ID"
    )
    bedrock_region: str = Field("us-east-1", description="AWS region for Bedrock")
    bedrock_max_tokens: int = Field(
        32768,  # Claude 3.5 Sonnet supports up to 200K tokens total
        description="Maximum tokens for response generation"
    )
    
    def get_provider(self) -> LLMProvider:
        """Get the configured LLM provider."""
        if self.provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            return OpenAIProvider(api_key=self.openai_api_key, model=self.openai_model)
        elif self.provider == "bedrock":
            return BedrockProvider(
                model_id=self.bedrock_model_id,
                region=self.bedrock_region,
                max_tokens=self.bedrock_max_tokens
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")


class Config(BaseModel):
    """Configuration for AICA."""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    workspace_dir: Path = Field(default=Path("./output"))
    debug: bool = Field(default=False)


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file or use defaults."""
    if config_path is None:
        # Try to load from default locations
        default_locations = [
            Path.home() / ".aica" / "config.yaml",
            Path.cwd() / "aica.yaml",
        ]
        
        for path in default_locations:
            if path.exists():
                config_path = path
                break
    
    if config_path and config_path.exists():
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        return Config(**config_data)
    
    return Config()
