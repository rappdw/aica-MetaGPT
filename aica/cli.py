"""Command-line interface for AICA."""

import asyncio
from pathlib import Path
from typing import Dict, Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from aica.core.config import load_config
from aica.core.workspace import Workspace
from aica.team.software_team import SoftwareTeam

app = typer.Typer(
    name="aica",
    help="AI Coding Assistant - An MGX-like implementation using MetaGPT",
    add_completion=False,
)
console = Console()


def load_prompt(prompt_file: Path) -> str:
    """Load the prompt from a file."""
    return prompt_file.read_text().strip()


def load_spec(spec_file: Path) -> Dict:
    """Load the specification from a file.
    
    Supports both YAML and Markdown formats. For Markdown files,
    the entire content is passed as a string in the spec dictionary.
    """
    content = spec_file.read_text()
    if spec_file.suffix.lower() in ['.yaml', '.yml']:
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            console.print(f"[red]Error parsing YAML file: {e}[/red]")
            raise typer.Exit(1)
    else:
        # For non-YAML files (e.g., Markdown), pass the content as is
        return {"content": content}


@app.command()
def generate(
    prompt_file: Path = typer.Argument(
        ...,
        help="Path to the prompt file containing the project requirements",
        exists=True,
    ),
    spec_file: Optional[Path] = typer.Option(
        None,
        "--spec",
        "-s",
        help="Path to the specification file (YAML or Markdown)",
        exists=True,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output",
        "-o",
        help="Directory where the generated project will be created",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to the configuration file",
    ),
):
    """Generate a software project based on the provided prompt and specification."""
    try:
        # Load configuration
        config = load_config(config_file)
        
        # Create workspace
        workspace = Workspace(output_dir)
        workspace.initialize()
        
        # Load prompt and spec
        prompt = load_prompt(prompt_file)
        spec = load_spec(spec_file) if spec_file else {}
        
        # Create and run software team
        team = SoftwareTeam(config=config)
        
        console.print(Panel.fit("🚀 Starting project generation...", title="AICA"))
        console.print(f"📝 Prompt: {prompt}")
        if spec:
            console.print(f"📋 Specification loaded from: {spec_file}")
        console.print(f"📂 Output directory: {output_dir}")
        
        # Run the team asynchronously
        asyncio.run(team.run(prompt=prompt, spec=spec, workspace=workspace))
        
        console.print(Panel.fit("✨ Project generation completed!", title="AICA"))
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show the version of AICA."""
    from aica import __version__
    console.print(f"AICA version: {__version__}")


if __name__ == "__main__":
    app()
