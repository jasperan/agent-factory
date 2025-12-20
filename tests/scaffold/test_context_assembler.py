"""Unit tests for ContextAssembler.

Tests the context assembly for Claude Code CLI execution.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from agent_factory.scaffold.context_assembler import (
    ContextAssembler,
    ContextAssemblerError,
    create_context_assembler
)


# Fixtures

@pytest.fixture
def temp_repo(tmp_path):
    """Create temporary repo structure for testing."""
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Create CLAUDE.md
    claude_md = repo / "CLAUDE.md"
    claude_md.write_text("""# Test System Prompt

You are a helpful assistant.

## Instructions

Follow these rules:
1. Be concise
2. Be accurate

## Additional Section

More content here.
""")

    # Create some files
    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("print('hello')")
    (repo / "README.md").write_text("# Test Repo")

    return repo


@pytest.fixture
def sample_task():
    """Sample task data."""
    return {
        "id": "task-42",
        "title": "Test Task",
        "description": "This is a test task",
        "acceptance_criteria": [
            "Criterion 1",
            "Criterion 2",
            "Criterion 3"
        ]
    }


@pytest.fixture
def assembler(temp_repo):
    """ContextAssembler instance with temp repo."""
    return ContextAssembler(repo_root=temp_repo, max_tree_depth=2, max_commits=5)


# Initialization Tests

def test_initialization(temp_repo):
    """Test ContextAssembler initializes correctly."""
    assembler = ContextAssembler(repo_root=temp_repo)

    assert assembler.repo_root == temp_repo.resolve()
    assert assembler.max_tree_depth == 3
    assert assembler.max_commits == 10
    assert assembler.claude_md_path == temp_repo / "CLAUDE.md"


def test_initialization_no_claude_md(tmp_path, caplog):
    """Test initialization when CLAUDE.md doesn't exist."""
    assembler = ContextAssembler(repo_root=tmp_path)

    assert "CLAUDE.md not found" in caplog.text


def test_factory_function_default():
    """Test create_context_assembler with defaults."""
    with patch('agent_factory.scaffold.context_assembler.Path.cwd') as mock_cwd:
        mock_cwd.return_value = Path("/test")
        assembler = create_context_assembler()

        assert assembler.repo_root == Path("/test").resolve()
        assert assembler.max_tree_depth == 3
        assert assembler.max_commits == 10


def test_factory_function_custom():
    """Test create_context_assembler with custom parameters."""
    assembler = create_context_assembler(
        repo_root=Path("/custom"),
        max_tree_depth=5,
        max_commits=20
    )

    assert assembler.repo_root == Path("/custom").resolve()
    assert assembler.max_tree_depth == 5
    assert assembler.max_commits == 20


# CLAUDE.md Reading Tests

def test_read_claude_md_success(assembler):
    """Test reading CLAUDE.md successfully."""
    prompt = assembler._read_claude_md()

    assert "Test System Prompt" in prompt
    assert "You are a helpful assistant" in prompt
    assert "Follow these rules" in prompt


def test_read_claude_md_missing(tmp_path):
    """Test reading when CLAUDE.md doesn't exist."""
    assembler = ContextAssembler(repo_root=tmp_path)
    prompt = assembler._read_claude_md()

    assert prompt == "You are a helpful AI assistant helping implement tasks."


def test_read_claude_md_truncation(temp_repo):
    """Test CLAUDE.md reading truncates to 200 lines."""
    # Create large CLAUDE.md
    large_content = "# Header\n" + "\n".join([f"Line {i}" for i in range(300)])
    (temp_repo / "CLAUDE.md").write_text(large_content)

    assembler = ContextAssembler(repo_root=temp_repo)
    prompt = assembler._read_claude_md()

    # Should be truncated
    lines = prompt.split('\n')
    assert len(lines) <= 200


# File Tree Tests

def test_generate_file_tree_with_tree_command(assembler):
    """Test file tree generation using tree command."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout=".\n├── src\n│   └── main.py\n└── README.md"
        )

        tree = assembler._generate_file_tree()

        assert "src" in tree
        assert "main.py" in tree
        assert "README.md" in tree
        assert tree.startswith("```")
        assert tree.endswith("```")


def test_generate_file_tree_fallback(assembler):
    """Test fallback file tree when tree command unavailable."""
    with patch('subprocess.run', side_effect=FileNotFoundError):
        tree = assembler._generate_file_tree()

        assert "```" in tree
        assert "test_repo" in tree or "truncated" in tree


def test_fallback_file_tree(assembler):
    """Test fallback file tree generator directly."""
    tree = assembler._fallback_file_tree()

    assert "```" in tree
    assert tree.startswith("```")


def test_fallback_file_tree_excludes_dirs(temp_repo):
    """Test fallback excludes node_modules, __pycache__, etc."""
    # Create excluded directories
    (temp_repo / "node_modules").mkdir()
    (temp_repo / "node_modules" / "package.json").write_text("{}")
    (temp_repo / "__pycache__").mkdir()
    (temp_repo / ".git").mkdir()

    assembler = ContextAssembler(repo_root=temp_repo)
    tree = assembler._fallback_file_tree()

    assert "node_modules" not in tree
    assert "__pycache__" not in tree
    assert ".git" not in tree


# Git Commit Tests

def test_extract_git_commits_success(assembler):
    """Test extracting git commits successfully."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="abc123 (HEAD -> main) Latest commit\ndef456 Previous commit"
        )

        commits = assembler._extract_git_commits()

        assert "abc123" in commits
        assert "Latest commit" in commits
        assert "def456" in commits
        assert commits.startswith("```")


