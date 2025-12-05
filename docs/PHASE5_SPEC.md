# PHASE5_SPEC.md - Project Twin (Digital Twin System)

## Overview

Build a digital twin that mirrors your project's codebase, providing intelligent context about structure, patterns, and state. The twin maintains a living representation of the project for instant queries.

**Success:** Ask "What files handle authentication?" and get accurate answers without searching.

**Vision:** Friday (voice AI) + Jarvis (digital ecosystem) = Project Twin bridges them.

---

## Concept: Digital Twin

A **digital twin** is a virtual replica that:
- Mirrors the real project structure
- Understands code relationships
- Tracks project state and changes
- Answers questions about the codebase
- Provides context for agent decisions

**Not a simple file index** - it's an intelligent representation with semantic understanding.

---

## Files to Create

```
agent_factory/refs/
├── __init__.py
├── project_twin.py          # Main twin class
├── code_analyzer.py          # Parses and understands code
├── knowledge_graph.py        # Relationships between files
└── twin_agent.py             # Agent that queries the twin

tests/test_project_twin.py
agent_factory/examples/twin_demo.py
```

---

## 1. Core Data Structure - The Twin

### `refs/project_twin.py`

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime


@dataclass
class FileNode:
    """Represents a file in the project twin."""
    path: Path
    file_type: str  # "python", "markdown", "config", etc.
    last_modified: datetime
    size_bytes: int

    # Semantic information
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)

    # Documentation
    docstring: Optional[str] = None
    comments: List[str] = field(default_factory=list)

    # Metadata
    purpose: Optional[str] = None  # What this file does
    related_files: List[Path] = field(default_factory=list)


@dataclass
class ProjectTwin:
    """
    Digital twin of a software project.

    Maintains a semantic representation of:
    - File structure and relationships
    - Code dependencies
    - Documentation and patterns
    - Project state and history
    """
    project_root: Path
    files: Dict[Path, FileNode] = field(default_factory=dict)
    last_sync: Optional[datetime] = None

    # Knowledge graph
    file_graph: Dict[Path, Set[Path]] = field(default_factory=dict)  # path -> dependencies
    function_map: Dict[str, Path] = field(default_factory=dict)  # function_name -> file
    class_map: Dict[str, Path] = field(default_factory=dict)  # class_name -> file

    def sync(self, include_patterns: List[str] = None, exclude_patterns: List[str] = None):
        """
        Sync twin with actual project files.

        Scans project directory and updates twin representation.
        """
        pass

    def query(self, question: str) -> str:
        """
        Answer questions about the project.

        Examples:
            - "What files handle authentication?"
            - "Where is the User class defined?"
            - "What depends on database.py?"
        """
        pass

    def find_files_by_purpose(self, purpose: str) -> List[Path]:
        """Find files that serve a specific purpose."""
        pass

    def get_dependencies(self, file_path: Path) -> Set[Path]:
        """Get all dependencies of a file."""
        pass

    def get_dependents(self, file_path: Path) -> Set[Path]:
        """Get all files that depend on this file."""
        pass

    def get_file_summary(self, file_path: Path) -> str:
        """Get human-readable summary of a file."""
        pass
```

---

## 2. Code Analysis

### `refs/code_analyzer.py`

Parses Python files to extract semantic information:

```python
import ast
from pathlib import Path
from typing import List, Set


class CodeAnalyzer:
    """
    Analyzes Python code to extract semantic information.

    Uses AST parsing to understand:
    - Function and class definitions
    - Import statements
    - Docstrings and comments
    - Call relationships
    """

    def analyze_file(self, file_path: Path) -> FileNode:
        """
        Analyze a Python file and extract information.

        Returns FileNode with:
        - Functions: List of function names
        - Classes: List of class names
        - Imports: What this file imports
        - Dependencies: Files this depends on
        - Docstring: Module docstring
        """
        pass

    def extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract function definitions from AST."""
        pass

    def extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class definitions from AST."""
        pass

    def extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements."""
        pass

    def infer_purpose(self, file_node: FileNode) -> str:
        """
        Infer the purpose of a file from its contents.

        Uses heuristics:
        - File name patterns (test_*, config*, setup*)
        - Docstrings
        - Function/class names
        - Import patterns
        """
        pass
```

---

## 3. Knowledge Graph

### `refs/knowledge_graph.py`

Builds a graph of file relationships:

```python
from pathlib import Path
from typing import Dict, Set, List
import networkx as nx


class KnowledgeGraph:
    """
    Graph representation of project structure.

    Nodes: Files
    Edges: Dependencies (imports, calls, references)

    Enables queries like:
    - What depends on this?
    - What's the dependency chain?
    - Find circular dependencies
    - Identify central files (most imported)
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_file(self, file_path: Path, dependencies: Set[Path]):
        """Add a file and its dependencies to the graph."""
        pass

    def get_dependencies(self, file_path: Path, recursive: bool = False) -> Set[Path]:
        """Get direct or transitive dependencies."""
        pass

    def get_dependents(self, file_path: Path, recursive: bool = False) -> Set[Path]:
        """Get files that depend on this file."""
        pass

    def find_path(self, from_file: Path, to_file: Path) -> List[Path]:
        """Find dependency path between two files."""
        pass

    def find_circular_dependencies(self) -> List[List[Path]]:
        """Find circular dependency cycles."""
        pass

    def get_central_files(self, top_n: int = 10) -> List[Path]:
        """Get most-depended-on files (by PageRank or degree)."""
        pass
