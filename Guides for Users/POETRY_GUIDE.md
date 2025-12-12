# Poetry 2.x Guide for Agent Factory

This guide explains the changes in Poetry 2.x and how to use it with Agent Factory.

## What Changed in Poetry 2.x?

Poetry 2.0+ introduced several breaking changes that affect how you interact with the tool. If you're familiar with older Poetry versions, here's what you need to know.

## Key Changes

### 1. `poetry sync` is Now Recommended

**Old Way (Poetry 1.x):**
```bash
poetry install
```

**New Way (Poetry 2.x):**
```bash
poetry sync
```

**Why?** `poetry sync` ensures your environment exactly matches `poetry.lock`, removing packages that aren't needed. It's more precise than `install`.

You can still use `poetry install`, but `sync` is the recommended approach.

### 2. `poetry shell` is Deprecated

**Old Way (Poetry 1.x):**
```bash
poetry shell
```

**New Way (Poetry 2.x) - Option 1: Use `poetry run`**
```bash
poetry run python your_script.py
poetry run pytest
poetry run black .
```

**New Way (Poetry 2.x) - Option 2: Manual Activation**
```bash
# Get the virtual environment path
poetry env info --path

# Activate on Unix/Mac
source $(poetry env info --path)/bin/activate

# Activate on Windows (PowerShell)
& "$(poetry env info --path)\Scripts\Activate.ps1"

# Activate on Windows (CMD)
$(poetry env info --path)\Scripts\activate.bat
```

**Why deprecated?** `poetry shell` had issues with nested shells and inconsistent behavior. It's now available as a separate plugin: `poetry-plugin-shell`.

### 3. `--no-dev` is Replaced

**Old Way (Poetry 1.x):**
```bash
poetry install --no-dev
```

**New Way (Poetry 2.x):**
```bash
poetry install --only main
# OR
poetry install --without dev
```

### 4. New `--all-groups` Option

Install all dependency groups (main + all optional groups):
```bash
poetry sync --all-groups
```

### 5. `package-mode` Configuration

Poetry 2.x introduced `package-mode` to distinguish between:
- **Libraries** (meant to be installed as packages)
- **Applications/Frameworks** (not meant to be installed)

**Agent Factory uses:**
```toml
[tool.poetry]
package-mode = false
```

This means Agent Factory is treated as an application, not a library package. You don't need `--no-root` anymore!

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `poetry sync` |
| Run Python script | `poetry run python script.py` |
| Run tests | `poetry run pytest` |
| Format code | `poetry run black .` |
| Add new package | `poetry add package-name` |
| Add dev package | `poetry add --group dev package-name` |
| Update dependencies | `poetry update` |
| Show environment path | `poetry env info --path` |
| List environments | `poetry env list` |
| Remove environment | `poetry env remove python` |

## Common Workflows

### First Time Setup
```bash
cd agent-factory
poetry sync
cp .env.example .env
# Edit .env with your API keys
poetry run python agent_factory/examples/demo.py
```

### Daily Development
```bash
# Run the demo
poetry run python agent_factory/examples/demo.py

# Run your own script
poetry run python my_agent.py

# Add a new dependency
poetry add requests

# Update all dependencies
poetry update
```

### Using an IDE (VS Code, PyCharm)

**VS Code:**
1. Get the Python interpreter path:
   ```bash
   poetry env info --path
   ```
2. In VS Code: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose or paste the path from step 1

**PyCharm:**
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Navigate to the path from `poetry env info --path`

## Troubleshooting

### "poetry: command not found"
Poetry is not in your PATH. Reinstall or add to PATH:
```bash
# Check if Poetry is installed
poetry --version

# If not, install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

### "No module named 'agent_factory'"
The virtual environment isn't active. Use `poetry run`:
```bash
poetry run python your_script.py
```

### Dependencies not updating
Try clearing the cache and re-syncing:
```bash
poetry cache clear pypi --all
poetry sync
```

### Multiple Python versions
Specify which Python to use:
```bash
poetry env use python3.11
poetry sync
```

## Migration from Poetry 1.x

If you have an existing project using Poetry 1.x:

1. **Update Poetry:**
   ```bash
   poetry self update
   ```

2. **Update your habits:**
   - Replace `poetry install` → `poetry sync`
   - Replace `poetry shell` → `poetry run <command>`
   - Replace `--no-dev` → `--without dev`

3. **Update documentation:**
   - Update README installation instructions
   - Update CI/CD pipelines
   - Inform team members

## Additional Resources

- [Official Poetry 2.0 Announcement](https://python-poetry.org/blog/announcing-poetry-2.0.0/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Poetry Commands Reference](https://python-poetry.org/docs/cli/)

## Why These Changes?

Poetry 2.x changes aim to:
- **Improve clarity**: `sync` is clearer than `install --sync`
- **Better separation**: Distinguish between libraries and applications
- **Reduce complexity**: Remove problematic features like `poetry shell`
- **Modern Python**: Better support for Python 3.9+

---

**Bottom Line:** Use `poetry sync` to install dependencies and `poetry run <command>` to run scripts. That's 90% of what you need!
