"""Roles for the software development team."""

from typing import Dict, List, Optional, Any
import json

from pydantic import BaseModel, ConfigDict, Field

from aica.core.base import Action, LLMProvider, Role


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
            result = await self.llm.aask(prompt)
            if isinstance(result, str):
                result = json.loads(result)
            return {"specification": result}
        except json.JSONDecodeError as e:
            return {
                "specification": {
                    "error": f"Failed to parse specification: {str(e)}"
                }
            }


class CreateProjectStructure(Action):
    """Create initial project structure with necessary files."""
    name: str = "CreateProjectStructure"
    
    async def run(self, specification: Dict) -> Dict:
        """Create project structure based on specification."""
        prompt = f"""
        Based on the following specification, create the initial project structure and files:
        
        {specification}
        
        Return your response as a JSON object with the following structure:
        {{
            "files": {{
                "pyproject.toml": "content...",
                "README.md": "content...",
                ".gitignore": "content...",
                ".pre-commit-config.yaml": "content...",
                "src/package_name/__init__.py": "content...",
                "tests/__init__.py": "content..."
            }}
        }}
        
        Include:
        1. pyproject.toml with dependencies
        2. README.md with setup and usage instructions
        3. .gitignore file
        4. Pre-commit configuration
        5. Basic package structure
        6. Test directory structure
        7. License file
        8. Configuration file templates
        
        Ensure the response is a valid JSON object with the exact structure shown above.
        The response should start with {{ and end with }}.
        Do not include any explanatory text before or after the JSON.
        """
        try:
            result = await self.llm.aask(prompt)
            if isinstance(result, str):
                result = json.loads(result)
            return {"project_structure": result}
        except json.JSONDecodeError as e:
            return {
                "project_structure": {
                    "files": {},
                    "error": f"Failed to parse project structure: {str(e)}"
                }
            }


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
            result = await self.llm.aask(prompt)
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
            result = await self.llm.aask(prompt)
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
            result = await self.llm.aask(prompt)
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


class BaseRole(Role):
    """Base class for all roles with LLM support."""
    llm: Optional[Any] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ProjectManager(BaseRole):
    """Manages the overall project and coordinates between roles."""
    name: str = "Project Manager"
    profile: str = "Experienced project manager who coordinates the development process"
    
    def __init__(self):
        super().__init__()
        self.actions = [AnalyzeRequirements()]


class Architect(BaseRole):
    """Designs the system architecture and makes high-level technical decisions."""
    name: str = "Architect"
    profile: str = "Senior software architect who designs system architecture"
    
    def __init__(self):
        super().__init__()
        self.actions = [CreateProjectStructure()]


class TechLead(BaseRole):
    """Makes technical decisions and guides implementation."""
    name: str = "Tech Lead"
    profile: str = "Senior developer who guides technical implementation"
    
    def __init__(self):
        super().__init__()
        self.actions = [ImplementFeature()]


class Developer(BaseRole):
    """Implements code based on specifications and architecture."""
    name: str = "Developer"
    profile: str = "Software developer who implements features"
    
    def __init__(self):
        super().__init__()
        self.actions = [ImplementFeature()]


class CodeReviewer(BaseRole):
    """Reviews code and ensures quality standards."""
    name: str = "Code Reviewer"
    profile: str = "Senior developer who reviews code and ensures quality"
    
    def __init__(self):
        super().__init__()
        self.actions = [ReviewCode()]


class QAEngineer(BaseRole):
    """Tests implementations and ensures quality."""
    name: str = "QA Engineer"
    profile: str = "Quality assurance engineer who tests implementations"
    
    def __init__(self):
        super().__init__()
        self.actions = [RunTests()]
