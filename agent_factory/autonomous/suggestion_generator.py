"""
Suggestion Generator - LLM-powered code analysis and improvement suggestion generation.

Uses decomposed reasoning strategy from agent-reasoning to break down
complex improvement opportunities into actionable suggestions.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Generator
from fnmatch import fnmatch

from .models import Suggestion, SuggestionCategory
from .config import AutonomousConfig

logger = logging.getLogger(__name__)


# Default fallback suggestions when LLM fails or returns empty
FALLBACK_SUGGESTIONS = [
    {
        "title": "Add/Improve Module Documentation",
        "description": "Add comprehensive module-level docstrings explaining the purpose, usage, and key components of each file.",
        "priority": 6,
        "category": "documentation",
        "acceptance_criteria": [
            "All Python files have module-level docstrings",
            "Docstrings explain the purpose and main components",
            "Usage examples are included where appropriate"
        ],
        "reasoning": "Good documentation helps maintainability and onboarding."
    },
    {
        "title": "Add Type Hints",
        "description": "Add complete type hints to all function parameters and return values to improve code clarity and enable static type checking.",
        "priority": 5,
        "category": "maintainability",
        "acceptance_criteria": [
            "All functions have type hints for parameters",
            "All functions have return type annotations",
            "Complex types use typing module appropriately"
        ],
        "reasoning": "Type hints improve code readability and catch bugs early."
    },
    {
        "title": "Add Unit Tests",
        "description": "Create comprehensive unit tests for the main functions and classes to ensure correctness and prevent regressions.",
        "priority": 7,
        "category": "testing",
        "acceptance_criteria": [
            "Test file created for each module",
            "All public functions have at least one test case",
            "Edge cases are covered"
        ],
        "reasoning": "Unit tests ensure code quality and enable safe refactoring."
    },
]


# Analysis prompts for different improvement categories
ANALYSIS_PROMPTS = {
    "maintainability": """Analyze the following code for maintainability improvements.
Look for:
- Functions that are too long (>50 lines)
- Missing or inadequate docstrings
- Complex nested conditionals
- Magic numbers or hardcoded values
- Code duplication
- Poor naming conventions

For each issue found, suggest a specific, actionable improvement.""",

    "documentation": """Analyze the following code for documentation improvements.
Look for:
- Missing module-level docstrings
- Functions/methods without docstrings
- Complex logic without explanatory comments
- Missing type hints
- Outdated or incorrect comments
- Missing README sections

For each issue found, suggest a specific, actionable improvement.""",

    "error_handling": """Analyze the following code for error handling improvements.
Look for:
- Bare except clauses
- Missing error handling for I/O operations
- Unvalidated user inputs
- Missing null/None checks
- Unclosed resources (files, connections)
- Silent failures

For each issue found, suggest a specific, actionable improvement.""",

    "performance": """Analyze the following code for performance improvements.
Look for:
- Inefficient loops (could use list comprehensions)
- Repeated expensive operations
- N+1 query patterns
- Missing caching opportunities
- Large data structures copied unnecessarily
- Blocking operations that could be async

For each issue found, suggest a specific, actionable improvement.""",

    "security": """Analyze the following code for security improvements.
Look for:
- SQL injection vulnerabilities
- Hardcoded secrets or credentials
- Missing input validation
- Insecure file operations
- Missing authentication checks
- Exposed sensitive data in logs

For each issue found, suggest a specific, actionable improvement.""",

    "testing": """Analyze the following code for testing improvements.
Look for:
- Functions without test coverage
- Edge cases not tested
- Missing error case tests
- Tightly coupled code difficult to test
- Missing mocks for external dependencies

