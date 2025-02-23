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
        
        # Initialize multiple developers
        self.developers = [
            Developer() for _ in range(2)  # Start with 2 developers
        ]
        for dev in self.developers:
            dev.set_llm(self.llm)
            
        self.qa_engineer = QAEngineer()
        self.qa_engineer.set_llm(self.llm)
        
        self.code_reviewer = CodeReviewer()
        self.code_reviewer.set_llm(self.llm)
        
        # Token tracking
        self.token_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "actions": []
        }
    
    def _track_tokens(self, action_name: str, role: str, input_tokens: int, output_tokens: int):
        """Track token usage for an action."""
        # Update cumulative totals
        self.token_usage["input_tokens"] += input_tokens
        self.token_usage["output_tokens"] += output_tokens
        
        # Track per-action usage
        self.token_usage["actions"].append({
            "action": action_name,
            "role": role,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        })
    
    async def _run_action(self, role: Any, action: str, **kwargs) -> Dict:
        """Run an action and track its token usage."""
        try:
            # Run the action
            print(f"\n[DEBUG] SoftwareTeam._run_action starting {action}")
            start_time = datetime.now()
            result = await role.run(action, **kwargs)
            end_time = datetime.now()
            print(f"[DEBUG] Result from role.run: {result}")

            # Validate token counts
            if not isinstance(result, dict):
                raise ValueError(f"Expected dict result from {action}, got {type(result)}")
            if "input_tokens" not in result or "output_tokens" not in result:
                raise ValueError(f"Token counts missing in result from {action}")
            if result["input_tokens"] == 0 or result["output_tokens"] == 0:
                raise ValueError(f"Zero token counts detected in result from {action}")

            # Extract token counts
            input_tokens = result["input_tokens"]
            output_tokens = result["output_tokens"]
            print(f"[DEBUG] Token counts: input={input_tokens}, output={output_tokens}")
            
            # Remove token counts from result to avoid duplication
            result.pop("input_tokens", None)
            result.pop("output_tokens", None)
            
            # Track tokens
            self._track_tokens(action, role.__class__.__name__, input_tokens, output_tokens)
            
            # Add execution time 
            result = result if isinstance(result, dict) else {"response": result}
            result["execution_time"] = str(end_time - start_time)
            
            return result
        except Exception as e:
            print(f"[DEBUG] Error in _run_action for {action}: {str(e)}")
            # Even on error, try to track any tokens that were used
            if isinstance(e, dict):  # Some actions return error as dict
                input_tokens = e.get("input_tokens", 0)
                output_tokens = e.get("output_tokens", 0)
                self._track_tokens(action, role.__class__.__name__, input_tokens, output_tokens)
                print(f"\nToken Usage before error in {action}:")
                print(f"- Input tokens: {input_tokens}")
                print(f"- Output tokens: {output_tokens}\n")
            raise  # Re-raise the exception

    def _save_json_artifact(self, path: str, content: Union[str, Dict]) -> None:
        """Save JSON artifact, ensuring proper formatting."""
        try:
            # Convert content to string if it's a dict
            if isinstance(content, dict):
                # Remove any existing token information at root level
                content.pop("input_tokens", None)
                content.pop("output_tokens", None)
                
                # Add cumulative token usage
                content["token_usage"] = {
                    "input_tokens": self.token_usage["input_tokens"],
                    "output_tokens": self.token_usage["output_tokens"],
                    "total_tokens": self.token_usage["input_tokens"] + self.token_usage["output_tokens"],
                    "actions": self.token_usage["actions"]
                }
                json_str = json.dumps(content, indent=2)
            else:
                # Try to parse as JSON if it's a string
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        # Remove any existing token information at root level
                        data.pop("input_tokens", None)
                        data.pop("output_tokens", None)
                        
                        # Add cumulative token usage
                        data["token_usage"] = {
                            "input_tokens": self.token_usage["input_tokens"],
                            "output_tokens": self.token_usage["output_tokens"],
                            "total_tokens": self.token_usage["input_tokens"] + self.token_usage["output_tokens"],
                            "actions": self.token_usage["actions"]
                        }
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

    async def _handle_integration_issues(self, review_result: Dict, requirements: Dict) -> None:
        """Handle integration issues by creating work items and dispatching to team."""
        if not review_result.get("conflicts"):
            return
            
        # Get work items from review
        work_items = review_result.get("new_work_items", [])
        
        # If no specific work items were created, create generic ones from conflicts
        if not work_items:
            work_items = [{
                "title": f"Fix Integration Issue: {conflict}",
                "description": conflict,
                "priority": "High",
                "dependencies": [],
                "estimated_effort": 3
            } for conflict in review_result["conflicts"]]
            
        # Have project manager plan the work
        plan = await self._run_action(
            self.project_manager,
            "PlanWork",
            work_items=work_items
        )
        
        # Process each sprint in order
        for sprint_num in sorted(plan.get("sprints", {}).keys()):
            sprint_items = plan["sprints"][sprint_num]
            
            # Create batch of implementations for this sprint
            batch_implementations = []
            
            for item in sprint_items:
                # Determine appropriate role based on work item
                if "test" in item.lower():
                    role = self.qa_engineer
                elif any(kw in item.lower() for kw in ["implement", "create", "add", "build"]):
                    role = self.developers[0]  # Assign to first available developer
                else:
                    role = self.tech_lead
                    
                # Have role implement the feature
                self._show_status(
                    f"Sprint {sprint_num} Implementation",
                    f"Implementing: {item}"
                )
                
                implementation = await self._run_action(
                    role,
                    "ImplementFeature",
                    feature=item,
                    spec=requirements
                )
                
                if implementation:
                    batch_implementations.append({
                        "feature": item,
                        "implementation": implementation
                    })
            
            # Have tech lead review the implementations
            if batch_implementations:
                self._show_status(
                    f"Sprint {sprint_num} Code Review",
                    "Tech Lead reviewing implementations:\n" +
                    "\n".join(f"- {impl['feature']}" for impl in batch_implementations)
                )
                
                for impl in batch_implementations:
                    # Review each implementation
                    review = await self._run_action(
                        self.tech_lead,
                        "ReviewCode",
                        code=impl["implementation"].get("code", ""),
                        context={
                            "feature": impl["feature"],
                            "requirements": requirements
                        }
                    )
                    
                    # Save review artifacts
                    self._save_json_artifact(
                        f"docs/code_review_{impl['feature'].lower().replace(' ', '_')}.json",
                        review
                    )
                
                # Run tests
                self._show_status(
                    f"Sprint {sprint_num} Testing",
                    "QA Engineer running tests"
                )
                
                test_results = await self._run_action(
                    self.qa_engineer,
                    "RunTests",
                    implementations=batch_implementations
                )
                
                # Save test results
                self._save_json_artifact(
                    f"docs/test_results_sprint_{sprint_num}.json",
                    test_results
                )

    async def _run_integration_review(
        self,
        batch_implementations: List[Dict],
        previous_implementations: List[Dict],
        requirements: Dict
    ) -> Dict:
        """Run integration review and handle any issues."""
        # Run the review
        review_result = await self._run_action(
            self.architect,
            "ReviewIntegration",
            batch_implementations=batch_implementations,
            previous_implementations=previous_implementations,
            requirements=requirements
        )
        
        # If there are conflicts, handle them by creating and implementing work items
        if review_result.get("conflicts"):
            await self._handle_integration_issues(review_result, requirements)
            
        return review_result

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
            
            # After implementing batch features, review their integration
            if batch_implementations:
                self._show_status(
                    f"Reviewing Batch {batch_num} Integration",
                    f"Architect reviewing integration of {len(batch_implementations)} features:\n" +
                    "\n".join(f"- {impl.get('feature', 'unknown')}" for impl in batch_implementations)
                )
                
                review_result = await self._run_integration_review(
                    batch_implementations,
                    implementations,
                    requirements_analysis
                )
                
                if not review_result.get("approved", False):
                    conflicts = review_result.get("conflicts", [])
                    raise ValueError(
                        f"Failed to integrate batch {batch_num}:\n\n"
                        f"Critical conflicts:\n" +
                        "\n".join(f"- {conflict}" for conflict in conflicts)
                    )
                
                # Add successful batch implementations to our total implementations
                implementations.extend(batch_implementations)
                
                # Save integration review
                self._save_json_artifact(
                    f"docs/integration_review_batch_{batch_num}.json",
                    review_result
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
                code=impl.get("implementation", {}).get("code", ""),
                context={
                    "feature": impl.get("feature", "unknown"),
                    "requirements": requirements_analysis
                }
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
            requirements=requirements_analysis,
            implementation={
                "core": core_implementation,
                "features": implementations,
                "test_results": test_results
            },
            original_prompt=self.prompt
        )

        # Architect validates technical implementation
        arch_validation = await self._run_action(
            self.architect,
            "ReviewRequirements",
            requirements=requirements_analysis,
            implementation={
                "core": core_implementation,
                "features": implementations,
                "test_results": test_results
            },
            original_prompt=self.prompt
        )

        # Save validation results regardless of outcome
        validation_results = {
            "business_validation": pm_validation,
            "technical_validation": arch_validation,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }

        # Check business validation
        if not pm_validation.get("approved", False):
            missing_reqs = pm_validation.get("missing_requirements", [])
            deviations = pm_validation.get("deviations", [])
            quality_issues = pm_validation.get("quality_issues", [])
            
            error_details = []
            if missing_reqs:
                error_details.append("Missing Requirements:\n" + "\n".join(f"- {req}" for req in missing_reqs))
            if deviations:
                error_details.append("Implementation Deviations:\n" + "\n".join(f"- {dev}" for dev in deviations))
            if quality_issues:
                error_details.append("Quality Issues:\n" + "\n".join(f"- {issue}" for issue in quality_issues))
            
            if error_details:
                self._show_status(
                    "Validation Failed",
                    "\n\n".join(error_details)
                )
            
            validation_results["status"] = "failed"
            validation_results["error"] = "Implementation does not fully satisfy business requirements"
            validation_results["error_details"] = error_details
            
            # Save validation results before raising error
            self._save_json_artifact(
                "docs/validation_results.json",
                validation_results
            )
            
            # Save token usage statistics
            self._save_json_artifact(
                "docs/token_usage.json",
                self.token_usage
            )
            
            raise ValueError(
                "Implementation does not fully satisfy business requirements.\n" +
                "\n".join(error_details)
            )

        # Check technical validation
        if not arch_validation.get("approved", False):
            missing_reqs = arch_validation.get("missing_requirements", [])
            deviations = arch_validation.get("deviations", [])
            quality_issues = arch_validation.get("quality_issues", [])
            
            error_details = []
            if missing_reqs:
                error_details.append("Missing Technical Requirements:\n" + "\n".join(f"- {req}" for req in missing_reqs))
            if deviations:
                error_details.append("Technical Deviations:\n" + "\n".join(f"- {dev}" for dev in deviations))
            if quality_issues:
                error_details.append("Technical Quality Issues:\n" + "\n".join(f"- {issue}" for issue in quality_issues))
            
            if error_details:
                self._show_status(
                    "Technical Validation Failed",
                    "\n\n".join(error_details)
                )
            
            validation_results["status"] = "failed"
            validation_results["error"] = "Implementation does not meet technical requirements"
            validation_results["error_details"] = error_details
            
            # Save validation results before raising error
            self._save_json_artifact(
                "docs/validation_results.json",
                validation_results
            )
            
            # Save token usage statistics
            self._save_json_artifact(
                "docs/token_usage.json",
                self.token_usage
            )
            
            raise ValueError(
                "Implementation does not meet technical requirements.\n" +
                "\n".join(error_details)
            )

        # Save validation results for successful case
        self._save_json_artifact(
            "docs/validation_results.json",
            validation_results
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
