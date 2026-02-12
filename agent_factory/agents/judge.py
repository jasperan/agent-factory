import time
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


# The main prompt that drives the Judge's verification
JUDGE_SYSTEM_PROMPT = """You are a senior code reviewer and quality assurance expert. Your role is to verify that code implementations meet their acceptance criteria.

When reviewing implementations:
1. Check EACH acceptance criterion explicitly
2. Verify the code actually implements what was requested
3. Look for bugs, edge cases, and potential issues
4. Check code quality and best practices
5. Be strict but fair - don't fail implementations for minor style issues

Your verdict must be:
- PASS: All acceptance criteria are met and code works correctly
- FAIL: One or more criteria not met, or significant issues found
- NEEDS_ITERATION: Minor issues that Worker should fix

Always provide specific, actionable feedback the Worker can use to improve."""


JUDGE_VERIFICATION_PROMPT = """Verify this implementation meets the acceptance criteria:

## Original Task
**Title:** {title}
**Description:** {description}

## Acceptance Criteria
{acceptance_criteria}

## Implementation Result
{implementation_logs}

## Current File States
{file_contents}

## Your Task
1. Check each acceptance criterion - is it satisfied?
2. Review the code quality
3. Identify any bugs or issues
4. Provide a verdict

Output your verdict as JSON:
{{
  "verdict": "PASS" or "FAIL" or "NEEDS_ITERATION",
  "score": 0.0-1.0,
  "criteria_results": [
    {{"criterion": "...", "met": true/false, "notes": "..."}}
  ],
  "issues": ["list of issues found"],
  "feedback": "Detailed feedback for the Worker",
  "suggested_fixes": ["Specific fixes if verdict is FAIL/NEEDS_ITERATION"]
}}"""


class JudgeAgent:
    """
    Judge Agent - Verifies implementations meet acceptance criteria via LLM.
    
    The Judge's job is to:
    1. Receive the completed task and implementation result
    2. Read the current state of affected files
    3. Verify each acceptance criterion is met
    4. Provide structured feedback
    5. Determine if the task passes or needs iteration
    """
    
    def __init__(
        self,
        agent_name: str = "judge",
        model: str = "qwen2.5-coder:latest",
        workspace_dir: Optional[str] = None,
        ollama_base_url: str = "http://localhost:11434",
        num_ctx: int = 32768,
    ):
        self.agent_name = agent_name
        self.model = model
        self.workspace_dir = Path(workspace_dir).resolve() if workspace_dir else Path.cwd()
        self.ollama_base_url = ollama_base_url
        self.num_ctx = num_ctx
        
        self._llm = None
    
    @property
    def agent_id(self) -> str:
        return f"judge-{self.agent_name}"
    
    def _get_llm(self):
        """Lazy-load LLM client."""
        if self._llm is None:
            try:
                import litellm
                litellm.set_verbose = False
                self._llm = litellm
            except ImportError:
                raise ImportError("litellm not installed")
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
    
    def _read_file_contents(self, files: List[str]) -> str:
        """Read contents of affected files."""
        contents = []
        for file_path in files:
            full_path = self.workspace_dir / file_path
            try:
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8')
                    if len(content) > 4000:
                        content = content[:4000] + "\n... (truncated)"
                    contents.append(f"### {file_path}\n```\n{content}\n```")
                else:
                    contents.append(f"### {file_path}\n(File does not exist)")
            except Exception as e:
                contents.append(f"### {file_path}\n(Error reading: {e})")
        
        return "\n\n".join(contents) if contents else "(No files to review)"
    
    def verify_task(
        self,
        task: Dict[str, Any],
        implementation_logs: str = ""
    ) -> Dict[str, Any]:
        """
        Verify a completed task meets its acceptance criteria.
        
        This is the Judge's main job - evaluate if the Worker's implementation is correct.
        
        Args:
            task: Dictionary with title, description, affected_files, acceptance_criteria
            implementation_logs: Logs from Worker's implementation
            
        Returns:
            Verdict dict with verdict, score, criteria_results, issues, feedback, suggested_fixes
        """
        title = task.get("title", "Unknown task")
        description = task.get("description", "")
        affected_files = task.get("affected_files", [])
        acceptance_criteria = task.get("acceptance_criteria", [])
        
        logger.info(f"Judge verifying: {title}")
        
        # Read current file states
        file_contents = self._read_file_contents(affected_files)
        
        # Build verification prompt
        prompt = JUDGE_VERIFICATION_PROMPT.format(
            title=title,
            description=description,
            acceptance_criteria="\n".join(f"- {c}" for c in acceptance_criteria) if acceptance_criteria else "- Task completed successfully",
            implementation_logs=implementation_logs[:3000] if implementation_logs else "(No implementation logs)",
            file_contents=file_contents,
        )
        
        try:
            response = self._call_llm(prompt, JUDGE_SYSTEM_PROMPT)
            
            # Parse JSON from response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            verdict_data = json.loads(response.strip())
            
            return {
                "verdict": verdict_data.get("verdict", "FAIL"),
                "score": float(verdict_data.get("score", 0.0)),
                "criteria_results": verdict_data.get("criteria_results", []),
                "issues": verdict_data.get("issues", []),
                "feedback": verdict_data.get("feedback", ""),
                "suggested_fixes": verdict_data.get("suggested_fixes", []),
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Judge response: {e}")
            return {
                "verdict": "FAIL",
                "score": 0.0,
                "feedback": f"Could not parse verification response: {e}",
                "issues": ["Response parsing failed"],
                "suggested_fixes": [],
            }
        except Exception as e:
            logger.error(f"Judge verification failed: {e}")
            return {
                "verdict": "FAIL",
                "score": 0.0,
                "feedback": f"Verification error: {e}",
                "issues": [str(e)],
                "suggested_fixes": [],
            }
    
    def should_iterate(self, verdict: Dict[str, Any]) -> bool:
        """Determine if the Worker should iterate based on verdict."""
        return verdict["verdict"] in ("FAIL", "NEEDS_ITERATION")
