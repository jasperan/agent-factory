# WORKSTREAM 6: INTEGRATION TESTING + MERGE COORDINATION
# Computer 2, Tab 3
# Copy everything below this line into Claude Code CLI

You are WS-6 (Integration Testing) in a 6-instance parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context feels long (5+ tasks done), checkpoint immediately

## YOUR IDENTITY
- Workstream: WS-6
- Branch: integration-testing
- Focus: E2E tests, CI/CD, merge coordination

## FIRST ACTIONS (Do These Now)
1. Check if worktree exists: `git worktree list`
2. If not, create it: `git worktree add ../rivet-integration integration-testing`
3. cd into worktree
4. Read this entire prompt before starting

## YOUR SPECIAL ROLE
You are the ONLY workstream that:
- Pulls from all other branches
- Resolves merge conflicts
- Merges to main after tests pass
- Coordinates integration between components

## YOUR TASKS (In Order)

### Task 1: Set Up Test Infrastructure
Create: `/tests/` structure:
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_intent.py
│   ├── test_voice.py
│   ├── test_atlas.py
│   └── test_print.py
├── integration/
│   ├── test_voice_to_workorder.py
│   ├── test_print_to_atlas.py
│   └── test_payment_to_user.py
├── e2e/
│   └── test_full_flow.py
└── fixtures/
    ├── audio/              # Sample voice files
    ├── prints/             # Sample schematics
    └── mock_responses/     # API mocks
```

### Task 2: Create Test Fixtures
`/tests/conftest.py`:
```python
"""Shared test fixtures for Rivet tests."""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Test data paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
AUDIO_FIXTURES = FIXTURES_DIR / "audio"
PRINT_FIXTURES = FIXTURES_DIR / "prints"

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_atlas_client():
    """Mock Atlas CMMS client."""
    client = AsyncMock()
    client.create_work_order.return_value = {
        "id": "WO-TEST-001",
        "title": "Test Work Order",
        "status": "OPEN",
        "asset_id": "asset_001"
    }
    client.get_asset.return_value = {
        "id": "asset_001",
        "name": "Test Pump",
        "location": "Building A"
    }
    client.provision_user_from_stripe.return_value = {
        "id": "user_001",
        "email": "test@example.com",
        "tier": "pro"
    }
    return client

@pytest.fixture
def mock_whisper():
    """Mock Whisper transcription."""
    transcriber = AsyncMock()
    transcriber.transcribe.return_value = "The main pump is making a grinding noise"
    transcriber.transcribe_with_confidence.return_value = {
        "text": "The main pump is making a grinding noise",
        "language": "en",
        "confidence": 0.95
    }
    return transcriber

@pytest.fixture
def mock_claude_vision():
    """Mock Claude Vision for print analysis."""
    analyzer = AsyncMock()
    analyzer.analyze_image.return_value = {
        "text": "This schematic shows a motor control circuit with...",
        "components": ["relay", "contactor", "motor"],
        "confidence": 0.92
    }
    return analyzer

@pytest.fixture
def sample_voice_file():
    """Path to sample voice file."""
    return AUDIO_FIXTURES / "sample_work_order.ogg"

@pytest.fixture
def sample_schematic():
    """Path to sample schematic."""
    return PRINT_FIXTURES / "sample_schematic.png"

