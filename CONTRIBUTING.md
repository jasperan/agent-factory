# Contributing to Agent Factory

Thank you for your interest in contributing to Agent Factory! This document provides guidelines and information for contributors.

---

## 🎯 Project Vision

Agent Factory is building the **orchestration engine for autonomous content production systems** that power:
- **PLC Tutor / Industrial Skills Hub** - AI-powered education with 24/7 YouTube content production
- **RIVET** - Industrial maintenance knowledge platform with validated troubleshooting

We're creating autonomous agent systems that create, distribute, and monetize educational content while building the largest validated knowledge base in industrial automation.

**See:** [README.md](README.md) for complete vision and [docs/TRIUNE_STRATEGY.md](docs/TRIUNE_STRATEGY.md) for detailed strategy.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10 or 3.11** (required)
- **Poetry** for dependency management
- **Git** for version control
- **Familiarity with:**
  - Pydantic v2 (data validation)
  - LangChain (agent orchestration)
  - Supabase + pgvector (if working on memory/storage)

### Development Setup

```bash
# 1. Fork the repository
# Visit https://github.com/your-username/agent-factory
# Click "Fork" button

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/agent-factory.git
cd agent-factory

# 3. Add upstream remote
git remote add upstream https://github.com/original-username/agent-factory.git

# 4. Install dependencies
poetry install --with dev

# 5. Copy environment template
cp .env.example .env

# 6. Add required API keys to .env
# (See README.md for required keys)

# 7. Run tests to verify setup
poetry run pytest
poetry run python test_models.py
```

---

## 🛠️ Development Workflow

### Git Worktree Pattern (REQUIRED)

Agent Factory uses **git worktrees** to enable multiple agents to work on the codebase simultaneously without conflicts.

**❌ Don't:** Work directly in the main directory (pre-commit hook will block commits)

**✅ Do:** Create a worktree for each feature/bug

```bash
# Create worktree for your feature
git worktree add ../agent-factory-feature-name -b feature-name

# Work in the worktree
cd ../agent-factory-feature-name

# Make changes, commit, push
git add .
git commit -m "feat: add amazing feature"
git push origin feature-name

# Clean up after PR is merged
cd ../agent-factory
git worktree remove ../agent-factory-feature-name
```

**See:** [docs/GIT_WORKTREE_GUIDE.md](docs/GIT_WORKTREE_GUIDE.md) for complete guide.

---

## 📝 Contribution Guidelines

### What to Contribute

