# Agent Factory

**A scalable framework for creating specialized AI agents with dynamic tool assignment.**

> 📚 **Documentation:** Main documentation is now located in the `docs/` directory.
> - [Free LLM Guide](docs/OPENHANDS_FREE_LLM_GUIDE.md)
> - [Create New Repo Guide](docs/guides/CREATE_NEW_REPO.md)

## OverviewnHands and local LLMs.**

## 🚀 Main Feature: Run entirely for $0

Stop paying for expensive API credits. Agent Factory allows you to run autonomous coding agents 100% locally using Ollama.


This guide covers:
- Installing Ollama
- Setting up DeepSeek Coder (6.7B/33B)
- Running your first autonomous coding task for free

## ⚡ Quick Start

### 1. Prerequisites
- [Ollama](https://ollama.com) installed
- Python 3.11+
- Docker (for OpenHands isolation)

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/jasperan/agent-factory.git
cd agent-factory

# Install dependencies
pip install -r requirements.txt
# OR if you have Poetry
poetry install

# Configure Environment
cp .env.example .env
# Edit .env to set USE_OLLAMA=true and OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Verify Setup
Run the included demo to confirm your free local LLM is working:
```bash
python3 examples/openhands_ollama_demo.py
```

## 📚 Documentation

- **[Create a New Repository](docs/guides/CREATE_NEW_REPO.md)**: How to use the Agent Factory to scaffold and build new projects from scratch.
- **[Project History](docs/PROJECT_HISTORY.md)**: detailed logs and history of the Agent Factory development.
- **[Architecture](docs/SYSTEM_MAP.md)**: System map and components.

## 🤝 Contributing
Open issues or submit PRs to improve the factory!