def test_extract_git_commits_failure(assembler):
    """Test git commits extraction when git fails."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=1)

        commits = assembler._extract_git_commits()

        assert commits == "Git history unavailable"


def test_extract_git_commits_not_installed(assembler):
    """Test git commits when git not installed."""
    with patch('subprocess.run', side_effect=FileNotFoundError):
        commits = assembler._extract_git_commits()

        assert commits == "Git history unavailable"


# Task Spec Formatting Tests

def test_format_task_spec_complete(assembler, sample_task):
    """Test formatting complete task spec."""
    spec = assembler._format_task_spec(sample_task)

    assert "task-42" in spec
    assert "Test Task" in spec
    assert "This is a test task" in spec
    assert "Criterion 1" in spec
    assert "Criterion 2" in spec
    assert "Criterion 3" in spec


def test_format_task_spec_minimal(assembler):
    """Test formatting minimal task spec."""
    minimal_task = {
        "id": "task-1",
        "title": "Minimal Task"
    }

    spec = assembler._format_task_spec(minimal_task)

    assert "task-1" in spec
    assert "Minimal Task" in spec
    assert "No description" in spec
    assert "None specified" in spec


def test_format_task_spec_no_criteria(assembler):
    """Test formatting task with no acceptance criteria."""
    task = {
        "id": "task-2",
        "title": "Task Without Criteria",
        "description": "Description here"
    }

    spec = assembler._format_task_spec(task)

    assert "None specified" in spec


# Complete Context Assembly Tests

def test_assemble_context_complete(assembler, sample_task):
    """Test complete context assembly."""
    with patch('subprocess.run') as mock_run:
        # Mock git log
        mock_run.return_value = Mock(
            returncode=0,
            stdout="abc123 Latest commit"
        )

        context = assembler.assemble_context(sample_task, "/path/to/worktree")

        # Check all sections present
        assert "# SCAFFOLD Task Execution Context" in context
        assert "## System Prompt" in context
        assert "## Repository Snapshot" in context
        assert "### File Tree" in context
        assert "### Recent Commits" in context
        assert "## Task Specification" in context
        assert "## Execution Environment" in context
        assert "## Instructions" in context

        # Check content
        assert "task-42" in context
        assert "Test Task" in context
        assert "/path/to/worktree" in context


def test_assemble_context_error_handling(assembler, sample_task):
    """Test context assembly error handling."""
    # Break the assembler by making CLAUDE.md unreadable
    with patch.object(assembler, '_read_claude_md', side_effect=Exception("Test error")):
        with pytest.raises(ContextAssemblerError, match="Context assembly failed"):
            assembler.assemble_context(sample_task, "/worktree")


def test_assemble_context_length(assembler, sample_task):
    """Test assembled context has reasonable length."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="abc123 commit")

        context = assembler.assemble_context(sample_task, "/worktree")

        # Should be substantial but not excessive
        assert len(context) > 100
        assert len(context) < 100000


# Integration Tests

def test_full_workflow(assembler, sample_task):
    """Test complete workflow: initialize → assemble → verify output."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="abc123 (HEAD -> main) Test commit"
        )

        # Assemble context
        context = assembler.assemble_context(sample_task, "/test/worktree")

        # Verify structure
        assert "# SCAFFOLD Task Execution Context" in context
        assert "Test System Prompt" in context  # From CLAUDE.md
        assert "task-42" in context
        assert "Test Task" in context
        assert "Criterion 1" in context
        assert "/test/worktree" in context


def test_multiple_tasks_same_assembler(assembler):
    """Test using same assembler for multiple tasks."""
    task1 = {"id": "task-1", "title": "First", "description": "First task"}
    task2 = {"id": "task-2", "title": "Second", "description": "Second task"}

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="abc123 commit")

        context1 = assembler.assemble_context(task1, "/worktree1")
        context2 = assembler.assemble_context(task2, "/worktree2")

        # Both should work
        assert "task-1" in context1
        assert "First task" in context1

        assert "task-2" in context2
        assert "Second task" in context2
