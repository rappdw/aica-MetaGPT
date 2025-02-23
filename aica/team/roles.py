"""Roles for the software development team."""

from typing import Dict, List, Optional, Any
import json

from pydantic import BaseModel, ConfigDict, Field

from aica.core.base import Action, LLMProvider, Role
from aica.team.actions import (
    AnalyzeRequirements,
    CreateProjectStructure,
    ImplementFeature,
    PlanWork,
    ReviewCode,
    ReviewIntegration,
    ReviewRequirements,
    RunTests
)


class AnalyzeRequirements(Action):
    """Analyze project requirements and create detailed specifications."""
    name: str = "AnalyzeRequirements"
    
    async def run(self, requirements: str, spec: dict) -> Dict:
        """Analyze requirements and create detailed specifications."""
        prompt = f"""
        Analyze the following project requirements and specification:
        
        Requirements:
        {requirements}
        
        Specification:
        {spec}
        
        Create a detailed technical specification including:
        1. System components and their responsibilities
        2. Data models and storage requirements
        3. API endpoints and interfaces
        4. Technical requirements and constraints
        5. Performance considerations
        6. Testing and quality assurance requirements
        7. Project structure and organization
        
        Return your response as a JSON object with the following structure:
        {{
            "components": [...],
            "data_models": [...],
            "api_endpoints": [...],
            "technical_requirements": [...],
            "performance": [...],
            "testing": [...],
            "project_structure": [...]
        }}
        
        Ensure the response is a valid JSON object with the exact structure shown above.
        The response should start with {{ and end with }}.
        Do not include any explanatory text before or after the JSON.
        """
        try:
            result = await self._call_llm(prompt)
            
            # Extract token counts before modifying result
            token_counts = {
                "input_tokens": result.get("input_tokens", 0),
                "output_tokens": result.get("output_tokens", 0)
            }
            
            # Parse result if needed
            if isinstance(result, str):
                result = json.loads(result)
            elif isinstance(result, dict):
                # Remove token counts from inner result to avoid duplication
                result.pop("input_tokens", None)
                result.pop("output_tokens", None)
            
            # Return with token counts preserved
            return {
                "specification": result,
                "input_tokens": token_counts["input_tokens"],
                "output_tokens": token_counts["output_tokens"]
            }
        except json.JSONDecodeError as e:
            return {
                "specification": {
                    "error": f"Failed to parse specification: {str(e)}"
                },
                "input_tokens": 0,
                "output_tokens": 0
            }


class CreateProjectStructure(Action):
    """Create initial project structure with necessary files."""
    name: str = "CreateProjectStructure"
    
    async def run(self, specification: Dict) -> Dict:
        """Create project structure based on specification."""
        prompt = f"""
        You are a software architect designing the initial project structure.
        
        Specification:
        {specification}
        
        Create a project structure including:
        1. Directory layout
        2. Key files and their purposes
        3. Module organization
        4. Dependencies and configuration
        5. Documentation structure
        6. Test directory structure
        7. License file
        8. Configuration file templates
        
        Ensure the response is a valid JSON object with the exact structure shown above.
        The response should start with {{ and end with }}.
        Do not include any explanatory text before or after the JSON.
        """
        try:
            print("\n[DEBUG] CreateProjectStructure.run in roles.py")
            result = await self._call_llm(prompt)
            print(f"[DEBUG] Result from LLM: {result}")
            
            # Validate token counts are present
            if "input_tokens" not in result or "output_tokens" not in result:
                raise ValueError("Token counts missing in CreateProjectStructure LLM result")
            
            # Get token counts
            token_counts = {
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"]
            }
            
            # Get the response content
            if isinstance(result, dict) and "response" in result:
                response = result["response"]
            else:
                response = result
                
            # Parse response as JSON if needed
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    response = {"error": "Failed to parse response as JSON"}
            
            # Ensure response is a dict
            if not isinstance(response, dict):
                response = {"response": response}
            
            # Add project_structure key but preserve token counts at top level
            final_result = {
                "project_structure": response,
                "input_tokens": token_counts["input_tokens"],
                "output_tokens": token_counts["output_tokens"]
            }
            
            print(f"[DEBUG] Final result from CreateProjectStructure: {final_result}")
            return final_result
            
        except json.JSONDecodeError as e:
            # Even on error, try to preserve token counts
            token_counts = result.get("token_counts", {
                "input_tokens": 0,
                "output_tokens": 0
            }) if isinstance(result, dict) else {
                "input_tokens": 0,
                "output_tokens": 0
            }
            
            error_result = {
                "project_structure": {
                    "files": {},
                    "error": f"Failed to parse project structure: {str(e)}"
                },
                "input_tokens": token_counts["input_tokens"],
                "output_tokens": token_counts["output_tokens"]
            }
            print(f"[DEBUG] Error result: {error_result}")
            return error_result


class ImplementFeature(Action):
    """Implement a specific feature with tests."""
    name: str = "ImplementFeature"
    
    async def run(self, feature: str, spec: Dict) -> Dict:
        """Implement a feature with appropriate tests."""
        prompt = f"""
        Implement the following feature with tests:
        
        Feature: {feature}
        Specification: {spec}
        
        Return your response as a JSON object with the following structure:
        {{
            "implementation": {{
                "files": {{
                    "src/package_name/{feature}.py": "content...",
                    "tests/test_{feature}.py": "content..."
                }}
            }},
            "feature": "{feature}"
        }}
        
        Ensure:
        1. Code follows PEP 8 style guide
        2. Type hints are used
        3. Docstrings are included
        4. Unit tests are written
        5. Edge cases are handled
        6. Error handling is implemented
        
        Ensure the response is a valid JSON object with the exact structure shown above.
        The response should start with {{ and end with }}.
        Do not include any explanatory text before or after the JSON.
        """
        try:
            result = await self._call_llm(prompt)
            if isinstance(result, str):
                result = json.loads(result)
            return result
        except json.JSONDecodeError as e:
            return {
                "implementation": {
                    "files": {}
                },
                "feature": feature,
                "error": f"Failed to parse implementation: {str(e)}"
            }


