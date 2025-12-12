# Quick Start Guide

Get up and running with Agent Factory in 5 minutes!

## 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd agent-factory

# Install with Poetry 2.x (recommended)
poetry sync

# OR install with pip
pip install -e .
```

**Note:** If using Poetry, this project requires Poetry 2.x. The `poetry shell` command is deprecated. Use `poetry run` prefix or manually activate the environment.

## 2. Set up API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

## 3. Run the Demo

```bash
# With Poetry 2.x
poetry run python agent_factory/examples/demo.py

# Or if using pip/venv
python agent_factory/examples/demo.py
```

## 4. Try Your First Agent

Create a file called `my_first_agent.py`:

```python
from dotenv import load_dotenv
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import get_research_tools

# Load environment variables
load_dotenv()

# Create factory and tools
factory = AgentFactory()
tools = get_research_tools()

# Create research agent
agent = factory.create_research_agent(tools)

# Ask a question
response = agent.invoke({"input": "What is artificial intelligence?"})
print(response['output'])
```

Run it:

```bash
# With Poetry 2.x
poetry run python my_first_agent.py

# Or if using pip/venv
python my_first_agent.py
```

## 5. What's Next?

- **Read the full [README.md](README.md)** for detailed documentation
- **Explore [examples/demo.py](agent_factory/examples/demo.py)** for more advanced usage
- **Create custom tools** by following the patterns in `agent_factory/tools/`
- **Build your own agents** using the factory pattern

## Common Issues

### "No module named 'agent_factory'"

Make sure you've installed the package:
```bash
pip install -e .
```

### "OPENAI_API_KEY not found"

Set your API key in the `.env` file or as an environment variable:
```bash
export OPENAI_API_KEY='your-key-here'
```

### Import errors

Make sure you're in the activated virtual environment or using `poetry run`:
```bash
# Option 1: Use poetry run (Poetry 2.x)
poetry run python your_script.py

# Option 2: Activate manually
# Get path: poetry env info --path
# Then activate based on your OS
```

## Need Help?

- Check the [README.md](README.md) for full documentation
- Open an issue on GitHub
- Review the example code in `agent_factory/examples/`

Happy building! 🚀
