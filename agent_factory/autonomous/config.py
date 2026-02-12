"""
Configuration for the Autonomous Code Improvement System.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class AutonomousConfig:
    """Configuration for autonomous code improvement runs."""
    
    # Target repository (default to tests folder for safe experimentation)
    target_repo: str = "/home/ubuntu/git/tests"
    
    # Target directory within repository (scoping)
    target_dir: str = ""  # Empty means repo root
    
    # Model configuration
    model: str = "qwen2.5-coder:latest"
    ollama_base_url: str = "http://localhost:11434"
    
    # Context size - increased for large codebases
    num_ctx: int = 32768
    
    # Run settings
    max_suggestions: int = 5  # Max suggestions to generate per run
    max_iterations: int = 3   # Max worker-judge loops per suggestion
    auto_accept: bool = False # Auto-accept all suggestions without user review
    
    # Analysis types to run
    analysis_types: List[str] = field(default_factory=lambda: [
        "maintainability",
        "documentation", 
        "error_handling",
        "performance",
    ])
    
    # File patterns to include/exclude
    include_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.ts", "*.js"])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__/*",
        "node_modules/*",
        ".git/*",
        "*.pyc",
        ".env*",
    ])
    
    # Workspace for file operations
    workspace_dir: Optional[str] = None
    
    # Persistence - save run history
    history_dir: str = ".autonomous_history"  # Directory for run history
    state_file: Optional[str] = None  # Path to save/resume run state
    
    # Headless mode (for CI/automation)
    headless: bool = False  # Run without interactive prompts
    
    # Callbacks
    verbose: bool = True
    
    def get_target_path(self) -> Path:
        """Get resolved target repository path."""
        return Path(self.target_repo).resolve()
    
    def get_target_dir_path(self) -> Path:
        """Get resolved target directory path (scoped)."""
        base = self.get_target_path()
        return (base / self.target_dir).resolve()
    
    def get_workspace_path(self) -> Path:
        """Get workspace directory, defaulting to target dir path."""
        if self.workspace_dir:
            return Path(self.workspace_dir).resolve()
        return self.get_target_dir_path()
    
    def get_history_path(self) -> Path:
        """Get history directory path."""
        return self.get_target_path() / self.history_dir

    
    def ensure_history_dir(self) -> Path:
        """Ensure history directory exists and return path."""
        path = self.get_history_path()
        path.mkdir(parents=True, exist_ok=True)
        return path

