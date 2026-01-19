# Agent Factory

**A scalable framework for creating specialized AI agents with dynamic tool assignment.**

> 📚 **Documentation:** Main documentation is now located in the `docs/` directory.
> - [Free LLM Guide](docs/OPENHANDS_FREE_LLM_GUIDE.md)
> - [Create New Repo Guide](docs/guides/CREATE_NEW_REPO.md)

## 🚀 Zero-Cost Autonomous Coding

Run autonomous coding agents **100% locally** using OpenHands + Ollama. No API costs, no subscriptions.

| Solution | Cost/Month |
|----------|------------|
| **Agent Factory + Ollama** | **$0** |
| Claude Code Subscription | $200 |
| Claude/GPT API | $100-300 |

## ⚡ Quick Start

### 1. Prerequisites
- [Ollama](https://ollama.com) installed and running
- Python 3.12+
- Docker (for OpenHands sandbox)

### 2. Install
```bash
# Clone and install
git clone https://github.com/jasperan/agent-factory.git
cd agent-factory
pip install -r requirements.txt

# Install OpenHands
uv tool install openhands --python 3.12

# Pull a coding model
ollama pull deepseek-coder:6.7b
```

### 3. Run Autonomous Mode (Default)

```bash
USE_OLLAMA=true python agentcli.py autonomous
```

This will:
- Read tasks from `backlog/tasks/*.md`
- Execute each task using OpenHands + Ollama
- Run continuously until stopped (Ctrl+C)

**Options:**
```bash
# Dry run (no actual execution)
USE_OLLAMA=true python agentcli.py autonomous --dry-run

# Custom interval (seconds between cycles)
USE_OLLAMA=true python agentcli.py autonomous --interval 120

# Limit tasks per cycle
USE_OLLAMA=true python agentcli.py autonomous --max-tasks 5
```

### Alternative: Interactive CLI
```bash
python cli.py start
```

### Alternative: Web GUI
```bash
python gui.py
```

## 📁 Task Format

Create task files in `backlog/tasks/`:

```markdown
---
id: task-42
title: Add user authentication
status: To Do
priority: high
---

## Description
Implement JWT-based authentication for the API.

## Acceptance Criteria
- [ ] Login endpoint returns JWT token
- [ ] Protected routes require valid token
- [ ] Unit tests pass
```

## 🔧 Configuration

Add to `.env`:
```bash
USE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:6.7b
```

## 📚 Documentation

- **[Free LLM Guide](docs/OPENHANDS_FREE_LLM_GUIDE.md)**: Full Ollama setup guide
- **[Create a New Repository](docs/guides/CREATE_NEW_REPO.md)**: Scaffold new projects
- **[Architecture](docs/SYSTEM_MAP.md)**: System overview

## 🤝 Contributing
Open issues or submit PRs to improve the factory!