**High-Priority Areas (Week 1-12):**
1. **Agent Implementations** (Issues #47, #48, etc.)
   - Research Agent (web scraping, YouTube transcripts, PDFs)
   - Scriptwriter Agent (atom → engaging video scripts)
   - Voice Production Agent (ElevenLabs integration)
   - Video Assembly Agent (MoviePy + FFmpeg)
   - And 14 more agents (see [docs/AGENT_ORGANIZATION.md](docs/AGENT_ORGANIZATION.md))

2. **Knowledge Atoms** (Issue #45)
   - Electrical fundamentals (voltage, current, Ohm's Law)
   - PLC basics (scan cycle, ladder logic, timers)
   - Industrial maintenance troubleshooting

3. **Testing & Documentation**
   - Test suites for agents
   - Integration tests (end-to-end pipelines)
   - Documentation improvements

4. **Infrastructure**
   - Supabase schema optimizations
   - Vector search performance
   - Agent communication protocol

**Future Areas (Month 4+):**
- RIVET vertical (industrial maintenance)
- Multi-platform distribution (TikTok, Instagram APIs)
- B2B features (corporate training, white-label)
- Analytics dashboard

### What NOT to Contribute (Yet)

- Major architectural changes (discuss in Issues first)
- Breaking changes to data models (needs coordination)
- Features outside current roadmap (see [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md))

---

## 🔒 Security Requirements

Agent Factory is built with **enterprise-grade security** from inception.

### Security Checklist (Before Every PR)

**Before Writing Code:**
- [ ] Does this handle user input? → Validate + sanitize
- [ ] Does this touch data? → Encrypt if sensitive + log access
- [ ] Does this expose functionality? → Add auth + rate limits
- [ ] Does this generate output? → Filter PII + validate safety
- [ ] Could an agent abuse this? → Add monitoring + circuit breakers

**Before Marking PR Ready:**
- [ ] Security implications documented in PR description
- [ ] Audit logging implemented (who did what, when)
- [ ] Error messages don't leak sensitive data
- [ ] Rate limits exist (if user-facing)
- [ ] Input validation with allow-lists (not block-lists)

**See:** [docs/SECURITY_STANDARDS.md](docs/SECURITY_STANDARDS.md) for complete guidelines.

---

## 📋 Code Standards

### Python Style

- **PEP 8** compliant (use `black` formatter)
- **Type hints** on all functions
- **Docstrings** for all public functions/classes (Google style)
- **ASCII-only output** (Windows compatibility)

```python
def process_atom(atom: PLCAtom, validate: bool = True) -> Dict[str, Any]:
    """
    Process a PLC knowledge atom and return metadata.

    Args:
        atom: PLCAtom to process
        validate: Whether to run validation (default: True)

    Returns:
        Dictionary containing processed metadata

    Raises:
        ValidationError: If atom validation fails
    """
    if validate:
        validate_atom_prerequisites(atom)

    return {
        "id": atom.id,
        "title": atom.title,
        "difficulty": atom.educational_level
    }
```

### Pydantic Models

- **Pydantic v2** syntax
- **Field validators** for complex constraints
- **Examples** in `Config.json_schema_extra`
- **Type safety** everywhere

```python
from pydantic import BaseModel, Field, field_validator

class MyModel(BaseModel):
    """Clear docstring explaining the model"""

    name: str = Field(..., min_length=3, max_length=100, description="Human-readable name")
    count: int = Field(ge=0, le=1000, description="Valid count range")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Example Name",
                "count": 42
            }
        }
```

### Testing

- **Pytest** for all tests
- **Test coverage > 80%** for new code
- **Unit tests** for individual functions
- **Integration tests** for agent pipelines
- **Fixtures** for reusable test data

```python
import pytest
from core.models import PLCAtom, EducationalLevel

@pytest.fixture
def sample_plc_atom():
    """Fixture providing a sample PLC atom for testing"""
    return PLCAtom(
        id="test:plc:sample",
        title="Test Atom",
        description="A test atom for unit tests",
        domain="plc",
        educational_level=EducationalLevel.INTRO,
        learning_resource_type="example",
        typical_learning_time_minutes=10
    )

def test_plc_atom_validation(sample_plc_atom):
    """Test PLC atom validation logic"""
    assert sample_plc_atom.id.startswith("test:")
    assert sample_plc_atom.educational_level == EducationalLevel.INTRO
    assert sample_plc_atom.typical_learning_time_minutes == 10
```

---

## 🔀 Pull Request Process

### 1. Create Feature Branch

```bash
# Create worktree for feature
git worktree add ../agent-factory-my-feature -b feature/my-feature

# Work in worktree
cd ../agent-factory-my-feature
```

### 2. Implement Feature

- Follow code standards (above)
- Write tests (coverage > 80%)
- Update documentation (README, CLAUDE.md, TASK.md if needed)
- Follow security checklist

### 3. Commit with Conventional Commits

```bash
# Format: <type>: <description>

# Types:
feat: Add new feature
fix: Bug fix
docs: Documentation changes
test: Add or update tests
refactor: Code refactoring
chore: Maintenance tasks
perf: Performance improvements
style: Code style changes (formatting, no logic change)

# Examples:
git commit -m "feat: Add Research Agent web scraping (Issue #47)"
git commit -m "fix: Handle missing atom prerequisites gracefully"
git commit -m "docs: Update AGENT_ORGANIZATION with Research Agent specs"
git commit -m "test: Add unit tests for PLCAtom validation"
```

### 4. Push & Create PR

```bash
# Push to your fork
git push origin feature/my-feature

# Create PR on GitHub
# Visit: https://github.com/YOUR_USERNAME/agent-factory
# Click "New Pull Request"
```

### 5. PR Template

```markdown
## Description
Clear description of what this PR does and why.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to break)
- [ ] Documentation update

## Related Issues
Fixes #<issue_number>
Relates to #<issue_number>

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing (`poetry run pytest`)
- [ ] Models validated (`poetry run python test_models.py`)

## Security Checklist
- [ ] Input validation implemented
- [ ] Sensitive data encrypted/logged appropriately
- [ ] Error messages don't leak sensitive data
- [ ] Rate limits added (if applicable)
- [ ] Audit logging implemented (if applicable)

## Documentation
- [ ] Code comments added/updated
- [ ] README.md updated (if needed)
- [ ] CLAUDE.md updated (if needed)
- [ ] TASK.md updated (if needed)
- [ ] Docstrings added for public functions

## Screenshots (if applicable)
Attach screenshots/videos showing the feature in action.
```

### 6. Code Review

- Maintainers will review within 2-3 business days
- Address feedback promptly
- Be open to suggestions
- Squash commits if requested

### 7. Merge

Once approved:
- PR will be merged by maintainer
- Delete your feature branch
- Clean up worktree

```bash
cd ../agent-factory
git worktree remove ../agent-factory-my-feature
git branch -d feature/my-feature
```

---

## 🐛 Bug Reports

### Before Submitting

1. **Search existing issues** - Your bug might already be reported
2. **Reproduce the bug** - Ensure it's consistent
3. **Check TASK.md** - It might be a known issue

### Bug Report Template

```markdown
## Bug Description
Clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Run command '...'
3. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., Windows 11, macOS 14, Ubuntu 22.04]
- Python version: [e.g., 3.10.8]
- Poetry version: [e.g., 2.0.0]
- Relevant package versions: [e.g., pydantic 2.5.0]

## Error Messages
```
Paste full error message/traceback here
```

## Additional Context
Any other context about the problem (screenshots, logs, etc.)

## Possible Solution (optional)
If you have ideas on how to fix it.
```

---

## 💡 Feature Requests

### Before Submitting

1. **Check roadmap** - See [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md)
2. **Search existing issues** - Feature might already be requested
3. **Read strategy docs** - Understand project direction

### Feature Request Template

```markdown
## Feature Description
Clear and concise description of the feature.

## Problem It Solves
What problem does this feature solve? Why is it needed?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other approaches you've thought about.

## Related Agents/Docs
Which agents would implement this? (See docs/AGENT_ORGANIZATION.md)

## Priority
- [ ] Critical (blocks current work)
- [ ] High (needed for upcoming milestone)
- [ ] Medium (nice to have soon)
- [ ] Low (future enhancement)

## Additional Context
Any other context, screenshots, examples, etc.
```

---

## 🤖 For AI Agents

If you're an AI agent contributing to this project:

### Required Reading
- [CLAUDE.md](CLAUDE.md) - Complete project context
- [TASK.md](TASK.md) - Current tasks and priorities
- [docs/TRIUNE_STRATEGY.md](docs/TRIUNE_STRATEGY.md) - Master strategy
- [docs/AGENT_ORGANIZATION.md](docs/AGENT_ORGANIZATION.md) - 18-agent system

### Special Considerations
- **Always use git worktrees** (pre-commit hook enforces this)
- **Check TASK.md first** before starting work
- **Update documentation** as you build (README, CLAUDE.md, TASK.md)
- **Follow security checklist** (docs/SECURITY_STANDARDS.md)
- **Use TodoWrite tool** to track progress (if available)
- **Commit frequently** with clear messages
- **Ask before refactoring** existing working code

---

## 📞 Getting Help

- **Documentation:** Check [README.md](README.md) and [docs/](docs/) first
- **GitHub Issues:** [Search existing issues](https://github.com/your-username/agent-factory/issues)
- **GitHub Discussions:** [Ask questions](https://github.com/your-username/agent-factory/discussions)
- **Email:** your-email@example.com (for sensitive issues)

---

## 📜 License

By contributing to Agent Factory, you agree that your contributions will be licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Thank you for contributing to Agent Factory! Your work helps build autonomous systems that democratize education and knowledge in industrial automation.

**Contributors:**
- See [CONTRIBUTORS.md](CONTRIBUTORS.md) for full list (coming soon)
- All contributors will be credited in releases

---

## 📊 Contribution Statistics

Check [GitHub Insights](https://github.com/your-username/agent-factory/graphs/contributors) for:
- Top contributors
- Contribution activity
- Code frequency
- Commit history

---

**"The best way to predict the future is to build it autonomously—together."**