class ReviewCode(Action):
    """Review code for quality and standards."""
    name: str = "ReviewCode"
    
    async def run(self, code: str) -> Dict:
        """Review code and provide feedback."""
        prompt = f"""
        Review the following code for quality and standards:
        
        {code}
        
        Return your response as a JSON object with the following structure:
        {{
            "needs_changes": true/false,
            "suggestions": [
                {{
                    "file": "path/to/file.py",
                    "line": 123,
                    "suggestion": "description..."
                }}
            ]
        }}
        
        Check for:
        1. Code style (PEP 8)
        2. Type hints
        3. Documentation
        4. Test coverage
        5. Error handling
        6. Performance issues
        7. Security concerns
        
        Ensure the response is a valid JSON object with the exact structure shown above.
        The response should start with {{ and end with }}.
        Do not include any explanatory text before or after the JSON.
        """
        try:
            result = await self._call_llm(prompt)
            if isinstance(result, str):
                result = json.loads(result)
            return {"review": result}
        except json.JSONDecodeError as e:
            return {
                "review": {
                    "needs_changes": True,
                    "suggestions": [{
                        "file": "unknown",
                        "line": 0,
                        "suggestion": f"Failed to parse review: {str(e)}"
                    }]
                }
            }


class RunTests(Action):
    """Run tests and verify coverage."""
    name: str = "RunTests"
    
    async def run(self, implementations: List[Dict]) -> Dict:
        """Run tests and check coverage."""
        prompt = f"""
        Create and run tests for the following implementations:
        
        {implementations}
        
        Return your response as a JSON object with the following structure:
        {{
            "files": {{
                "tests/test_core.py": "content...",
                "tests/test_git_metrics.py": "content...",
                "tests/test_excel_report.py": "content...",
                "tests/test_statistical_analysis.py": "content..."
            }},
            "results": {{
                "total_tests": 42,
                "passed": 42,
                "failed": 0,
                "coverage": 95.5
            }}
        }}
        
        Verify:
        1. All tests pass
        2. Coverage meets requirements (80%+)
        3. Edge cases are tested
        4. Integration tests are included
        5. Performance tests if applicable
        
        Ensure the response is a valid JSON object with the exact structure shown above.
        The response should start with {{ and end with }}.
        Do not include any explanatory text before or after the JSON.
        """
        try:
            result = await self._call_llm(prompt)
            if isinstance(result, str):
                result = json.loads(result)
            return {"test_files": result}
        except json.JSONDecodeError as e:
            return {
                "test_files": {
                    "files": {},
                    "results": {
                        "total_tests": 0,
                        "passed": 0,
                        "failed": 1,
                        "coverage": 0,
                        "error": f"Failed to parse test results: {str(e)}"
                    }
                }
            }


class BaseRole(BaseModel):
    """Base class for all roles with LLM support."""
    name: str
    profile: str
    llm: Optional[LLMProvider] = None
    actions: List[Action] = Field(default_factory=list)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def set_llm(self, llm: LLMProvider) -> None:
        """Set the LLM provider for this role and all its actions."""
        self.llm = llm
        for action in self.actions:
            action.set_llm(llm)
    
    async def run(self, action_name: str, **kwargs) -> Dict[str, Any]:
        """Run an action by name."""
        # Find the action instance by name
        action = next((a for a in self.actions if a.name == action_name), None)
        if not action:
            available_actions = [a.name for a in self.actions]
            raise ValueError(f"Action {action_name} not found. Available actions: {available_actions}")
        
        # Run the action
        return await action.run(**kwargs)


class ProjectManager(BaseRole):
    """Manages the overall project and coordinates between roles."""
    def __init__(self):
        super().__init__(
            name="Project Manager",
            profile="Experienced project manager who coordinates the development process",
            actions=[
                AnalyzeRequirements(),
                ReviewRequirements(),
                PlanWork()
            ]
        )


class Architect(BaseRole):
    """Designs the system architecture and makes high-level technical decisions."""
    def __init__(self):
        super().__init__(
            name="Architect",
            profile="Senior software architect who designs system architecture",
            actions=[
                CreateProjectStructure(),
                ReviewIntegration(),
                ReviewRequirements()  # Add ReviewRequirements for technical validation
            ]
        )


class TechLead(BaseRole):
    """Technical lead who guides implementation and reviews code."""
    def __init__(self):
        super().__init__(
            name="Tech Lead",
            profile="Senior developer who guides implementation and reviews code",
            actions=[
                ImplementFeature(),
                ReviewCode(),
                ReviewRequirements()
            ]
        )


class Developer(BaseRole):
    """Implements code based on specifications and architecture."""
    def __init__(self):
        super().__init__(
            name="Developer",
            profile="Software developer who implements features",
            actions=[ImplementFeature()]
        )


class CodeReviewer(BaseRole):
    """Reviews code and ensures quality standards."""
    def __init__(self):
        super().__init__(
            name="Code Reviewer",
            profile="Senior developer who reviews code and ensures quality",
            actions=[ReviewCode()]
        )


class QAEngineer(BaseRole):
    """Quality assurance engineer who tests implementations."""
    def __init__(self):
        super().__init__(
            name="QA Engineer",
            profile="Quality assurance engineer who tests and verifies implementations",
            actions=[
                RunTests(),
                ReviewRequirements()
            ]
        )
