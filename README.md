# Agent Factory - OpenHands CLI

**AI Coding Agent powered by OpenHands SDK + Ollama (100% Free & Local)**

A Gemini-style interactive CLI for autonomous code generation using local LLMs via Ollama. No API keys required.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the interactive CLI
python openhands_cli.py
```

## Features

| Feature | Description |
|---------|-------------|
| **Interactive CLI** | Gemini-style interface with arrow key navigation |
| **Model Selection** | Choose from any installed Ollama model |
| **Tool Calling** | Native function calling for supported models (qwen2.5-coder, llama3.1, etc.) |
| **All SDK Tools** | Terminal, FileEditor, ApplyPatch, TaskTracker, Browser, Delegate |
| **Auto-Visualization** | Displays only new or modified files |
| **Token Tracking** | Shows token usage and cost per task |
| **Local & Free** | Uses Ollama - no API costs |

## Available Tools

The OpenHands SDK provides these tools that agents can use:

| Tool | Description | Default |
|------|-------------|---------|
| `terminal` | Execute shell commands | ✅ |
| `file_editor` | Create and edit files | ✅ |
| `apply_patch` | Apply unified diff patches | ✅ |
| `task_tracker` | Track task progress | ❌ |
| `browser` | Web browsing (requires playwright) | ❌ |
| `delegate` | Multi-agent delegation | ❌ |

## Recommended Ollama Models

```bash
# Best for coding tasks (with tool calling support)
ollama pull qwen2.5-coder:latest    # Recommended
ollama pull deepseek-coder:latest   # Alternative
ollama pull llama3.2:latest         # General purpose + tools
ollama pull codegemma:latest        # Code focused
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `USE_OLLAMA` | `true` | Enable Ollama mode |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `VERBOSE` | `true` | Show debug output |

## How It Works

The CLI uses the [OpenHands SDK](https://docs.openhands.dev/sdk/getting-started) with [LiteLLM](https://docs.litellm.ai/docs/providers/ollama) for Ollama integration:

1. **Model Selection**: Choose from available Ollama models (coding models prioritized)
2. **Tool Configuration**: Optionally customize which tools the agent can use
3. **Task Execution**: Agent uses tools to complete your coding task
4. **Result Display**: Shows modified files with syntax highlighting

### LiteLLM Ollama Integration

- Uses `ollama_chat/` prefix for models with native tool calling
- Uses `ollama/` prefix for models requiring prompt-based tool calling
- Supports `keep_alive` for persistent model loading

## Example Session

```
╭─────────────────────────────────────────────────╮
│ OpenHands Interactive CLI                       │
│ Model: qwen2.5-coder:latest | Tools: terminal, file_editor, apply_patch │
╰─────────────────────────────────────────────────╯
Workspace: /home/user/project/tests
Ready. Type 'exit' or 'quit' to leave.

 Task > create a python script that generates fibonacci numbers

╭─────────── Result ───────────╮
│ Success                      │
│ Tokens: 1234 | Cost: $0.0000 │
╰──────────────────────────────╯

Modified/Created Files:
╭──── fibonacci.py ────╮
│   1 def fibonacci(n):│
│   2     if n <= 1:   │
│   3         return n │
│   ...                │
╰──────────────────────╯
```

## Project Structure

```
agent-factory/
├── openhands_cli.py           # Main entry point - Interactive CLI
├── agent_factory/
│   ├── core/
│   │   └── agent_factory.py   # Factory for creating agents
│   └── workers/
│       └── openhands_worker.py # OpenHands SDK integration
├── requirements.txt           # Python dependencies
└── tests/                     # Default workspace directory
```

## Requirements

- Python 3.12+
- [Ollama](https://ollama.ai) installed and running
- OpenHands SDK packages:
  ```bash
  pip install openhands-sdk openhands-tools
  ```

## Programmatic Usage

```python
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.workers.openhands_worker import ToolOption

# Create factory configured for Ollama
factory = AgentFactory(
    default_llm_provider="ollama",
    default_model="qwen2.5-coder:latest",
    enable_routing=False
)

# Create worker with specific tools
worker = factory.create_openhands_agent(
    workspace_dir="/path/to/workspace",
    enabled_tools={ToolOption.TERMINAL, ToolOption.FILE_EDITOR},
    enable_tool_calling=True,
    keep_alive="10m"
)

# Run a task
result = worker.run_task("Create a hello world script")
print(result.logs)
```

## License

MIT