```

---

## 4. Twin Agent

### `refs/twin_agent.py`

An agent that uses the twin to answer questions:

```python
from agent_factory.core import AgentFactory
from .project_twin import ProjectTwin


class TwinAgent:
    """
    Agent that queries the project twin.

    Combines:
    - ProjectTwin (semantic project representation)
    - LLM (natural language understanding)
    - Tools (code analysis, search)

    Can answer:
    - "Where is X defined?"
    - "What depends on Y?"
    - "Show me all authentication files"
    - "Explain how the database connection works"
    """

    def __init__(self, project_twin: ProjectTwin, llm=None):
        self.twin = project_twin
        self.llm = llm

        # Create specialized tools
        self.tools = [
            self._create_find_file_tool(),
            self._create_get_dependencies_tool(),
            self._create_search_functions_tool(),
            self._create_explain_file_tool(),
        ]

        # Create agent
        factory = AgentFactory()
        self.agent = factory.create_agent(
            role="Project Twin Assistant",
            tools_list=self.tools,
            system_prompt=self._get_system_prompt()
        )

    def query(self, question: str) -> str:
        """Ask the twin a question about the project."""
        return self.agent.invoke({"input": question})

    def _get_system_prompt(self) -> str:
        """System prompt that gives context about the project."""
        return f"""You are a Project Twin assistant.

You have deep knowledge of this project:
- Project root: {self.twin.project_root}
- Total files: {len(self.twin.files)}
- Last synced: {self.twin.last_sync}

You can answer questions about:
- File locations and purposes
- Code dependencies and relationships
- Function and class definitions
- Project structure and patterns

Use your tools to query the project twin and provide accurate answers."""

    def _create_find_file_tool(self):
        """Tool: Find files by purpose or name."""
        pass

    def _create_get_dependencies_tool(self):
        """Tool: Get dependencies of a file."""
        pass

    def _create_search_functions_tool(self):
        """Tool: Search for functions/classes."""
        pass

    def _create_explain_file_tool(self):
        """Tool: Explain what a file does."""
        pass
```

---

## 5. Integration with Orchestrator

The Twin Agent becomes a specialist that can be registered:

```python
from agent_factory.core import AgentFactory
from agent_factory.refs import ProjectTwin, TwinAgent

# Create factory
factory = AgentFactory()

# Create project twin
twin = ProjectTwin(project_root=Path.cwd())
twin.sync(
    include_patterns=["*.py", "*.md"],
    exclude_patterns=["**/tests/**", "**/__pycache__/**"]
)

# Create twin agent
twin_agent = TwinAgent(project_twin=twin, llm=factory._create_llm())

# Create orchestrator
orchestrator = factory.create_orchestrator()

# Register twin agent
orchestrator.register(
    "project_twin",
    twin_agent.agent,
    keywords=["where is", "find file", "what depends", "show me", "list files"],
    description="Answers questions about project structure and code",
    priority=20  # High priority for codebase questions
)

# Now queries about the project route to twin
result = orchestrator.route("Where is the User class defined?")
# → Routes to project_twin agent
# → Uses knowledge graph to find User class
# → Returns "User class is defined in agent_factory/models/user.py"
```

---

## 6. Use Cases

### UC-1: Find File by Purpose
**Query:** "What files handle authentication?"
**Twin Response:**
```
Authentication is handled by:
- agent_factory/auth/login.py (login flow)
- agent_factory/auth/tokens.py (JWT token management)
- agent_factory/middleware/auth.py (authentication middleware)
```

### UC-2: Understand Dependencies
**Query:** "What depends on database.py?"
**Twin Response:**
```
Files that depend on database.py:
- agent_factory/models/user.py
- agent_factory/models/agent.py
- agent_factory/tools/storage.py
Total: 3 files
```

### UC-3: Explain File Purpose
**Query:** "What does orchestrator.py do?"
**Twin Response:**
```
orchestrator.py (agent_factory/core/orchestrator.py)

