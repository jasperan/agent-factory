"""
Autonomous Runner - Main orchestration for Planner → Worker → Judge loop.

Manages the complete autonomous code improvement cycle:
1. Planner generates suggestions via SuggestionGenerator
2. Worker implements suggestions via OpenHands SDK
3. Judge verifies implementations and provides feedback
4. Loop until success or max iterations reached
"""

import time
import logging
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any

from .models import (
    Suggestion,
    SuggestionStatus,
    Verdict,
    VerdictStatus,
    AutonomousRun,
    RunStatus,
)
from .config import AutonomousConfig
from .suggestion_generator import SuggestionGenerator

logger = logging.getLogger(__name__)


class AutonomousRunner:
    """
    Orchestrates the autonomous code improvement pipeline.
    
    Pipeline:
        PLANNER (SuggestionGenerator) → Generate suggestions
        WORKER (OpenHandsWorker) → Implement changes
        JUDGE (LLM Verification) → Verify and provide feedback
        
    The runner manages:
    - Suggestion queue and status
    - Worker-Judge iteration loop
    - Progress callbacks for CLI integration
    - Run state persistence
    """

    def __init__(
        self,
        config: AutonomousConfig,
        on_suggestion: Optional[Callable[[Suggestion], None]] = None,
        on_implementation: Optional[Callable[[Suggestion, str], None]] = None,
        on_verdict: Optional[Callable[[Verdict], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the autonomous runner.
        
        Args:
            config: Autonomous configuration
            on_suggestion: Callback when new suggestion is generated
            on_implementation: Callback when implementation completes (suggestion, logs)
            on_verdict: Callback when judge provides verdict
            on_status_change: Callback when run status changes
        """
        self.config = config
        self.on_suggestion = on_suggestion
        self.on_implementation = on_implementation
        self.on_verdict = on_verdict
        self.on_status_change = on_status_change
        
        # Initialize components
        self.generator = SuggestionGenerator(config)
        self._worker = None  # Lazy loaded
        self._llm = None     # Lazy loaded for judge
        
        # Current run state
        self.current_run: Optional[AutonomousRun] = None
    
    def _get_worker(self):
        """Lazy-load OpenHands worker."""
        if self._worker is None:
            from ..workers.openhands_worker import OpenHandsWorker
            
            self._worker = OpenHandsWorker(
                model=self.config.model,
                workspace_dir=self.config.get_workspace_path(),
                use_ollama=True,
                ollama_base_url=self.config.ollama_base_url,
                verbose=self.config.verbose,
            )
        return self._worker
    
    def _get_llm(self):
        """Lazy-load LLM for judge."""
        if self._llm is None:
            import litellm
            litellm.set_verbose = False
            self._llm = litellm
        return self._llm
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Call LLM for judge reasoning."""
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
    
    def _emit_status(self, status: str):
        """Emit status change callback."""
        if self.on_status_change:
            self.on_status_change(status)
        if self.config.verbose:
            logger.info(f"[Runner] {status}")
    
    def generate_suggestions(self) -> List[Suggestion]:
        """
        Generate improvement suggestions for the target codebase.
        
        Returns:
            List of generated suggestions
        """
        self._emit_status("Generating suggestions...")
        
        suggestions = self.generator.generate_suggestions_list(
            max_suggestions=self.config.max_suggestions
        )
        
        for suggestion in suggestions:
            if self.on_suggestion:
                self.on_suggestion(suggestion)
        
        self._emit_status(f"Generated {len(suggestions)} suggestions")
        return suggestions
    
    def implement_suggestion(self, suggestion: Suggestion) -> str:
        """
        Have the worker implement a suggestion using OpenHands.
        
        Args:
            suggestion: The suggestion to implement
            
        Returns:
            Implementation logs
        """
        self._emit_status(f"Implementing: {suggestion.title}")
        suggestion.status = SuggestionStatus.IN_PROGRESS
        
        worker = self._get_worker()
        
        # Get workspace path for context
        workspace = self.config.get_workspace_path()
        
        # Build detailed implementation prompt with explicit file editing instructions
        files_list = '\n'.join(f'  - {f}' for f in suggestion.affected_files)
        criteria_list = '\n'.join(f'  - {c}' for c in suggestion.acceptance_criteria)
        
        task_prompt = f"""You are a code improvement agent. Implement the following improvement.

## Task: {suggestion.title}

## Description
{suggestion.description}

## Files to Modify
{files_list}

## Acceptance Criteria
{criteria_list}

## Workspace
Working directory: {workspace}

## Instructions
1. Read the existing files first to understand the current code
2. Make the necessary modifications using the file_editor tool
3. Ensure all acceptance criteria are met
4. Verify the changes are saved correctly

IMPORTANT: You MUST use the file_editor tool to actually modify the files. Do not just describe the changes - implement them."""

        # Execute via OpenHands
        result = worker.run_task(task_prompt, timeout=300)
        
        logs = result.logs if result.success else f"Error: {result.message}\n{result.logs}"
        
        # Log files changed
        if result.files_changed:
            self._emit_status(f"Modified {len(result.files_changed)} files: {result.files_changed}")
        
        if self.on_implementation:
            self.on_implementation(suggestion, logs)
        
        return logs
    
    def judge_implementation(
        self,
        suggestion: Suggestion,
        implementation_logs: str
    ) -> Verdict:
        """
        Have the judge verify the implementation.
        
        Args:
            suggestion: The implemented suggestion
            implementation_logs: Logs from worker implementation
            
        Returns:
            Judge's verdict
        """
        self._emit_status(f"Verifying: {suggestion.title}")
        
        # Read current state of affected files
        files_content = {}
        target = self.config.get_target_path()
        for file_path in suggestion.affected_files:
            full_path = target / file_path
            if full_path.exists():
                try:
                    files_content[file_path] = full_path.read_text()[:10000]
                except Exception:
                    files_content[file_path] = "[Could not read file]"
        
        system_prompt = """You are a code review judge. Evaluate if an implementation meets the acceptance criteria.

Output your verdict as JSON:
{
  "status": "pass" or "fail",
  "score": 0.0-1.0,
  "feedback": "Detailed feedback",
  "criteria_met": ["list of criteria that passed"],
  "criteria_failed": ["list of criteria that failed"],
  "suggested_fixes": ["specific fixes if status is fail"]
}

Only output valid JSON."""

        prompt = f"""Evaluate this implementation:

## Suggestion
Title: {suggestion.title}
Description: {suggestion.description}

## Acceptance Criteria
{chr(10).join(f'- {c}' for c in suggestion.acceptance_criteria)}

## Implementation Logs
```
{implementation_logs[:5000]}
```

## Current File States
{chr(10).join(f'### {path}{chr(10)}```{chr(10)}{content}{chr(10)}```' for path, content in files_content.items())}

Provide your verdict as JSON."""

        try:
            import json
            response = self._call_llm(prompt, system_prompt)
            
            # Parse JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            verdict_data = json.loads(response.strip())
            
            verdict = Verdict(
                suggestion_id=suggestion.id,
                status=VerdictStatus(verdict_data.get("status", "fail")),
                score=float(verdict_data.get("score", 0.0)),
                feedback=verdict_data.get("feedback", ""),
                criteria_met=verdict_data.get("criteria_met", []),
                criteria_failed=verdict_data.get("criteria_failed", []),
                suggested_fixes=verdict_data.get("suggested_fixes", []),
            )
            
        except Exception as e:
            logger.warning(f"Could not parse judge response: {e}")
            verdict = Verdict(
                suggestion_id=suggestion.id,
                status=VerdictStatus.NEEDS_REVIEW,
                feedback=f"Could not parse verdict: {e}",
            )
        
        if self.on_verdict:
            self.on_verdict(verdict)
        
        return verdict
    
    def run_suggestion(self, suggestion: Suggestion) -> bool:
        """
        Run the complete Worker → Judge loop for a single suggestion.
        
        Args:
            suggestion: The suggestion to implement
            
        Returns:
            True if implementation succeeded, False otherwise
        """
        for iteration in range(self.config.max_iterations):
            suggestion.iterations = iteration + 1
            
            # Worker implements
            logs = self.implement_suggestion(suggestion)
            
            # Judge verifies
            verdict = self.judge_implementation(suggestion, logs)
            
            if verdict.status == VerdictStatus.PASS:
                suggestion.status = SuggestionStatus.COMPLETED
                suggestion.implementation_notes = f"Completed after {iteration + 1} iteration(s)"
                return True
            
            if iteration < self.config.max_iterations - 1:
                self._emit_status(f"Iteration {iteration + 1} failed, retrying with feedback...")
                # Add judge feedback to next iteration context
                suggestion.implementation_notes = f"Previous attempt feedback: {verdict.feedback}"
        
        # Max iterations reached
        suggestion.status = SuggestionStatus.FAILED
        suggestion.implementation_notes = f"Failed after {self.config.max_iterations} iterations"
        return False
    
    def create_run(self, suggestions: List[Suggestion]) -> AutonomousRun:
        """
        Create a new autonomous run with the given suggestions.
        
        Args:
            suggestions: List of suggestions to process
            
        Returns:
            New AutonomousRun instance
        """
        run = AutonomousRun(
            target_repo=str(self.config.get_target_path()),
            suggestions=suggestions,
            total_suggestions=len(suggestions),
            model=self.config.model,
            max_iterations=self.config.max_iterations,
        )
        self.current_run = run
        return run
    
    def run_all(self, accepted_suggestions: List[Suggestion]) -> AutonomousRun:
        """
        Run the complete pipeline for all accepted suggestions.
        
        Args:
            accepted_suggestions: Suggestions that have been accepted for implementation
            
        Returns:
            Completed AutonomousRun with results
        """
        run = self.create_run(accepted_suggestions)
        run.status = RunStatus.RUNNING
        run.started_at = datetime.utcnow()
        
        for suggestion in accepted_suggestions:
            suggestion.status = SuggestionStatus.ACCEPTED
        
        run.accepted_count = len(accepted_suggestions)
        
        self._emit_status(f"Starting autonomous run with {len(accepted_suggestions)} suggestions")
        
        for i, suggestion in enumerate(accepted_suggestions):
            self._emit_status(f"Processing suggestion {i + 1}/{len(accepted_suggestions)}")
            
            success = self.run_suggestion(suggestion)
            
            if success:
                run.completed_count += 1
            else:
                run.failed_count += 1
        
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.utcnow()
        
        self._emit_status(
            f"Run completed: {run.completed_count} succeeded, {run.failed_count} failed"
        )
        
        return run
    
    def run_single(self) -> Optional[Suggestion]:
        """
        Generate one suggestion and run it (for testing).
        
        Returns:
            The processed suggestion, or None if no suggestions generated
        """
        suggestions = self.generate_suggestions()
        
        if not suggestions:
            self._emit_status("No suggestions generated")
            return None
        
        suggestion = suggestions[0]
        suggestion.status = SuggestionStatus.ACCEPTED
        
        self.run_suggestion(suggestion)
        
        return suggestion
    
    # ========== PERSISTENCE METHODS ==========
    
    def save_run(self, run: Optional[AutonomousRun] = None) -> Path:
        """
        Save run state to history directory.
        
        Args:
            run: Run to save (defaults to current_run)
            
        Returns:
            Path to saved file
        """
        run = run or self.current_run
        if not run:
            raise ValueError("No run to save")
        
        history_dir = self.config.ensure_history_dir()
        filename = f"run_{run.id}_{run.started_at.strftime('%Y%m%d_%H%M%S') if run.started_at else 'pending'}.json"
        filepath = history_dir / filename
        
        # Convert to dict for JSON serialization
        run_dict = run.model_dump()
        run_dict['started_at'] = run_dict['started_at'].isoformat() if run_dict['started_at'] else None
        run_dict['completed_at'] = run_dict['completed_at'].isoformat() if run_dict['completed_at'] else None
        
        # Handle suggestion dates
        for s in run_dict['suggestions']:
            if s['created_at']:
                s['created_at'] = s['created_at'].isoformat()
        
        filepath.write_text(json.dumps(run_dict, indent=2, default=str))
        self._emit_status(f"Saved run to {filepath}")
        return filepath
    
    def load_run(self, run_id: str) -> Optional[AutonomousRun]:
        """
        Load a run from history by ID.
        
        Args:
            run_id: The run ID to load
            
        Returns:
            Loaded AutonomousRun or None if not found
        """
        history_dir = self.config.get_history_path()
        if not history_dir.exists():
            return None
        
        for filepath in history_dir.glob(f"run_{run_id}_*.json"):
            try:
                data = json.loads(filepath.read_text())
                # Parse dates back
                if data.get('started_at'):
                    data['started_at'] = datetime.fromisoformat(data['started_at'])
                if data.get('completed_at'):
                    data['completed_at'] = datetime.fromisoformat(data['completed_at'])
                for s in data.get('suggestions', []):
                    if s.get('created_at'):
                        s['created_at'] = datetime.fromisoformat(s['created_at'])
                
                run = AutonomousRun(**data)
                self.current_run = run
                return run
            except Exception as e:
                logger.warning(f"Failed to load run {filepath}: {e}")
        
        return None
    
    def list_runs(self) -> List[Dict[str, Any]]:
        """
        List all saved runs.
        
        Returns:
            List of run summaries (id, status, date, suggestion counts)
        """
        history_dir = self.config.get_history_path()
        if not history_dir.exists():
            return []
        
        runs = []
        for filepath in sorted(history_dir.glob("run_*.json"), reverse=True):
            try:
                data = json.loads(filepath.read_text())
                runs.append({
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "target_repo": data.get("target_repo"),
                    "started_at": data.get("started_at"),
                    "total": data.get("total_suggestions", 0),
                    "completed": data.get("completed_count", 0),
                    "failed": data.get("failed_count", 0),
                    "filepath": str(filepath),
                })
            except Exception:
                continue
        
        return runs
    
    # ========== DIFF METHODS ==========
    
    def get_git_diff(self) -> str:
        """
        Get git diff of changes in target repository.
        
        Returns:
            Git diff output as string
        """
        target = self.config.get_target_path()
        try:
            result = subprocess.run(
                ["git", "diff", "--color=always"],
                cwd=target,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout or "(No changes detected)"
        except Exception as e:
            return f"(Could not get diff: {e})"
    
    def get_file_diff(self, file_path: str) -> str:
        """
        Get git diff for a specific file.
        
        Args:
            file_path: Path relative to target repo
            
        Returns:
            Git diff for the file
        """
        target = self.config.get_target_path()
        try:
            result = subprocess.run(
                ["git", "diff", "--color=always", file_path],
                cwd=target,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout or "(No changes to this file)"
        except Exception as e:
            return f"(Could not get diff: {e})"

