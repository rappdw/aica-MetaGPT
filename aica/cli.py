"""Command line interface for AICA."""

import asyncio
from pathlib import Path
from typing import Dict, Optional
import os

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from aica.core.config import Config
from aica.core.parsers import parse_spec_file
from aica.core.workspace import Workspace
from aica.team.software_team import SoftwareTeam

console = Console()
app = typer.Typer(
    name="aica",
    help="AI Coding Assistant - An MGX-like implementation using MetaGPT",
    add_completion=False,
)

def load_prompt(prompt_file: Path) -> str:
    """Load the prompt from a file."""
    if not prompt_file:
        raise ValueError("Prompt file is required")
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    return prompt_file.read_text().strip()


def load_spec(spec_file: Optional[Path]) -> Dict:
    """Load the spec from a file.
    
    Supports both YAML and Markdown formats:
    - For .yaml/.yml files: Parse as YAML
    - For .md files: Parse structured Markdown into equivalent YAML structure
    """
    if not spec_file:
        return {}
    
    if not spec_file.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_file}")
    
    content = spec_file.read_text()
    format = "yaml" if spec_file.suffix.lower() in ['.yaml', '.yml'] else "markdown"
    
    try:
        return parse_spec_file(content, format)
    except Exception as e:
        console.print(f"[red]Error parsing {format} file: {e}[/red]")
        raise typer.Exit(1)


def load_config(config_file: Optional[Path]) -> Dict:
    """Load configuration from file."""
    if config_file and config_file.exists():
        with config_file.open() as f:
            return yaml.safe_load(f) or {}
    return {}


@app.command()
def generate(
    prompt_file: Path = typer.Argument(
        ...,
        help="Path to the prompt file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True
    ),
    output_dir: Path = typer.Option(
        "./output",
        "--output-dir", "-o",
        help="Output directory for generated files"
    ),
    spec_file: Optional[Path] = typer.Option(
        None,
        "--spec", "-s",
        help="Path to the spec file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to config file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True
    )
):
    """Generate a software project based on the provided prompt and specification."""
    try:
        # Load config from file or defaults
        config = Config(**load_config(config_file))
        
        # Create output directory
        output_dir = Path(output_dir).absolute()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load prompt
        prompt = load_prompt(prompt_file)
        
        # Load spec if provided
        spec = load_spec(spec_file) if spec_file else {}
        
        # Create workspace
        workspace = Workspace(output_dir)
        workspace.initialize()
        
        # Create software team
        team = SoftwareTeam(
            workspace=workspace,
            prompt=prompt,
            config=config.dict()
        )
        
        console.print(Panel.fit("🚀 Starting project generation...", title="AICA"))
        console.print(f"📝 Prompt: {prompt}")
        console.print(f"🔧 Spec: {spec}")
        console.print(f"📂 Output directory: {output_dir}")
        
        # Run the development process
        asyncio.run(team.run(spec=spec))
        
        console.print(Panel.fit("✨ Project generation completed!", title="AICA"))
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show the version of AICA."""
    from aica import __version__
    console.print(f"AICA version: {__version__}")


if __name__ == "__main__":
    app()
