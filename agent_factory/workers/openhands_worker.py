"""
OpenHands Worker - AI Coding Agent Integration

PURPOSE:
    Integrates OpenHands autonomous coding agent into the factory.
    OpenHands can write code, run commands, browse web, edit files autonomously.

WHAT THIS DOES:
    - Uses OpenHands SDK for programmatic agent control
    - Configures agents with all available tools (Terminal, FileEditor, ApplyPatch, etc.)
    - Supports LiteLLM with Ollama for local model execution
    - Executes tasks within the Python process
    - Returns structured results

HOW IT WORKS:
    1. User calls: worker.run_task("Fix bug in file.py")
    2. Worker creates OpenHands SDK components (LLM, Agent, Conversation)
    3. Worker configures tools based on enabled options
    4. Task executed via Conversation.run()
    5. Result parsed and returned

INPUTS:
    - task: String describing what to code/fix
    - model: Which LLM to use (default: ollama/qwen2.5-coder)
    - timeout: Max seconds to wait (default: 300)
    - tools: List of tools to enable (default: terminal, file_editor)

OUTPUTS:
    - OpenHandsResult with: success (bool), message (str), logs (str), cost (float)

LITELLM OLLAMA INTEGRATION:
    - Use `ollama/model` for standard chat
    - Use `ollama_chat/model` for tool calling with supported models
    - Set `api_base` to Ollama server URL
    - Set `keep_alive` for persistent model loading
"""

import os
import time
import logging
import warnings
from typing import List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

# Suppress warnings and noisy logs
warnings.filterwarnings("ignore")
logging.getLogger("openhands").setLevel(logging.ERROR)
logging.getLogger("litellm").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

# Check SDK availability
try:
    import openhands.sdk
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


class ToolOption(str, Enum):
    """Available OpenHands tools."""
    TERMINAL = "terminal"
    FILE_EDITOR = "file_editor"
    APPLY_PATCH = "apply_patch"
    TASK_TRACKER = "task_tracker"
    # Browser and Delegate require additional dependencies
    BROWSER = "browser"
    DELEGATE = "delegate"


# Default tools for most tasks
DEFAULT_TOOLS: Set[ToolOption] = {
    ToolOption.TERMINAL,
    ToolOption.FILE_EDITOR,
    ToolOption.APPLY_PATCH,
}

# All available tools
ALL_TOOLS: Set[ToolOption] = set(ToolOption)

# Models known to support function/tool calling via Ollama
TOOL_CALLING_MODELS = {
    "llama3.1",
    "llama3.2", 
    "qwen2.5",
    "qwen2.5-coder",
    "qwen3",
    "qwen3-coder",
    "mistral",
    "mixtral",
    "deepseek-coder",
    "deepseek-coder-v2",
    "codellama",
    "codegemma",
}


@dataclass
class OpenHandsResult:
    """Result from an OpenHands coding task."""
    success: bool
    message: str
    code: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    cost: float = 0.0
    logs: str = ""
    token_usage: Optional[dict] = None