For each issue found, suggest a specific, actionable improvement.""",
}


class SuggestionGenerator:
    """
    Generates code improvement suggestions using LLM analysis.
    
    Uses the decomposed reasoning strategy to:
    1. Scan codebase structure
    2. Analyze files for improvement opportunities
    3. Generate prioritized, actionable suggestions
    """

    def __init__(self, config: AutonomousConfig):
        """
        Initialize the suggestion generator.
        
        Args:
            config: Autonomous configuration with model and analysis settings
        """
        self.config = config
        self._llm = None
    
    def _get_llm(self):
        """Lazy-load LLM client with Ollama."""
        if self._llm is None:
            try:
                import litellm
                litellm.set_verbose = False
                self._llm = litellm
            except ImportError:
                raise ImportError("litellm not installed. Run: pip install litellm")
        return self._llm
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Call LLM with the given prompt."""
        llm = self._get_llm()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = llm.completion(
            model=f"ollama/{self.config.model}",
            messages=messages,
            api_base=self.config.ollama_base_url,
            num_ctx=self.config.num_ctx,
        )
        
        return response.choices[0].message.content
    
    def scan_codebase(self) -> List[str]:
        """
        Scan the target repository for files to analyze, scoped to target_dir.
        
        Returns:
            List of file paths relative to target repo
        """
        repo_root = self.config.get_target_path()
        target_dir = self.config.get_target_dir_path()
        files = []
        
        # Ensure target_dir exists
        if not target_dir.exists():
            logger.warning(f"Target directory {target_dir} does not exist")
            return []
            
        # Use extension-based search
        extensions = ['.py', '.ts', '.js', '.tsx', '.jsx']
        
        for ext in extensions:
            for path in target_dir.rglob(f'*{ext}'):
                if path.is_file():
                    rel_path = str(path.relative_to(repo_root))
                    
                    # Check exclusions
                    excluded = False
                    for exclude in self.config.exclude_patterns:
                        if exclude.rstrip('/*') in rel_path:
                            excluded = True
                            break
                    
                    if not excluded:
                        files.append(rel_path)
        
        return sorted(set(files))
    
    def _get_generic_improvements_for_codebase(self, files: List[str]) -> List[dict]:
        """Generate fallback generic improvements if LLM fails."""
        improvements = []
        for suggestion in FALLBACK_SUGGESTIONS:
            s = suggestion.copy()
            s["affected_files"] = files[:3] if files else ["."]  # Affect first 3 files
            improvements.append(s)
        return improvements
    
    def analyze_file(self, file_path: str, analysis_type: str) -> List[dict]:
        """
        Analyze a single file for improvements.
        
        Args:
            file_path: Relative path to file (relative to repo root)
            analysis_type: Type of analysis to perform
            
        Returns:
            List of improvement opportunities found
        """
        repo_root = self.config.get_target_path()
        full_path = repo_root / file_path
        
        if not full_path.exists():
            return []

        
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return []
        
        # Skip very large files
        if len(content) > 50000:
            logger.info(f"Skipping large file: {file_path}")
            return []
        
        # Get analysis prompt
        analysis_prompt = ANALYSIS_PROMPTS.get(analysis_type, ANALYSIS_PROMPTS["maintainability"])
        
        system_prompt = """You are an expert code reviewer. Analyze the provided code and output improvement suggestions in JSON format.

Output format (JSON array):
[
  {
    "title": "Short title",
    "description": "Detailed description of the improvement",
    "priority": 1-10,
    "acceptance_criteria": ["Criterion 1", "Criterion 2"],
    "reasoning": "Why this improvement matters"
  }
]

Only output valid JSON, no other text."""

        prompt = f"""{analysis_prompt}

File: {file_path}

```
{content[:20000]}
```

IMPORTANT: You MUST provide at least 1 improvement suggestion. Even if the code looks good, suggest documentation improvements, type hints, or potential edge cases. Never return an empty array.

Provide your analysis as a JSON array of improvements."""

        try:
            response = self._call_llm(prompt, system_prompt)
            
            # Parse JSON from response
            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            improvements = json.loads(response.strip())
            
            # Add file path to each improvement
            for imp in improvements:
                imp["affected_files"] = [file_path]
                imp["category"] = analysis_type
            
            return improvements
            
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse LLM response for {file_path}: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            return []
    
    def generate_suggestions(
        self,
        max_suggestions: Optional[int] = None,
        on_file_analyzed: Optional[callable] = None
    ) -> Generator[Suggestion, None, None]:
        """
        Generate improvement suggestions for the codebase.
        
        Args:
            max_suggestions: Maximum number of suggestions to generate
            on_file_analyzed: Callback(file_path, suggestions_count) for progress
            
        Yields:
            Suggestion objects
        """
        max_suggestions = max_suggestions or self.config.max_suggestions
        files = self.scan_codebase()
        
        # Debug output
        target_dir = self.config.get_target_dir_path()
        print(f"[DEBUG] Scanning directory: {target_dir}")
        print(f"[DEBUG] Found {len(files)} files: {files[:10]}{'...' if len(files) > 10 else ''}")
        
        if self.config.verbose:
            logger.info(f"Scanning {len(files)} files for improvements...")
        
        all_improvements = []
        
        # If no files found, use fallback immediately
        if not files:
            print("[DEBUG] No files found in target directory, using fallback suggestions")
            all_improvements = self._get_generic_improvements_for_codebase([])
        else:
            # Analyze files
            for file_path in files:
                for analysis_type in self.config.analysis_types:
                    print(f"[DEBUG] Analyzing {file_path} for {analysis_type}...")
                    improvements = self.analyze_file(file_path, analysis_type)
                    print(f"[DEBUG] Found {len(improvements)} improvements")
                    all_improvements.extend(improvements)
                    
                    if on_file_analyzed:
                        on_file_analyzed(file_path, len(improvements))
                    
                    # Early exit if we have enough
                    if len(all_improvements) >= max_suggestions * 2:
                        break
                
                if len(all_improvements) >= max_suggestions * 2:
                    break
        
        # If still no improvements after analysis, use fallback
        if not all_improvements:
            print("[DEBUG] LLM returned no improvements, using fallback suggestions")
            all_improvements = self._get_generic_improvements_for_codebase(files)
        
        # Sort by priority (descending) and take top N
        all_improvements.sort(key=lambda x: x.get("priority", 5), reverse=True)
        top_improvements = all_improvements[:max_suggestions]
        
        print(f"[DEBUG] Returning {len(top_improvements)} suggestions")
        
        # Convert to Suggestion objects
        for imp in top_improvements:
            try:
                category = SuggestionCategory(imp.get("category", "refactoring"))
            except ValueError:
                category = SuggestionCategory.REFACTORING
            
            suggestion = Suggestion(
                title=imp.get("title", "Untitled improvement"),
                description=imp.get("description", ""),
                category=category,
                priority=imp.get("priority", 5),
                affected_files=imp.get("affected_files", []),
                acceptance_criteria=imp.get("acceptance_criteria", []),
                reasoning=imp.get("reasoning", ""),
            )
            yield suggestion
    
    def generate_suggestions_list(
        self,
        max_suggestions: Optional[int] = None
    ) -> List[Suggestion]:
        """
        Generate suggestions and return as a list.
        
        Args:
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of Suggestion objects
        """
        return list(self.generate_suggestions(max_suggestions))
