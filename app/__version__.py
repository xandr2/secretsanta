"""Version information for the Secret Santa application.

This module reads version information from pyproject.toml and provides
it as a module-level constant for use throughout the application.
"""

import importlib.metadata
import tomllib
from pathlib import Path


def get_version() -> str:
    """Get the application version from pyproject.toml or package metadata.

    Returns:
        str: Version string (e.g., "0.1.0")
    """
    try:
        # Try to get version from installed package metadata first
        return importlib.metadata.version("secret-santa")
    except importlib.metadata.PackageNotFoundError:
        # Fallback: read from pyproject.toml
        try:
            # Get the project root (app/__version__.py -> app/ -> project root)
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            pyproject_path = project_root / "pyproject.toml"
            
            if not pyproject_path.exists():
                # Try alternative path resolution
                project_root = current_file.parent.parent.parent
                pyproject_path = project_root / "pyproject.toml"
            
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
                return pyproject.get("project", {}).get("version", "0.0.0")
        except (FileNotFoundError, KeyError, ValueError) as e:
            # Debug: print error in development
            import os
            if os.getenv("DEBUG"):
                print(f"Version read error: {e}")
            return "0.0.0"


# Module-level version constant
__version__ = get_version()

