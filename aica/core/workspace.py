"""Workspace management for AICA."""

import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


class Workspace:
    """Manages the workspace for project generation."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.src_dir = root_dir / "src"
        self.docs_dir = root_dir / "docs"
        self.tests_dir = root_dir / "tests"
    
    def initialize(self):
        """Initialize the workspace directory structure."""
        # Create directories
        for directory in [self.root_dir, self.src_dir, self.docs_dir, self.tests_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            console.print(f"📁 Created directory: {directory}")
    
    def clean(self):
        """Clean the workspace by removing all contents."""
        if self.root_dir.exists():
            shutil.rmtree(self.root_dir)
            console.print(f"🗑️  Cleaned workspace: {self.root_dir}")
    
    def get_file_path(self, relative_path: str) -> Path:
        """Get the absolute path for a file in the workspace."""
        return self.root_dir / relative_path
    
    def write_file(self, relative_path: str, content: str):
        """Write content to a file in the workspace."""
        file_path = self.get_file_path(relative_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        console.print(f"📝 Created file: {file_path}")
    
    def read_file(self, relative_path: str) -> Optional[str]:
        """Read content from a file in the workspace."""
        file_path = self.get_file_path(relative_path)
        if file_path.exists():
            return file_path.read_text()
        return None
