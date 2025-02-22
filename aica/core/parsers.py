"""Parsers for different file formats."""

import re
from typing import Dict, List, Union

import yaml


def parse_markdown_list(lines: List[str], indent: str = "") -> List[Union[str, Dict]]:
    """Parse a markdown list into a structured format."""
    items = []
    current_item = None
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Check if line is a list item
        if stripped.startswith(("- ", "* ", "+ ")):
            if current_item:
                items.append(current_item)
            
            # Remove list marker and get content
            content = stripped[2:].strip()
            
            # Check if item has emphasis/bold
            emphasis = re.findall(r'\*\*(.*?)\*\*', content)
            if emphasis:
                # Create dict for emphasized items
                key = emphasis[0].lower().replace(" ", "_")
                value = content.replace(f"**{emphasis[0]}**", "").strip()
                if value:
                    current_item = {key: value}
                else:
                    current_item = key
            else:
                current_item = content
        
        # Handle nested lists (indented)
        elif stripped.startswith(indent + "  - "):
            if isinstance(current_item, dict):
                key = list(current_item.keys())[0]
                if not isinstance(current_item[key], list):
                    current_item[key] = []
                current_item[key].append(stripped.strip("- "))
            else:
                if isinstance(current_item, str):
                    current_item = {current_item: []}
                current_item[list(current_item.keys())[0]].append(stripped.strip("- "))
    
    if current_item:
        items.append(current_item)
    
    return items


def parse_markdown_spec(content: str) -> Dict:
    """Parse a markdown specification into a structured format."""
    lines = content.split("\n")
    spec = {}
    current_section = None
    section_lines = []
    
    for line in lines:
        if line.startswith("# "):
            # Main title, skip
            continue
        elif line.startswith("## "):
            # Save previous section if exists
            if current_section and section_lines:
                spec[current_section.lower().replace(" ", "_")] = parse_markdown_list(section_lines)
            
            # Start new section
            current_section = line[3:].strip()
            section_lines = []
        else:
            if current_section:
                section_lines.append(line)
    
    # Save last section
    if current_section and section_lines:
        spec[current_section.lower().replace(" ", "_")] = parse_markdown_list(section_lines)
    
    return spec


def parse_spec_file(content: str, format: str = "yaml") -> Dict:
    """Parse a specification file into a structured format.
    
    Args:
        content: File content as string
        format: File format ('yaml' or 'markdown')
    
    Returns:
        Dict containing the parsed specification
    """
    if format == "yaml":
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML: {e}")
    elif format == "markdown":
        return parse_markdown_spec(content)
    else:
        raise ValueError(f"Unsupported format: {format}")