@pytest.fixture
def mock_telegram_update():
    """Mock Telegram update object."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.message.text = "Test message"
    update.message.voice = MagicMock()
    update.message.voice.file_id = "test_file_id"
    return update
```

### Task 3: Create E2E Test Scenarios
`/tests/e2e/test_full_flow.py`:
```python
"""End-to-end tests for complete user flows."""
import pytest
from unittest.mock import patch, AsyncMock

class TestVoiceToWorkOrder:
    """Test: Voice message → Transcription → Intent → Work Order."""
    
    @pytest.mark.asyncio
    async def test_voice_creates_work_order(
        self,
        mock_atlas_client,
        mock_whisper,
        mock_telegram_update
    ):
        """Complete flow: voice input creates work order in Atlas."""
        # Setup
        from agent_factory.integrations.telegram.voice.handler import VoiceHandler
        from agent_factory.rivet_pro.intent_detector import IntentDetector
        from agent_factory.core.orchestrator import RivetOrchestrator
        
        with patch('agent_factory.integrations.atlas.AtlasClient', return_value=mock_atlas_client):
            handler = VoiceHandler(
                intent_detector=IntentDetector(),
                orchestrator=RivetOrchestrator()
            )
            handler.transcriber = mock_whisper
            
            # Execute
            context = AsyncMock()
            context.bot.get_file.return_value = AsyncMock()
            
            await handler.handle_voice(mock_telegram_update, context)
            
            # Verify
            mock_atlas_client.create_work_order.assert_called_once()
            call_args = mock_atlas_client.create_work_order.call_args[0][0]
            assert "pump" in call_args["title"].lower() or "pump" in call_args.get("description", "").lower()

class TestPaymentToUser:
    """Test: Stripe payment → User provisioned in Atlas."""
    
    @pytest.mark.asyncio
    async def test_stripe_webhook_provisions_user(self, mock_atlas_client):
        """Stripe checkout.session.completed creates Atlas user."""
        from agent_factory.rivet_pro.stripe_integration import StripeManager
        
        # Simulate webhook payload
        webhook_data = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer_email": "newuser@example.com",
                    "metadata": {"tier": "pro"},
                    "customer": "cus_test123"
                }
            }
        }
        
        with patch('agent_factory.integrations.atlas.AtlasClient', return_value=mock_atlas_client):
            # Process webhook (your webhook handler here)
            # ...
            
            # Verify Atlas was called
            mock_atlas_client.provision_user_from_stripe.assert_called_once_with(
                email="newuser@example.com",
                stripe_customer_id="cus_test123",
                subscription_tier="pro"
            )

class TestPrintAnalysis:
    """Test: Print upload → Analysis → Q&A works."""
    
    @pytest.mark.asyncio
    async def test_print_qa_flow(self, mock_claude_vision, sample_schematic):
        """Upload print, ask question, get accurate answer."""
        from agent_factory.rivet_pro.print_analyzer import PrintAnalyzer
        
        with patch.object(PrintAnalyzer, '__init__', lambda x: None):
            analyzer = PrintAnalyzer()
            analyzer.provider = mock_claude_vision
            
            # Ask question
            answer = await analyzer.answer_question(
                sample_schematic,
                "What components are in this circuit?"
            )
            
            # Verify Claude was called with image
            mock_claude_vision.analyze_image.assert_called_once()
            assert "relay" in answer.lower() or "motor" in answer.lower()

class TestIntentClarification:
    """Test: Ambiguous input → Clarification → Resolution."""
    
    @pytest.mark.asyncio
    async def test_ambiguous_intent_asks_clarification(self):
        """Ambiguous equipment should trigger clarification."""
        from agent_factory.rivet_pro.intent_detector import IntentDetector
        from agent_factory.rivet_pro.clarifier import IntentClarifier
        
        detector = IntentDetector()
        clarifier = IntentClarifier()
        
        # Ambiguous input
        intent = await detector.detect("The pump is broken")
        
        if clarifier.needs_clarification(intent):
            clarification = clarifier.generate_clarification(intent)
            assert clarification is not None
            assert clarification.prompt  # Has a question to ask
```

### Task 4: Create CI/CD Pipeline
Create: `/.github/workflows/test.yml`:
```yaml
name: Rivet Tests

on:
  push:
    branches: [main, atlas-cmms, landing-stripe, telegram-voice, chat-with-print, intent-parser]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: rivet_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      
      - name: Install ffmpeg (for audio)
        run: sudo apt-get install -y ffmpeg
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/rivet_test
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          poetry run pytest tests/ -v --tb=short
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        if: always()

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff
      - run: ruff check .
```

### Task 5: Create Merge Protocol Script
Create: `/scripts/merge_branches.sh`:
```bash
#!/bin/bash
# Merge all workstream branches to integration-testing, then to main

set -e

echo "=== RIVET MERGE PROTOCOL ==="
echo "Pulling latest from all branches..."

BRANCHES=("atlas-cmms" "landing-stripe" "telegram-voice" "chat-with-print" "intent-parser")

# Ensure we're on integration-testing
git checkout integration-testing

# Pull each branch and merge
for branch in "${BRANCHES[@]}"; do
    echo ""
    echo "--- Merging $branch ---"
    
    # Fetch latest
    git fetch origin $branch
    
    # Try merge
    if git merge origin/$branch --no-edit; then
        echo "✅ $branch merged successfully"
    else
        echo "❌ CONFLICT in $branch"
        echo "Resolve conflicts, then run: git merge --continue"
        exit 1
    fi
done

echo ""
echo "=== All branches merged to integration-testing ==="
echo ""

# Run tests
echo "Running tests..."
if pytest tests/ -v; then
    echo ""
    echo "✅ All tests passed!"
    echo ""
    echo "Ready to merge to main:"
    echo "  git checkout main"
    echo "  git merge integration-testing"
    echo "  git push origin main"
else
    echo ""
    echo "❌ Tests failed. Fix before merging to main."
    exit 1
fi
```

### Task 6: Create Status Aggregator
Create: `/scripts/check_status.py`:
```python
#!/usr/bin/env python3
"""Aggregate status from all workstreams."""
from pathlib import Path
import re

STATUS_FILES = [
    "sprint/STATUS_WS1.md",
    "sprint/STATUS_WS2.md", 
    "sprint/STATUS_WS3.md",
    "sprint/STATUS_WS4.md",
    "sprint/STATUS_WS5.md",
    "sprint/STATUS_WS6.md",
]

def parse_status(filepath: Path) -> dict:
    """Parse a status file for completion info."""
    if not filepath.exists():
        return {"exists": False, "tasks": [], "blockers": []}
    
    content = filepath.read_text()
    
    # Find completed tasks
    completed = re.findall(r'\[x\]\s+(.+)', content, re.IGNORECASE)
    pending = re.findall(r'\[\s?\]\s+(.+)', content)
    
    # Find blockers
    blockers = []
    if "## Blockers" in content:
        blocker_section = content.split("## Blockers")[1].split("##")[0]
        blockers = [b.strip() for b in blocker_section.strip().split("\n") if b.strip() and b.strip() != "-"]
    
    return {
        "exists": True,
        "completed": completed,
        "pending": pending,
        "blockers": blockers,
        "progress": len(completed) / (len(completed) + len(pending)) if (completed or pending) else 0
    }

def main():
    print("=" * 60)
    print("RIVET MVP SPRINT STATUS")
    print("=" * 60)
    print()
    
    total_completed = 0
    total_pending = 0
    all_blockers = []
    
    for sf in STATUS_FILES:
        ws_name = sf.split("_")[1].replace(".md", "")
        status = parse_status(Path(sf))
        
        if not status["exists"]:
            print(f"⬜ {ws_name}: No status file yet")
            continue
        
        completed = len(status["completed"])
        pending = len(status["pending"])
        total = completed + pending
        pct = int(status["progress"] * 100)
        
        total_completed += completed
        total_pending += pending
        
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        print(f"{'✅' if pct == 100 else '🟡'} {ws_name}: [{bar}] {pct}% ({completed}/{total} tasks)")
        
        if status["blockers"]:
            all_blockers.extend([(ws_name, b) for b in status["blockers"]])
    
    print()
    print("-" * 60)
    overall = total_completed / (total_completed + total_pending) * 100 if (total_completed + total_pending) else 0
    print(f"OVERALL: {overall:.0f}% complete ({total_completed}/{total_completed + total_pending} tasks)")
    
    if all_blockers:
        print()
        print("🚨 ACTIVE BLOCKERS:")
        for ws, blocker in all_blockers:
            print(f"  - [{ws}] {blocker}")
    
    print()

if __name__ == "__main__":
    main()
```

### Task 7: Daily Integration Routine
Create: `/scripts/daily_integration.sh`:
```bash
#!/bin/bash
# Run this daily to sync all workstreams

echo "=== DAILY INTEGRATION CHECK ==="
date

# 1. Check status
echo ""
echo "--- STATUS ---"
python scripts/check_status.py

# 2. Fetch all branches
echo ""
echo "--- FETCHING BRANCHES ---"
git fetch --all

# 3. Check for conflicts (dry run)
echo ""
echo "--- CONFLICT CHECK ---"
git checkout integration-testing
for branch in atlas-cmms landing-stripe telegram-voice chat-with-print intent-parser; do
    echo -n "$branch: "
    if git merge --no-commit --no-ff origin/$branch 2>/dev/null; then
        echo "✅ clean"
        git merge --abort 2>/dev/null
    else
        echo "⚠️  has conflicts"
        git merge --abort 2>/dev/null
    fi
done

# 4. Run tests on current state
echo ""
echo "--- RUNNING TESTS ---"
pytest tests/ -v --tb=line || echo "⚠️  Some tests failing"

echo ""
echo "=== INTEGRATION CHECK COMPLETE ==="
```

## COMMIT PROTOCOL
After EACH task:
```bash
tree -L 3 --dirsfirst -I 'node_modules|__pycache__|.git|venv' > .tree_snapshot.txt
git add -A
git commit -m "WS-6: [component] description

SYSTEM MAP:
$(cat .tree_snapshot.txt | head -50)"
git push origin integration-testing
```

## YOUR SPECIAL RESPONSIBILITIES
1. Pull from all branches every 4 hours
2. Run tests after each pull
3. Log conflicts in `/sprint/MERGE_LOG.md`
4. Only YOU merge to main

## MERGE TO MAIN CRITERIA
Before merging to main, ALL must be true:
- [ ] All WS-* branches merged to integration-testing
- [ ] All unit tests pass
- [ ] All integration tests pass  
- [ ] All E2E tests pass
- [ ] No unresolved blockers
- [ ] Code reviewed (by you, looking at diffs)

## UPDATE STATUS
After each task, create/update: `/sprint/STATUS_WS6.md`

## START NOW
Begin with Task 1. Set up the test infrastructure.
