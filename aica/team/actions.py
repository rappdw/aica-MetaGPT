"""Actions that can be performed by roles."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict
import json

from aica.core.base import Action, LLMProvider


class AnalyzeRequirements(Action):
    """Analyze project requirements and create detailed specifications."""
    name: str = "AnalyzeRequirements"
    
    async def run(self, requirements: str, spec: dict) -> Dict:
        """Analyze requirements and create detailed specifications."""
        prompt = f"""
        You are a project manager analyzing requirements for a software project.
        
        Requirements:
        {requirements}
        
        Additional Specifications:
        {spec}
        
        Create a detailed analysis including:
        1. Core features and their priorities
        2. Technical requirements
        3. Dependencies and constraints
        4. Risks and mitigation strategies
        
        Format your response as JSON with these keys:
        - features: List of feature specifications
        - technical_requirements: List of technical requirements
        - dependencies: List of dependencies
        - risks: List of risks and mitigations
        """
        
        response = await self._call_llm(prompt)
        return self._parse_json_response(response)


class CreateProjectStructure(Action):
    """Create the initial project structure."""

    name: str = "CreateProjectStructure"
    description: str = "Create the initial project structure"

    async def run(self, specification: Dict) -> Dict:
        """Create project structure based on specification."""
        print("\n[DEBUG] Starting CreateProjectStructure.run")
        try:
            prompt = f"""
            You are a software architect designing the initial project structure.
            
            Specification:
            {specification}
            
            Create a project structure including:
            1. Directory layout
            2. Key files and their purposes
            3. Module organization
            4. Dependencies and configuration
            
            Format your response as JSON with these keys:
            - directories: List of directories to create
            - files: List of files with their content
            - dependencies: List of project dependencies
            - configuration: Configuration settings
            """
            
            print("[DEBUG] Calling LLM in CreateProjectStructure")
            result = await self._call_llm(prompt)
            print(f"[DEBUG] Result from LLM in CreateProjectStructure: {result}")
            
            # Validate token counts are present
            if "input_tokens" not in result or "output_tokens" not in result:
                raise ValueError("Token counts missing in CreateProjectStructure LLM result")
            
            # Keep the full result dict
            if isinstance(result, dict) and "response" in result:
                # Extract response content but keep it in a dict
                response_content = result["response"]
                if isinstance(response_content, str):
                    try:
                        response_content = json.loads(response_content)
                    except json.JSONDecodeError:
                        response_content = {"error": "Failed to parse response as JSON"}
                
                # Ensure response content is a dict
                if not isinstance(response_content, dict):
                    response_content = {"response": response_content}
                
                # Create new result with response content and preserve token counts
                final_result = {
                    **response_content,  # Response content at top level
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"]
                }
                print(f"[DEBUG] Final result from CreateProjectStructure: {final_result}")
                return final_result
            else:
                # If result isn't a dict with response key, just return it
                print(f"[DEBUG] Returning raw result: {result}")
                return result
        
        except Exception as e:
            print(f"[DEBUG] Error in CreateProjectStructure: {str(e)}")
            raise


class ImplementFeature(Action):
    """Implement a specific feature with tests."""
    name: str = "ImplementFeature"
    
    async def run(self, feature: str, spec: Dict) -> Dict:
        """Implement a feature with appropriate tests."""
        prompt = f"""
        You are a software developer implementing a feature.
        
        Feature:
        {feature}
        
        Specification:
        {spec}
        
        Implement the feature including:
        1. Source code
        2. Unit tests
        3. Documentation
        4. Integration notes
        
        Format your response as JSON with these keys:
        - implementation: Source code implementation
        - tests: Unit test implementation
        - docs: Documentation
        - integration: Integration notes
        """
        
        response = await self._call_llm(prompt)
        return self._parse_json_response(response)


class ReviewCode(Action):
    """Review code for quality and standards."""
    name: str = "ReviewCode"
    
    async def run(self, code: str) -> Dict:
        """Review code and provide feedback."""
        prompt = f"""
        You are a code reviewer evaluating code quality.
        
        Code to review:
        {code}
        
        Review the code for:
        1. Code quality and standards
        2. Potential bugs
        3. Performance issues
        4. Security concerns
        
        Format your response as JSON with these keys:
        - issues: List of issues found
        - suggestions: List of improvement suggestions
        - score: Quality score (0-100)
        - approved: Boolean indicating if code is approved
        """
        
        result = await self._call_llm(prompt)
        
        # Parse response if needed
        if isinstance(result, dict) and "response" in result:
            response = result["response"]
        else:
            response = result
            
        # Ensure we have a dictionary response
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                response = {"error": "Failed to parse response as JSON"}
        
        # Merge response with token tracking data
        if isinstance(result, dict):
            response.update({
                k: v for k, v in result.items() 
                if k in ["input_tokens", "output_tokens"]
            })
        
        return response


class ReviewIntegration(Action):
    """Review integration of multiple implementations."""
    name: str = "ReviewIntegration"
    
    async def run(
        self,
        batch_implementations: List[Dict],
        previous_implementations: List[Dict],
        requirements: Dict
    ) -> Dict:
        """Review integration of batch implementations with existing code."""
        # Validate inputs
        if not batch_implementations:
            return {
                "approved": False,
                "conflicts": [
                    "No implementations provided to review - batch_implementations is empty"
                ],
                "input_tokens": 0,
                "output_tokens": 0
            }
        
        # Format implementations for review
        batch_summary = "\n".join(
            f"- {impl.get('feature', 'unknown')}: {len(impl.get('implementation', {}).get('files', {}))} files"
            for impl in batch_implementations
        )
        
        previous_summary = "\n".join(
            f"- {impl.get('feature', 'unknown')}: {len(impl.get('implementation', {}).get('files', {}))} files"
            for impl in previous_implementations
        ) if previous_implementations else "No previous implementations"
        
        # Create review prompt
        prompt = f"""
        You are an architect reviewing the integration of multiple implementations.
        
        New implementations to integrate:
        {batch_summary}
        
        Previous implementations:
        {previous_summary}
        
        Requirements:
        {requirements}
        
        Review the integration for:
        1. Dependencies between components
        2. Interface compatibility
        3. Architectural consistency
        4. Potential conflicts
        
        Provide a detailed review in JSON format with:
        - approved: boolean indicating if integration can proceed
        - conflicts: list of any conflicts found
        - recommendations: list of suggestions for improving integration
        """
        
        return await self._call_llm(prompt)


class ReviewRequirements(Action):
    """Review and validate requirements analysis."""
    name: str = "ReviewRequirements"
    
    async def run(
        self,
        requirements: Dict,
        implementation: Dict,
        original_prompt: Optional[str] = None
    ) -> Dict:
        """Review requirements for completeness, clarity, feasibility, consistency, and testability.
        
        Args:
            requirements: Requirements analysis to review
            implementation: Current implementation details
            original_prompt: Original user prompt/requirements (optional)
        """
        # Format the review prompt
        prompt = f"""
        You are a senior software architect reviewing requirements implementation.
        
        Original Requirements:
        {original_prompt if original_prompt else "Not provided"}
        
        Requirements Analysis:
        {requirements}
        
        Current Implementation:
        {implementation}
        
        Review the implementation against requirements for:
        1. Completeness:
           - All functional requirements are implemented
           - Non-functional requirements are satisfied
           - No missing critical features
        2. Correctness:
           - Implementation matches requirements
           - No deviations from specifications
           - Edge cases are handled
        3. Quality:
           - Code follows best practices
           - Proper error handling
           - Sufficient test coverage
        
        Provide your review in JSON format with:
        {{
            "approved": boolean indicating if implementation satisfies requirements,
            "missing_requirements": ["List of requirements not fully implemented"],
            "deviations": ["List of implementations that deviate from requirements"],
            "quality_issues": ["List of quality concerns"],
            "recommendations": ["List of improvement suggestions"]
        }}
        """
        
        return await self._call_llm(prompt)


class RunTests(Action):
    """Run tests and verify coverage."""
    name: str = "RunTests"
    
    async def run(self, implementations: List[Dict]) -> Dict:
        """Run tests and check coverage."""
        prompt = f"""
        You are a QA engineer running tests on implementations.
        
        Implementations to test:
        {implementations}
        
        Perform testing including:
        1. Unit test execution
        2. Integration test execution
        3. Coverage analysis
        4. Performance testing
        
        Format your response as JSON with these keys:
        - test_results: Results of all tests
        - coverage: Test coverage metrics
        - performance: Performance test results
        - issues: List of identified issues
        - passed: Boolean indicating if all tests passed
        """
        
        result = await self._call_llm(prompt)
        
        # Parse response if needed
        if isinstance(result, dict) and "response" in result:
            response = result["response"]
        else:
            response = result
            
        # Ensure we have a dictionary response
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                response = {"error": "Failed to parse response as JSON"}
        
        # Merge response with token tracking data
        if isinstance(result, dict):
            response.update({
                k: v for k, v in result.items() 
                if k in ["input_tokens", "output_tokens"]
            })
        
        return response