Purpose: Multi-agent routing system

Key components:
- AgentOrchestrator class: Routes queries to specialist agents
- RouteResult dataclass: Result of routing operation
- Routing methods: keyword matching, LLM classification, fallback

Dependencies: callbacks.py, langchain_core
Used by: AgentFactory, demo scripts
```

### UC-4: Code Navigation
**Query:** "Show me the route() function"
**Twin Response:**
```
route() function found in:
- agent_factory/core/orchestrator.py:346 (main implementation)

def route(self, query: str) -> RouteResult:
    Routes query to appropriate agent and executes.

    Routing order:
    1. Keyword match (fast, deterministic)
    2. LLM classification (flexible)
    3. Fallback agent (if configured)
    4. Error response
```

---

## 7. Phase 5 Dependencies

**Required from Phase 2 (Structured Outputs):**
- Consistent data structures for twin responses
- Type-safe knowledge representation

**Required from Phase 3 (Enhanced Observability):**
- Track twin sync operations
- Monitor query performance
- Log twin state changes

**Required from Phase 4 (Deterministic Tools):**
- Reliable file parsing
- Consistent dependency extraction
- Repeatable analysis results

---

## 8. Implementation Phases

### Phase 5.1: Core Twin (2 days)
- [ ] ProjectTwin class with basic file tracking
- [ ] Sync mechanism (scan project, index files)
- [ ] Simple query interface
- [ ] File metadata extraction

### Phase 5.2: Code Analysis (2 days)
- [ ] CodeAnalyzer with AST parsing
- [ ] Function/class extraction
- [ ] Import dependency tracking
- [ ] Purpose inference heuristics

### Phase 5.3: Knowledge Graph (2 days)
- [ ] KnowledgeGraph with NetworkX
- [ ] Dependency relationship building
- [ ] Graph queries (dependencies, dependents, paths)
- [ ] Circular dependency detection

### Phase 5.4: Twin Agent (2 days)
- [ ] TwinAgent with specialized tools
- [ ] Natural language query processing
- [ ] Integration with orchestrator
- [ ] Demo and tests

---

## 9. Success Criteria

Phase 5 is complete when:

1. **Twin can sync with project**
   ```python
   twin = ProjectTwin(project_root=Path.cwd())
   twin.sync()
   assert len(twin.files) > 0
   ```

2. **Twin can answer structure questions**
   ```python
   answer = twin.query("Where is AgentFactory defined?")
   assert "agent_factory.py" in answer
   ```

3. **Twin can track dependencies**
   ```python
   deps = twin.get_dependencies(Path("agent_factory/core/orchestrator.py"))
   assert Path("agent_factory/core/callbacks.py") in deps
   ```

4. **Twin agent routes correctly**
   ```python
   orchestrator.register("twin", twin_agent, keywords=["where is", "find"])
   result = orchestrator.route("Where is the EventBus?")
   assert result.agent_name == "twin"
   ```

5. **Demo runs without errors**
   ```bash
   poetry run python agent_factory/examples/twin_demo.py
   ```

---

## 10. Friday + Jarvis Integration

**Friday (Voice AI):** "Show me the authentication code"
→ Routes to Twin Agent
→ Twin finds auth files
→ Friday reads back file locations

**Jarvis (Digital Ecosystem):** Manages project state
→ Uses Twin to understand structure
→ Monitors file changes
→ Suggests refactoring opportunities

**Together:** Voice-controlled project navigation powered by digital twin.

---

## 11. Future Enhancements (Phase 6+)

- **Semantic Search:** Vector embeddings for fuzzy file search
- **Change Detection:** Track git commits, auto-sync twin
- **Code Generation:** Twin suggests code based on patterns
- **Multi-Project:** Twin manages multiple projects
- **Visual Graph:** Web UI showing dependency graph
- **AI Refactoring:** Twin identifies improvement opportunities

---

**Save this as `docs/PHASE5_SPEC.md`**

**Constitutional Note:** This spec defines the Project Twin. Code in `agent_factory/refs/` will be generated from this specification using factory.py when Phase 5 begins.
