import time
import logging
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


# The main prompt that drives the Planner's suggestion generation
PLANNER_SYSTEM_PROMPT = """You are an expert code architect and senior software engineer. Your role is to analyze codebases and generate actionable improvement suggestions.

For each suggestion you create, it must be:
1. SPECIFIC - Target exact files with clear changes
2. ACTIONABLE - Describable in terms a developer can implement
3. VALUABLE - Improve code quality, performance, security, or maintainability
4. INDEPENDENT - Each suggestion should be implementable on its own

You should look for opportunities including:
- Missing error handling or edge cases
- Code that could be refactored for clarity
- Missing documentation or type hints  
- Performance optimizations
- Security improvements
- New utility functions that would reduce duplication
- Test coverage gaps
- Feature enhancements that would benefit the project

Output your suggestions as a JSON array."""


PLANNER_ANALYSIS_PROMPT = """Analyze this codebase and generate {max_suggestions} improvement suggestions.

## Repository Structure
{file_list}

## Sample File Contents
{sample_files}

## Your Task
Generate exactly {max_suggestions} improvement suggestions. For each suggestion, provide:
- title: Short descriptive title
- description: Detailed description of what to change and why
- affected_files: List of files to modify or create
- priority: 1-10 (10 = most important)
- acceptance_criteria: List of criteria to verify the change is complete
- reasoning: Why this improvement matters

Focus on HIGH-VALUE improvements that will genuinely help this project.

Output as JSON array:
[
  {{
    "title": "...",
    "description": "...",
    "affected_files": ["..."],
    "priority": 8,
    "acceptance_criteria": ["...", "..."],
    "reasoning": "..."
  }}
]"""


class PlannerAgent:
    """
    Planner Agent - Generates code improvement suggestions via LLM analysis.
    
    The Planner's job is to:
    1. Analyze the target codebase structure
    2. Read sample files to understand patterns
    3. Generate specific, actionable improvement suggestions
    4. Prioritize suggestions by impact
    """
    
    def __init__(
        self,
        agent_name: str = "planner",
        model: str = "qwen2.5-coder:latest",
        target_repo: str = ".",
        ollama_base_url: str = "http://localhost:11434",
        num_ctx: int = 32768,
    ):
        self.agent_name = agent_name
        self.model = model
        self.target_repo = Path(target_repo).resolve()
        self.ollama_base_url = ollama_base_url
        self.num_ctx = num_ctx
        self.planning_interval = 60
        
        self._llm = None
    
    @property
    def agent_id(self) -> str:
        return f"planner-{self.agent_name}"
    
    def _get_llm(self):
        """Lazy-load LLM client."""
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
            model=f"ollama/{self.model}",
            messages=messages,
            api_base=self.ollama_base_url,
            num_ctx=self.num_ctx,
        )
        
        return response.choices[0].message.content
    
    def _scan_files(self, max_files: int = 50) -> List[str]:
        """Scan repository for code files."""
        extensions = {'.py', '.ts', '.js', '.tsx', '.jsx', '.go', '.rs', '.java'}
        exclude_dirs = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'dist', 'build'}
        
        files = []
        for path in self.target_repo.rglob('*'):
            if path.is_file() and path.suffix in extensions:
                # Skip excluded directories
                if any(ex in path.parts for ex in exclude_dirs):
                    continue
                rel_path = str(path.relative_to(self.target_repo))
                files.append(rel_path)
                if len(files) >= max_files:
                    break
        
        return sorted(files)
    
    def _read_sample_files(self, files: List[str], max_chars: int = 15000) -> str:
        """Read sample file contents for analysis."""
        samples = []
        chars_used = 0
        
        # Prioritize important files
        priority_files = ['main.py', 'app.py', 'index.ts', 'index.js', '__init__.py', 'cli.py']
        sorted_files = sorted(files, key=lambda f: (
            0 if any(p in f for p in priority_files) else 1,
            f
        ))
        
        for file_path in sorted_files[:10]:  # Max 10 files
            full_path = self.target_repo / file_path
            try:
                content = full_path.read_text(encoding='utf-8')
                if len(content) > 3000:
                    content = content[:3000] + "\n... (truncated)"
                
                sample = f"### {file_path}\n```\n{content}\n```\n"
                if chars_used + len(sample) > max_chars:
                    break
                    
                samples.append(sample)
                chars_used += len(sample)
            except Exception:
                continue
        
        return "\n".join(samples)
    
    def generate_suggestions(self, max_count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate improvement suggestions by analyzing the codebase.
        
        This is the Planner's main job - analyze code and suggest improvements.
        
        Returns:
            List of suggestion dictionaries with title, description, affected_files,
            priority, acceptance_criteria, and reasoning.
        """
        logger.info(f"Planner analyzing {self.target_repo}...")
        
        # 1. Scan file structure
        files = self._scan_files()
        if not files:
            logger.warning("No code files found in repository")
            return []
        
        file_list = "\n".join(f"- {f}" for f in files)
        
        # 2. Read sample files
        sample_content = self._read_sample_files(files)
        
        # 3. Build analysis prompt
        prompt = PLANNER_ANALYSIS_PROMPT.format(
            max_suggestions=max_count,
            file_list=file_list,
            sample_files=sample_content
        )
        
        # 4. Call LLM
        logger.info(f"Planner calling LLM to generate {max_count} suggestions...")
        try:
            response = self._call_llm(prompt, PLANNER_SYSTEM_PROMPT)
            
            # Parse JSON from response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            suggestions = json.loads(response.strip())
            
            # Validate and clean suggestions
            valid_suggestions = []
            for s in suggestions[:max_count]:
                if isinstance(s, dict) and "title" in s:
                    valid_suggestions.append({
                        "title": s.get("title", "Untitled"),
                        "description": s.get("description", ""),
                        "affected_files": s.get("affected_files", []),
                        "priority": min(10, max(1, int(s.get("priority", 5)))),
                        "acceptance_criteria": s.get("acceptance_criteria", []),
                        "reasoning": s.get("reasoning", ""),
                    })
            
            logger.info(f"Planner generated {len(valid_suggestions)} valid suggestions")
            return valid_suggestions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []
        except Exception as e:
            logger.error(f"Planner LLM call failed: {e}")
            return []
