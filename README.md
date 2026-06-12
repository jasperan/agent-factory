# Agent Factory

**Autonomous AI Coding Agent powered by OpenHands SDK + Ollama (100% Free & Local)**

Two entry points:
1. **`openhands_cli.py`** - Interactive CLI for manual coding tasks
2. **`autonomous_cli.py`** - Autonomous code improvement system with Planner → Worker → Judge pipeline

## Quick Start

<!-- one-command-install -->
> **One-command install** — clone, configure, and run in a single step:
>
> ```bash
> curl -fsSL https://raw.githubusercontent.com/jasperan/agent-factory/main/install.sh | bash
> ```
>
> <details><summary>Advanced options</summary>
>
> Override install location:
> ```bash
> PROJECT_DIR=/opt/myapp curl -fsSL https://raw.githubusercontent.com/jasperan/agent-factory/main/install.sh | bash
> ```
>
> Or install manually:
> ```bash
> git clone https://github.com/jasperan/agent-factory.git
> cd agent-factory
> # See below for setup instructions
> ```
> </details>


```bash
# Install dependencies
pip install -r requirements.txt

# Interactive CLI (manual tasks)
python openhands_cli.py

# Autonomous CLI (auto code improvement)
python autonomous_cli.py

# Headless mode (for CI/automation)
python autonomous_cli.py --headless --target /path/to/repo --max-suggestions 3
```

## Autonomous Code Improvement System

The autonomous system continuously improves your codebase using a three-agent pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│  PLANNER (LLM)                                              │
│  • Scans codebase structure                                 │
│  • Analyzes code for improvements                           │
│  • Generates prioritized suggestions with acceptance criteria│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  USER REVIEW                                                 │
│  • Accept / Reject / Skip each suggestion                   │
│  • Or auto-accept all                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  WORKER (OpenHands)                                         │
│  • Implements accepted suggestions                          │
│  • Uses Terminal, FileEditor, ApplyPatch tools              │
│  • Iterates based on Judge feedback                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  JUDGE (LLM)                                                │
│  • Verifies implementation against acceptance criteria      │
│  • Provides feedback for iteration                          │
│  • PASS / FAIL / NEEDS_ITERATION verdict                    │
└─────────────────────────────────────────────────────────────┘
```

### Autonomous CLI Usage

```bash
python autonomous_cli.py
```

Menu options:
- **🚀 Start Autonomous Run** - Analyze codebase and generate improvement suggestions
- **⚙️ Settings** - View/modify configuration
- **❓ Help** - Usage instructions

### Programmatic Usage

```python
from agent_factory.autonomous import AutonomousRunner, AutonomousConfig

config = AutonomousConfig(
    target_repo="/path/to/your/repo",
    model="qwen2.5-coder:latest",
    max_suggestions=5,
    max_iterations=3,  # Max Worker-Judge loops per suggestion
    num_ctx=32768,     # Large context for codebases
)

runner = AutonomousRunner(config)

# Generate suggestions
suggestions = runner.generate_suggestions()

# Run accepted suggestions
runner.run_all(suggestions)
```

## OpenHands Interactive CLI

For manual coding tasks, use the original CLI:

```bash
python openhands_cli.py
```

Features:
- Arrow-key model selection
- Tool configuration
- Real-time file change display
- Token usage tracking

## Available SDK Tools

| Tool | Description | Default |
|------|-------------|---------|
| `terminal` | Execute shell commands | ✅ |
| `file_editor` | Create and edit files | ✅ |
| `apply_patch` | Apply unified diff patches | ✅ |
| `task_tracker` | Track task progress | ❌ |
| `browser` | Web browsing (requires playwright) | ❌ |

## Recommended Ollama Models

```bash
ollama pull qwen2.5-coder:latest    # Best for coding
ollama pull deepseek-coder:latest   # Alternative
ollama pull llama3.2:latest         # General purpose
```

## Project Structure

```
agent-factory/
├── openhands_cli.py               # Interactive CLI entry point
├── autonomous_cli.py              # Autonomous improvement CLI
├── agent_factory/
│   ├── autonomous/
│   │   ├── models.py              # Suggestion, Verdict, Run models
│   │   ├── config.py              # AutonomousConfig
│   │   ├── suggestion_generator.py # Planner: scans code and proposes improvements
│   │   ├── autonomous_runner.py   # Orchestrates Planner → Worker → Judge, persists runs
│   │   └── llm_utils.py           # Shared Ollama completion + JSON extraction helpers
│   └── workers/
│       └── openhands_worker.py    # Worker: OpenHands SDK integration
├── pyproject.toml
└── tests/                         # Default workspace
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_OLLAMA` | `true` | Enable Ollama mode |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `VERBOSE` | `true` | Show debug output |

## Requirements

- Python 3.12+
- [Ollama](https://ollama.ai) installed and running
- OpenHands SDK: `pip install openhands-sdk openhands-tools`

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS CLI                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Start Run│  │ History  │  │ Settings │  │   Exit   │        │
│  └────┬─────┘  └──────────┘  └──────────┘  └──────────┘        │
└───────┼─────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS RUNNER                               │
│                                                                    │
│  ┌─────────┐    generate     ┌──────────┐    implement    ┌─────┐│
│  │ PLANNER │ ──────────────► │ Suggestion│ ──────────────► │WORKER││
│  │  (LLM)  │                 │  Queue    │                 │(OH) ││
│  └─────────┘                 └──────────┘                 └──┬──┘│
│       ▲                           │                          │    │
│       │                           │                          ▼    │
│       │ iterate if fail           │                    ┌─────────┐│
│       └───────────────────────────┼────────────────────│  JUDGE  ││
│                                   │                    │  (LLM)  ││
│                                   │                    └────┬────┘│
│                                   │      verdict            │     │
│                                   ◄─────────────────────────┘     │
136: └───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│                    OPENHANDS SDK                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                   │
│  │ Terminal   │  │ FileEditor │  │ ApplyPatch │                   │
│  └────────────┘  └────────────┘  └────────────┘                   │
│                                                                    │
│  Target Repository: /path/to/repo                                  │
└───────────────────────────────────────────────────────────────────┘
```

## License

MIT