class OpenHandsWorker:
    """
    OpenHands AI Coding Agent Worker (SDK Version)
    
    Integrates with OpenHands SDK to provide autonomous coding capabilities
    using local Ollama models or cloud providers via LiteLLM.
    
    Features:
        - All SDK tools: Terminal, FileEditor, ApplyPatch, TaskTracker
        - LiteLLM Ollama integration with tool calling support
        - Configurable tool selection
        - Workspace management
        - Token usage and cost tracking
    """

    def __init__(
        self,
        model: str = "qwen2.5-coder:latest",
        workspace_dir: Optional[Path] = None,
        use_ollama: bool = None,
        ollama_base_url: str = None,
        verbose: bool = None,
        enabled_tools: Optional[Set[ToolOption]] = None,
        enable_tool_calling: bool = True,
        keep_alive: str = "5m",
        **kwargs
    ):
        """
        Initialize OpenHands worker.
        
        Args:
            model: Model name (e.g., "qwen2.5-coder:latest" for Ollama)
            workspace_dir: Directory where agent will work
            use_ollama: Whether to use local Ollama (auto-detected from env if None)
            ollama_base_url: Ollama API URL (default: http://localhost:11434)
            verbose: Whether to print debug information
            enabled_tools: Set of tools to enable (default: terminal, file_editor, apply_patch)
            enable_tool_calling: Use native tool calling for supported models
            keep_alive: How long Ollama keeps model loaded (default: 5m, use -1 for forever)
        """
        if not SDK_AVAILABLE:
            raise ImportError(
                "OpenHands SDK not found. Please install: pip install openhands-sdk openhands-tools"
            )

        # Auto-detect Ollama from environment
        if use_ollama is None:
            use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"

        if ollama_base_url is None:
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        if verbose is None:
            verbose = os.getenv("VERBOSE", "true").lower() == "true"

        # Store original model name for capability checking
        self._original_model = model.replace("ollama/", "").replace("ollama_chat/", "").split(":")[0]
        
        # Determine if model supports tool calling
        self._supports_tool_calling = any(
            tc_model in self._original_model.lower() 
            for tc_model in TOOL_CALLING_MODELS
        )
        
        # Configure model prefix for LiteLLM
        if use_ollama:
            # Strip any existing prefixes
            clean_model = model.replace("ollama/", "").replace("ollama_chat/", "")
            
            # Use ollama_chat/ for tool calling if supported and enabled
            if enable_tool_calling and self._supports_tool_calling:
                model = f"ollama_chat/{clean_model}"
            else:
                model = f"ollama/{clean_model}"

        self.model = model
        self.use_ollama = use_ollama
        self.ollama_base_url = ollama_base_url
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd() / "tests"
        self.verbose = verbose
        self.enabled_tools = enabled_tools or DEFAULT_TOOLS
        self.enable_tool_calling = enable_tool_calling
        self.keep_alive = keep_alive
        
        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        if self.verbose:
            print(f"[OpenHands] Model: {self.model}")
            print(f"[OpenHands] Tool Calling: {self._supports_tool_calling and enable_tool_calling}")
            print(f"[OpenHands] Enabled Tools: {[t.value for t in self.enabled_tools]}")

    def _build_tools(self) -> list:
        """Build list of Tool objects based on enabled options."""
        from openhands.sdk import Tool
        
        tools = []
        
        # Core tools (always available)
        if ToolOption.TERMINAL in self.enabled_tools:
            from openhands.tools.terminal import TerminalTool
            tools.append(Tool(name=TerminalTool.name))
            
        if ToolOption.FILE_EDITOR in self.enabled_tools:
            from openhands.tools.file_editor import FileEditorTool
            tools.append(Tool(name=FileEditorTool.name))
            
        if ToolOption.APPLY_PATCH in self.enabled_tools:
            try:
                from openhands.tools.apply_patch import ApplyPatchTool
                tools.append(Tool(name=ApplyPatchTool.name))
            except ImportError:
                if self.verbose:
                    print("[OpenHands] ApplyPatch tool not available")
                    
        if ToolOption.TASK_TRACKER in self.enabled_tools:
            try:
                from openhands.tools.task_tracker import TaskTrackerTool
                tools.append(Tool(name=TaskTrackerTool.name))
            except ImportError:
                if self.verbose:
                    print("[OpenHands] TaskTracker tool not available")
        
        # Optional tools (may require additional dependencies)
        if ToolOption.BROWSER in self.enabled_tools:
            try:
                from openhands.tools.browser_use import BrowserUseTool
                tools.append(Tool(name=BrowserUseTool.name))
            except ImportError:
                if self.verbose:
                    print("[OpenHands] BrowserUse tool not available (requires playwright)")
                    
        if ToolOption.DELEGATE in self.enabled_tools:
            try:
                from openhands.tools.delegate import DelegateTool
                tools.append(Tool(name=DelegateTool.name))
            except ImportError:
                if self.verbose:
                    print("[OpenHands] Delegate tool not available")
        
        return tools

    def run_task(
        self,
        task: str,
        timeout: int = 300,
        on_log: Optional[Any] = None
    ) -> OpenHandsResult:
        """
        Run a coding task using OpenHands SDK.
        
        Args:
            task: Task description for the agent
            timeout: Maximum execution time in seconds
            on_log: Optional callback for log events
            
        Returns:
            OpenHandsResult with execution details
        """
        start_time = time.time()

        if not task or not task.strip():
            return OpenHandsResult(
                success=False,
                message="Task cannot be empty",
                execution_time=time.time() - start_time
            )

        try:
            return self._run_sdk_task(task, timeout, on_log=on_log)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return OpenHandsResult(
                success=False,
                message=f"SDK Error: {str(e)}",
                logs=error_details,
                execution_time=time.time() - start_time
            )

    def _run_sdk_task(self, task: str, timeout: int, on_log=None) -> OpenHandsResult:
        """Internal method to run task using the SDK."""
        from openhands.sdk import Agent, LLM, Conversation
        from openhands.sdk.context.condenser import LLMSummarizingCondenser
        from pydantic import SecretStr
        import glob

        start_time = time.time()
        
        # Track files BEFORE execution for change detection
        workspace = Path(self.workspace_dir)
        files_before = {}
        for f in workspace.rglob("*"):
            if f.is_file() and not any(p in str(f) for p in [".git", "__pycache__", ".pyc"]):
                try:
                    files_before[str(f)] = f.stat().st_mtime
                except:
                    pass
        
        # 1. Setup LLM with Ollama optimizations
        api_key = os.getenv("LLM_API_KEY", "ollama")  # Ollama accepts any key
        
        llm_kwargs = {
            "model": self.model,
            "api_key": SecretStr(api_key),
        }
        
        if self.use_ollama:
            llm_kwargs["base_url"] = self.ollama_base_url
            # For Ollama: use prompt-based tool calling if model doesn't support native
            llm_kwargs["native_tool_calling"] = self._supports_tool_calling and self.enable_tool_calling
            
            # Add keep_alive for persistent model loading (Ollama-specific)
            # Note: This is passed through LiteLLM's extra params
            llm_kwargs["extra_body"] = {"keep_alive": self.keep_alive}
        else:
            llm_kwargs["native_tool_calling"] = True
        
        llm = LLM(**llm_kwargs)

        # 2. Build tools based on configuration
        tools = self._build_tools()
        
        if self.verbose:
            print(f"[OpenHands SDK] Loaded {len(tools)} tools")

        # 3. Setup Agent with condenser for context management
        condenser = LLMSummarizingCondenser(
            llm=llm.model_copy(update={"usage_id": "condenser"}),
            max_size=80,
            keep_first=4
        )
        
        agent = Agent(
            llm=llm,
            tools=tools,
            condenser=condenser,
            system_prompt_kwargs={"cli_mode": True},
        )

        if self.verbose:
            print(f"[OpenHands SDK] Starting task in {self.workspace_dir}")

        # 4. Create Conversation with LocalWorkspace
        conversation = Conversation(
            agent=agent,
            workspace=str(self.workspace_dir),
            visualizer=None  # Suppress default noisy output
        )

        # 5. Enhance task prompt with explicit tool usage instructions
        enhanced_task = f"""{task}

INSTRUCTIONS:
- Use the file_editor tool to create or modify files
- Use the terminal tool to run commands if needed
- After making changes, verify the files exist
- Working directory: {self.workspace_dir}

Begin implementing now. Create or modify the necessary files."""

        # 6. Run the task
        try:
            conversation.send_message(enhanced_task)
            conversation.run()
        except Exception as e:
            if on_log:
                on_log(f"Error during execution: {e}")
            return OpenHandsResult(
                success=False,
                message=f"Execution error: {e}",
                logs=str(e),
                execution_time=time.time() - start_time,
            )

        # 7. Collect Metrics and Logs
        metrics = agent.llm.metrics
        token_usage = {
            "prompt_tokens": metrics.accumulated_token_usage.prompt_tokens if hasattr(metrics.accumulated_token_usage, 'prompt_tokens') else 0,
            "completion_tokens": metrics.accumulated_token_usage.completion_tokens if hasattr(metrics.accumulated_token_usage, 'completion_tokens') else 0,
            "total_tokens": metrics.accumulated_token_usage.total_tokens if hasattr(metrics.accumulated_token_usage, 'total_tokens') else 0,
        }
        cost = metrics.accumulated_cost
        
        # 8. Parse events for file operations and extract code
        event_logs = []
        extracted_code = ""
        files_from_events = set()
        
        for event in conversation.state.events:
            event_str = str(event)
            event_logs.append(event_str)
            
            # Look for file editor operations in events
            if "file_editor" in event_str.lower() or "write" in event_str.lower():
                # Try to extract file paths mentioned
                import re
                file_pattern = r'(?:path|file)["\']?\s*[:=]\s*["\']?([^\s"\']+)'
                matches = re.findall(file_pattern, event_str, re.IGNORECASE)
                for match in matches:
                    if match and not match.startswith("http"):
                        files_from_events.add(match)
                
                # Extract code blocks
                code_pattern = r'```[\w]*\n(.*?)```'
                code_matches = re.findall(code_pattern, event_str, re.DOTALL)
                if code_matches:
                    extracted_code = code_matches[-1]  # Take last code block
        
        history_str = "\n".join(event_logs)
        
        # 9. Detect file changes by comparing before/after
        files_changed = list(files_from_events)
        
        for f in workspace.rglob("*"):
            if f.is_file() and not any(p in str(f) for p in [".git", "__pycache__", ".pyc"]):
                try:
                    f_str = str(f)
                    current_mtime = f.stat().st_mtime
                    # New file or modified file
                    if f_str not in files_before or files_before[f_str] < current_mtime:
                        rel_path = str(f.relative_to(workspace))
                        if rel_path not in files_changed:
                            files_changed.append(rel_path)
                except:
                    pass
        
        # Format logs with stats
        stats_msg = f"Task Completed.\nFiles Changed: {files_changed}\nToken Usage: {token_usage}\nCost: ${cost:.4f}"
        full_logs = f"{history_str}\n\n{stats_msg}"
        
        if self.verbose:
            print(f"[OpenHands SDK] {stats_msg}")

        return OpenHandsResult(
            success=True,
            message="Task completed via SDK",
            code=extracted_code,
            files_changed=files_changed,
            logs=full_logs,
            execution_time=time.time() - start_time,
            cost=cost,
            token_usage=token_usage
        )
    
    @classmethod
    def get_available_tools(cls) -> List[str]:
        """Get list of all available tool options."""
        return [t.value for t in ToolOption]
    
    @property
    def supports_tool_calling(self) -> bool:
        """Check if current model supports native tool calling."""
        return self._supports_tool_calling


def create_openhands_worker(
    model: str = "qwen2.5-coder:latest",
    enabled_tools: Optional[Set[ToolOption]] = None,
    **kwargs
) -> OpenHandsWorker:
    """
    Factory function to create an OpenHands worker.
    
    Args:
        model: Ollama model name
        enabled_tools: Set of ToolOption to enable (defaults to terminal, file_editor, apply_patch)
        **kwargs: Additional arguments passed to OpenHandsWorker
        
    Returns:
        Configured OpenHandsWorker instance
    """
    return OpenHandsWorker(
        model=model,
        enabled_tools=enabled_tools,
        **kwargs
    )
