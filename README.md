# Agent Factory 🏭

> A scalable framework for creating specialized AI agents with dynamic tool assignment

Agent Factory is a flexible, production-ready framework built on LangChain that enables you to create specialized AI agents with custom capabilities. Instead of hardcoding tools into agents, Agent Factory allows you to dynamically assign tools based on the agent's role and requirements.

## 🌟 Features

- **Dynamic Agent Creation**: Create agents with custom roles, system prompts, and tool sets
- **Pluggable Tool System**: Add or remove tools without modifying core code
- **Multiple LLM Providers**: Support for OpenAI, Anthropic (Claude), and Google (Gemini)
- **Pre-configured Agents**: Research Agent and Coding Agent ready to use
- **Tool Registry**: Centralized tool management and discovery
- **Memory Management**: Built-in conversation memory for multi-turn interactions
- **LCEL-Based**: Leverages LangChain Expression Language for clean composition

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Examples](#examples)
- [Available Tools](#available-tools)
- [Creating Custom Agents](#creating-custom-agents)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites

- Python 3.10 or 3.11
- Poetry (recommended) or pip

### Using Poetry (Recommended)

**Note:** This project uses Poetry 2.x. See [POETRY_GUIDE.md](POETRY_GUIDE.md) for details on Poetry 2.x changes.

```bash
# Clone the repository
git clone <your-repo-url>
cd agent-factory

# Install dependencies (Poetry 2.x)
poetry sync

# Run commands in the Poetry environment:
# Option 1: Use 'poetry run' prefix
poetry run python agent_factory/examples/demo.py

# Option 2: Activate manually (poetry shell is deprecated in Poetry 2.x)
# Get the environment path
poetry env info --path
# On Unix/Mac: source $(poetry env info --path)/bin/activate
# On Windows: $(poetry env info --path)\Scripts\activate
```

### Using pip

```bash
# Clone the repository
git clone <your-repo-url>
cd agent-factory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Add your API keys to `.env`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🎯 Quick Start

### Research Agent Example

```python
from dotenv import load_dotenv
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import get_research_tools

load_dotenv()

# Create factory
factory = AgentFactory()

# Get research tools
tools = get_research_tools(
    include_wikipedia=True,
    include_duckduckgo=True
)

# Create agent
agent = factory.create_research_agent(
    tools_list=tools,
    system_prompt="You are a helpful research assistant."
)

# Use the agent
response = agent.invoke({"input": "What is LangChain?"})
print(response['output'])
```

### Coding Agent Example

```python
from agent_factory.tools.coding_tools import get_coding_tools

# Get coding tools
tools = get_coding_tools(
    include_read=True,
    include_write=True,
    include_list=True,
    base_dir="."
)

# Create agent
agent = factory.create_coding_agent(
    tools_list=tools,
    system_prompt="You are a helpful coding assistant."
)

# Use the agent
response = agent.invoke({"input": "List all Python files in the current directory"})
print(response['output'])
```

### Run the Demo

```bash
# With Poetry 2.x
poetry run python agent_factory/examples/demo.py

# Or if you've activated the environment manually
python agent_factory/examples/demo.py
```

## 🧠 Core Concepts

### Agent Factory

The `AgentFactory` class is the core of the framework. It provides methods to create agents with different configurations:

```python
factory = AgentFactory(
    default_llm_provider="openai",  # or "anthropic", "google"
    default_model="gpt-4o",
    default_temperature=0.0,
    verbose=True
)
```

### Tools

Tools are capabilities that agents can use to interact with the world. Agent Factory includes:

**Research Tools:**
- Wikipedia Search
- DuckDuckGo Web Search
- Tavily AI Search (requires API key)
- Current Time

**Coding Tools:**
- Read Files
- Write Files
- List Directory
- Search Files
- Git Status

### Tool Registry

The `ToolRegistry` provides centralized tool management:

```python
from agent_factory.tools.tool_registry import ToolRegistry

registry = ToolRegistry()
registry.register("wikipedia", WikipediaSearchTool(), category="research")
tools = registry.get_by_category("research")
```

## 📚 Examples

### Custom Agent with Mixed Tools

```python
from agent_factory.tools.research_tools import WikipediaSearchTool
from agent_factory.tools.coding_tools import ReadFileTool

# Combine different tool types
mixed_tools = [
    WikipediaSearchTool(),
    ReadFileTool(),
]

# Create custom agent
agent = factory.create_agent(
    role="Hybrid Agent",
    tools_list=mixed_tools,
    system_prompt="You are a versatile AI assistant.",
    agent_type=AgentFactory.AGENT_TYPE_STRUCTURED_CHAT
)
```

### Using Different LLM Providers

```python
# Use Claude (Anthropic)
agent = factory.create_agent(
    role="Research Agent",
    tools_list=tools,
    llm_provider="anthropic",
    model="claude-3-opus-20240229"
)

# Use Gemini (Google)
agent = factory.create_agent(
    role="Research Agent",
    tools_list=tools,
    llm_provider="google",
    model="gemini-pro"
)
```

### Interactive Chat Mode

```python
agent = factory.create_research_agent(tools)

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break

    response = agent.invoke({"input": user_input})
    print(f"Agent: {response['output']}")
```

## 🛠️ Available Tools

### Research Tools

| Tool | Description | API Key Required |
|------|-------------|------------------|
| `WikipediaSearchTool` | Search Wikipedia articles | No |
| `DuckDuckGoSearchTool` | Web search via DuckDuckGo | No |
| `TavilySearchTool` | AI-optimized web search | Yes (TAVILY_API_KEY) |
| `CurrentTimeTool` | Get current time | No |

### Coding Tools

| Tool | Description | Configuration |
|------|-------------|---------------|
| `ReadFileTool` | Read file contents | base_dir |
| `WriteFileTool` | Write or append to files | base_dir |
| `ListDirectoryTool` | List directory contents | base_dir |
| `FileSearchTool` | Search files by pattern | base_dir |
| `GitStatusTool` | Check Git repository status | - |

## 🎨 Creating Custom Agents

### Method 1: Using Factory Methods

```python
# Pre-configured research agent
agent = factory.create_research_agent(tools)

# Pre-configured coding agent
agent = factory.create_coding_agent(tools)
```

### Method 2: Using Generic create_agent

```python
agent = factory.create_agent(
    role="Data Analyst Agent",
    tools_list=[tool1, tool2, tool3],
    system_prompt="You are a data analyst...",
    agent_type=AgentFactory.AGENT_TYPE_REACT,
    enable_memory=True,
    llm_provider="openai",
    model="gpt-4o",
    temperature=0.2
)
```

### Method 3: Creating Custom Tool

```python
from typing import Type
from langchain_core.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

class MyToolInput(BaseModel):
    query: str = Field(description="The input query")

class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "Description of what this tool does"
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, query: str) -> str:
        # Your tool logic here
        return f"Processed: {query}"

# Use your custom tool
tools = [MyCustomTool()]
agent = factory.create_agent(role="Custom Agent", tools_list=tools)
```

## 📖 API Reference

### AgentFactory

```python
class AgentFactory:
    def __init__(
        self,
        default_llm_provider: str = "openai",
        default_model: str = "gpt-4o",
        default_temperature: float = 0.0,
        verbose: bool = True
    )

    def create_agent(
        self,
        role: str,
        tools_list: List[BaseTool],
        system_prompt: Optional[str] = None,
        agent_type: str = "react",
        enable_memory: bool = True,
        **kwargs
    ) -> AgentExecutor

    def create_research_agent(
        self,
        tools_list: List[BaseTool],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AgentExecutor

    def create_coding_agent(
        self,
        tools_list: List[BaseTool],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AgentExecutor
```

### Utility Functions

```python
# Get pre-configured tool sets
get_research_tools(
    include_wikipedia=True,
    include_duckduckgo=True,
    include_tavily=False,
    include_time=True
) -> List[BaseTool]

get_coding_tools(
    include_read=True,
    include_write=True,
    include_list=True,
    include_git=True,
    include_search=True,
    base_dir="."
) -> List[BaseTool]
```

## 🏗️ Project Structure

```
agent_factory/
├── core/
│   └── agent_factory.py       # Main factory class
├── tools/
│   ├── tool_registry.py       # Tool registration system
│   ├── research_tools.py      # Research/web tools
│   └── coding_tools.py        # File system tools
├── agents/
│   ├── research_agent.py      # Pre-configured research agent
│   └── coding_agent.py        # Pre-configured coding agent
├── examples/
│   └── demo.py                # Demonstration scripts
└── config/
    └── agent_configs.yaml     # Agent configurations
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
poetry install

# Run tests
pytest

# Format code
black agent_factory/
isort agent_factory/

# Lint code
ruff agent_factory/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This project incorporates patterns from the [LangChain Crash Course](https://github.com/Mikecranesync/langchain-crash-course), also under MIT License.

## 🙏 Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Inspired by the [LangChain Crash Course](https://github.com/Mikecranesync/langchain-crash-course)
- Pattern concepts from the Agent Factory prompt methodology

## 🐛 Known Issues

- Git operations require GitPython package
- Tavily search requires API key (free tier available)
- Some tools may have platform-specific behavior (Windows vs. Unix)

## 🗺️ Roadmap

- [ ] Add more built-in tools (database, API calls, etc.)
- [ ] Support for LangGraph multi-agent orchestration
- [ ] Web UI for agent interaction
- [ ] Agent templates library
- [ ] Configuration-driven agent creation (YAML/JSON)
- [ ] Observability and monitoring integration
- [ ] Async agent execution
- [ ] Agent performance metrics

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/agent-factory/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/agent-factory/discussions)

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

Made with ❤️ by the Agent Factory community
