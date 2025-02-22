"""Software development team implementation."""

from typing import Dict, List, Optional, Union, Any
import json
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from aica.core.workspace import Workspace
from aica.core.base import LLMProvider
from aica.core.config import Config, LLMConfig
from aica.team.roles import (
    Architect,
    CodeReviewer,
    Developer,
    ProjectManager,
    QAEngineer,
    TechLead,
)

console = Console()


class SoftwareTeam:
    """Manages a team of AI agents for software development."""

    def __init__(
        self,
        workspace: Workspace,
        prompt: str,
        config: Optional[Dict] = None
    ):
        self.workspace = workspace
        self.prompt = prompt
        self.config = config or {}
        
        # Get LLM provider
        llm_config = self.config.get("llm", {})
        llm_config = LLMConfig(**llm_config) if llm_config else LLMConfig()
        self.llm = llm_config.get_provider()
        
        if not self.llm:
            raise ValueError("No LLM provider configured. Please check your configuration.")
        
        # Initialize roles with LLM
        self.project_manager = ProjectManager()
        self.project_manager.set_llm(self.llm)
        
        self.architect = Architect()
        self.architect.set_llm(self.llm)
        
        self.tech_lead = TechLead()
        self.tech_lead.set_llm(self.llm)
        
        self.developers = [Developer() for _ in range(self.config.get("num_developers", 3))]
        for dev in self.developers:
            dev.set_llm(self.llm)
        
        self.code_reviewer = CodeReviewer()
        self.code_reviewer.set_llm(self.llm)
        
        self.qa_engineer = QAEngineer()
        self.qa_engineer.set_llm(self.llm)
        
        # Token tracking
        self.token_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "actions": []
        }
    
    def _track_tokens(self, action_name: str, role: str, input_tokens: int, output_tokens: int):
        """Track token usage for an action."""
        self.token_usage["input_tokens"] += input_tokens
        self.token_usage["output_tokens"] += output_tokens
        self.token_usage["actions"].append({
            "action": action_name,
            "role": role,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        })
    
    async def _run_action(self, role: Any, action: str, **kwargs) -> Dict:
        """Run an action and track its token usage."""
        result = await role.run(action, **kwargs)
        
        # Extract token usage if available
        input_tokens = result.pop("input_tokens", 0) if isinstance(result, dict) else 0
        output_tokens = result.pop("output_tokens", 0) if isinstance(result, dict) else 0
        
        self._track_tokens(action, role.__class__.__name__, input_tokens, output_tokens)
        return result

    def _save_json_artifact(self, path: str, content: Union[str, Dict]) -> None:
        """Save JSON artifact, ensuring proper formatting."""
        try:
            # Convert content to string if it's a dict
            if isinstance(content, dict):
                json_str = json.dumps(content, indent=2)
            else:
                # Try to parse as JSON if it's a string
                try:
                    data = json.loads(content)
                    json_str = json.dumps(data, indent=2)
                except json.JSONDecodeError:
                    # If not valid JSON, save as markdown
                    json_str = f"```json\n{content}\n```"
            
            # Write the string content
            self.workspace.write_file(path, json_str)
            
            # Print a summary if it's JSON
            try:
                data = json.loads(json_str)
                if isinstance(data, dict):
                    summary = {k: "..." if isinstance(v, (dict, list)) else v for k, v in data.items()}
                    console.print(f"📄 Saved {path}:")
                    console.print(json.dumps(summary, indent=2))
            except json.JSONDecodeError:
                pass
                
        except Exception as e:
            console.print(f"[red]Error saving {path}: {str(e)}[/red]")
            # Save as-is with error note
            error_str = f"```\nError: {str(e)}\nOriginal content:\n{content}\n```"
            self.workspace.write_file(path, error_str)

    def _show_status(self, title: str, details: str) -> None:
        """Show a status update panel."""
        console.print()
        console.print(Panel(
            Markdown(details),
            title=f"🔄 {title}",
            expand=False
        ))
        console.print()

    async def run(self, spec: dict):
        """Run the software development process."""
        console.print(Panel.fit("🚀 Starting project generation...", title="AICA"))
        
        # 1. Project Manager analyzes requirements
        self._show_status(
            "Project Manager Analysis",
            "Analyzing project requirements and creating detailed specifications:\n"
            "- Identifying system components\n"
            "- Defining data models\n"
            "- Planning API endpoints\n"
            "- Setting technical requirements"
        )
        requirements_analysis = await self._run_action(
            self.project_manager,
            "AnalyzeRequirements",
            requirements=self.prompt,
            spec=spec
        )
        
        # Save requirements analysis
        self._save_json_artifact(
            "docs/requirements_analysis.json",
            requirements_analysis.get("specification", "{}")
        )
        
        # 2. Architect creates project structure
        self._show_status(
            "Architect Design",
            "Creating project structure and initial files:\n"
            "- Setting up project layout\n"
            "- Configuring development tools\n"
            "- Creating dependency specifications\n"
            "- Establishing testing framework"
        )
        project_structure = await self._run_action(
            self.architect,
            "CreateProjectStructure",
            specification=requirements_analysis
        )
        
        # Create project structure
        structure = project_structure.get("project_structure", {})
        if isinstance(structure, str):
            try:
                structure = json.loads(structure)
            except:
                structure = {"error": "Failed to parse project structure"}
        
        # Save project structure for reference
        self._save_json_artifact(
            "docs/project_structure.json",
            structure
        )
        
        # Create initial project files
        files_created = []
        for file_path, content in structure.get("files", {}).items():
            self.workspace.write_file(file_path, content)
            files_created.append(file_path)
        
        if files_created:
            self._show_status(
                "Project Structure Created",
                "Created initial project files:\n" +
                "\n".join(f"- `{f}`" for f in sorted(files_created))
            )
        
        # 3. Tech Lead implements core functionality
        self._show_status(
            "Tech Lead Implementation",
            "Implementing core functionality:\n"
            "- Setting up base classes\n"
            "- Implementing core utilities\n"
            "- Creating shared components\n"
            "- Establishing design patterns"
        )
        core_implementation = await self._run_action(
            self.tech_lead,
            "ImplementFeature",
            feature="core",
            spec=requirements_analysis
        )
        
        # Save core implementation metadata
        self._save_json_artifact(
            "docs/core_implementation.json",
            core_implementation
        )
        
        # Create core implementation files
        core_files = core_implementation.get("implementation", {}).get("files", {})
        core_files_created = []
        for file_path, content in core_files.items():
            self.workspace.write_file(file_path, content)
            core_files_created.append(file_path)
        
        if core_files_created:
            self._show_status(
                "Core Implementation Complete",
                "Created core implementation files:\n" +
                "\n".join(f"- `{f}`" for f in sorted(core_files_created))
            )
        
        # 4. Developers implement features in parallel
        # Get features from requirements analysis
        features = requirements_analysis.get("specification", {}).get("components", [])
        
        # If no features found, ask Project Manager to refine the analysis
        if not features:
            self._show_status(
                "Analysis Refinement",
                "No features found in initial analysis. Asking Project Manager to refine requirements."
            )
            
            refined_analysis = await self._run_action(
                self.project_manager,
                "RefineRequirements",
                analysis=requirements_analysis,
                feedback="Please identify specific feature components that need to be implemented."
            )
            
            # Update our requirements analysis with the refined version
            requirements_analysis = refined_analysis
            features = refined_analysis.get("specification", {}).get("components", [])
            
            if not features:
                # If still no features, ask Architect for technical breakdown
                self._show_status(
                    "Technical Breakdown",
                    "No features identified in refined requirements. Asking Architect for technical component breakdown."
                )
                
                arch_analysis = await self._run_action(
                    self.architect,
                    "BreakdownSystem",
                    requirements=refined_analysis,
                    feedback="Please break down the system into specific implementable components."
                )
                
                # Update our requirements analysis with the architect's breakdown
                requirements_analysis = arch_analysis
                features = arch_analysis.get("specification", {}).get("components", [])
                
                if not features:
                    raise ValueError(
                        "Unable to identify system components after Project Manager and Architect analysis. "
                        "Please check that the initial requirements are clear enough to derive specific features."
                    )
        
        # Filter out core components that are already implemented
        features = [f for f in features if not (
            isinstance(f, dict) and f.get("type") == "core" or
            isinstance(f, str) and "core" in f.lower()
        )]
        
        if not features:
            # Ask Architect to identify non-core components
            self._show_status(
                "Feature Identification",
                "Only core components found. Asking Architect to identify specific feature components."
            )
            
            arch_features = await self._run_action(
                self.architect,
                "IdentifyFeatures",
                analysis=requirements_analysis,
                feedback="Please identify specific non-core feature components that need to be implemented."
            )
            
            # Update our requirements analysis with the architect's features
            requirements_analysis = arch_features
            features = [f for f in arch_features.get("specification", {}).get("components", [])
                       if not (isinstance(f, dict) and f.get("type") == "core" or
                             isinstance(f, str) and "core" in f.lower())]
            
            if not features:
                raise ValueError(
                    "No non-core features could be identified. Please check that the requirements "
                    "include functionality beyond the core system components."
                )

        # Ensure we have a reasonable number of features for our developers
        max_features_per_batch = len(self.developers)
        feature_batches = [features[i:i + max_features_per_batch] 
                         for i in range(0, len(features), max_features_per_batch)]
        
        implementations = []
        for batch_num, feature_batch in enumerate(feature_batches, 1):
            if batch_num > 1:
                self._show_status(
                    f"Starting Batch {batch_num}",
                    f"Implementing next batch of {len(feature_batch)} features:\n" +
                    "\n".join(f"- {f.get('name', f) if isinstance(f, dict) else f}" 
                             for f in feature_batch)
                )
            
            # Distribute features among developers
            batch_implementations = []
            for dev_num, (dev, feature) in enumerate(zip(self.developers, feature_batch), 1):
                feature_name = feature.get("name", feature) if isinstance(feature, dict) else feature
                
                # Get feature details if available
                feature_spec = feature if isinstance(feature, dict) else {"name": feature}
                
                self._show_status(
                    f"Developer {dev_num} Implementation",
                    f"Implementing {feature_name} feature:\n"
                    f"- Creating feature module\n"
                    f"- Implementing business logic\n"
                    f"- Adding type hints and documentation\n"
                    f"- Writing unit tests"
                )
                
                impl = await self._run_action(
                    dev,
                    "ImplementFeature",
                    feature=feature_name,
                    spec={
                        **requirements_analysis,
                        "feature": feature_spec,  # Pass specific feature details
                        "implemented_features": implementations  # Pass previous implementations for context
                    }
                )
                batch_implementations.append(impl)
                
                # Save feature implementation metadata
                self._save_json_artifact(
                    f"docs/feature_{feature_name}_implementation.json",
                    impl
                )
                
                # Create feature implementation files
                feature_files = impl.get("implementation", {}).get("files", {})
                feature_files_created = []
                for file_path, content in feature_files.items():
                    self.workspace.write_file(file_path, content)
                    feature_files_created.append(file_path)
                
                if feature_files_created:
                    self._show_status(
                        f"{feature_name} Implementation Complete",
                        f"Created {feature_name} implementation files:\n" +
                        "\n".join(f"- `{f}`" for f in sorted(feature_files_created))
                    )
            
            # Add batch implementations to overall implementations
            implementations.extend(batch_implementations)
            
            if batch_num < len(feature_batches):
                # Review and integrate batch before moving to next one
                self._show_status(
                    f"Batch {batch_num} Integration",
                    "Reviewing and integrating batch implementation:\n"
                    "- Checking for dependencies\n"
                    "- Verifying interfaces\n"
                    "- Running integration tests"
                )
                
                integration_review = await self._run_action(
                    self.architect,
                    "ReviewIntegration",
                    batch_implementations=batch_implementations,
                    previous_implementations=implementations[:-len(batch_implementations)],
                    requirements=requirements_analysis
                )
                
                if not integration_review.get("success", False):
                    raise ValueError(
                        f"Failed to integrate batch {batch_num}: " +
                        integration_review.get("feedback", "Integration issues detected")
                    )
                
                self._show_status(
                    f"Batch {batch_num} Complete",
                    "✅ Successfully implemented and integrated batch:\n" +
                    "\n".join(f"- {f.get('name', f) if isinstance(f, dict) else f}" 
                             for f in feature_batch)
                )

        # 5. Code Reviewer reviews implementations
        self._show_status(
            "Code Review",
            "Reviewing all implementations:\n"
            "- Checking code style and quality\n"
            "- Verifying type hints\n"
            "- Reviewing documentation\n"
            "- Analyzing test coverage"
        )
        
        reviews = []
        for impl in [core_implementation] + implementations:
            feature = impl.get("feature", "unknown")
            self._show_status(
                f"Reviewing {feature}",
                f"Performing detailed review of {feature} implementation"
            )
            
            review = await self._run_action(
                self.code_reviewer,
                "ReviewCode",
                code=impl.get("implementation", {}).get("files", {})
            )
            reviews.append(review)
            
            # Save review
            self._save_json_artifact(
                f"docs/review_{feature}.json",
                review
            )

        # 6. QA Engineer creates and runs tests
        self._show_status(
            "Quality Assurance",
            "Creating and running tests:\n"
            "- Writing unit tests\n"
            "- Adding integration tests\n"
            "- Running test suite\n"
            "- Checking coverage metrics"
        )
        
        test_results = await self._run_action(
            self.qa_engineer,
            "RunTests",
            implementations=implementations
        )
        
        # Save test results
        self._save_json_artifact(
            "docs/test_results.json",
            test_results
        )
        
        # Create test files
        test_files = test_results.get("test_files", {}).get("files", {})
        test_files_created = []
        for file_path, content in test_files.items():
            self.workspace.write_file(file_path, content)
            test_files_created.append(file_path)
        
        if test_files_created:
            self._show_status(
                "Test Suite Created",
                "Created test files:\n" +
                "\n".join(f"- `{f}`" for f in sorted(test_files_created))
            )
        
        # Show final results
        results = test_results.get("test_files", {}).get("results", {})
        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                results = {}
        
        self._show_status(
            "Project Generation Complete",
            f"Final test results:\n"
            f"- Total tests: {results.get('total_tests', 'unknown')}\n"
            f"- Passed: {results.get('passed', 'unknown')}\n"
            f"- Failed: {results.get('failed', 'unknown')}\n"
            f"- Coverage: {results.get('coverage', 'unknown')}%"
        )
        
        # Final validation of implementation against requirements
        self._show_status(
            "Final Validation",
            "Validating implementation against original requirements:\n"
            "- Checking feature completeness\n"
            "- Verifying architectural compliance\n"
            "- Ensuring all requirements are met"
        )

        # Project Manager validates business requirements
        pm_validation = await self._run_action(
            self.project_manager,
            "ReviewRequirements",
            prompt=self.prompt,
            requirements=requirements_analysis,
            implementation={
                "core": core_implementation,
                "features": implementations,
                "test_results": test_results
            }
        )

        if not pm_validation.get("complete", False):
            missing_reqs = pm_validation.get("missing_requirements", [])
            if missing_reqs:
                self._show_status(
                    "Missing Requirements",
                    "The following requirements were not fully implemented:\n" +
                    "\n".join(f"- {req}" for req in missing_reqs)
                )
            raise ValueError(
                "Implementation does not fully satisfy business requirements. " +
                pm_validation.get("feedback", "Please review the requirements and implementation.")
            )

        # Architect validates technical implementation
        arch_validation = await self._run_action(
            self.architect,
            "ReviewArchitecture",
            requirements=requirements_analysis,
            implementation={
                "core": core_implementation,
                "features": implementations,
                "test_results": test_results
            }
        )

        if not arch_validation.get("approved", False):
            tech_issues = arch_validation.get("issues", [])
            if tech_issues:
                self._show_status(
                    "Technical Issues",
                    "The following technical issues were identified:\n" +
                    "\n".join(f"- {issue}" for issue in tech_issues)
                )
            raise ValueError(
                "Implementation does not meet technical requirements. " +
                arch_validation.get("feedback", "Please review the architecture and implementation.")
            )

        # Save validation results
        self._save_json_artifact(
            "docs/validation_results.json",
            {
                "business_validation": pm_validation,
                "technical_validation": arch_validation,
                "timestamp": datetime.now().isoformat()
            }
        )

        self._show_status(
            "Validation Complete",
            "✅ Implementation successfully validated:\n"
            "- All business requirements satisfied\n"
            "- Architecture and technical requirements met\n"
            "- Test coverage and quality metrics achieved"
        )

        # Save token usage statistics
        self._save_json_artifact(
            "docs/token_usage.json",
            self.token_usage
        )
        
        # Display token usage summary
        total_tokens = self.token_usage["input_tokens"] + self.token_usage["output_tokens"]
        console.print("\n[bold]Token Usage Summary:[/bold]")
        console.print(f"Input Tokens:  {self.token_usage['input_tokens']:,}")
        console.print(f"Output Tokens: {self.token_usage['output_tokens']:,}")
        console.print(f"Total Tokens:  {total_tokens:,}")
        
        # Display top 5 most token-intensive actions
        sorted_actions = sorted(
            self.token_usage["actions"],
            key=lambda x: x["input_tokens"] + x["output_tokens"],
            reverse=True
        )[:5]
        
        if sorted_actions:
            console.print("\n[bold]Top 5 Token-Intensive Actions:[/bold]")
            for action in sorted_actions:
                total = action["input_tokens"] + action["output_tokens"]
                console.print(
                    f"{action['role']}.{action['action']}: {total:,} tokens "
                    f"({action['input_tokens']:,} in, {action['output_tokens']:,} out)"
                )
        
        console.print(Panel.fit("✨ Project generation completed!", title="AICA"))
