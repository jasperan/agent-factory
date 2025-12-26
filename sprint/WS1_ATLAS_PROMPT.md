# WORKSTREAM 1: ATLAS CMMS DEPLOYMENT
# Computer 1, Tab 1
# Copy everything below this line into Claude Code CLI

You are WS-1 (Atlas CMMS) in a 6-instance parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context feels long (5+ tasks done), checkpoint immediately

## YOUR IDENTITY
- Workstream: WS-1
- Branch: atlas-cmms  
- Focus: Atlas CMMS deployment and API wrapper

## FIRST ACTIONS (Do These Now)
1. Check if worktree exists: `git worktree list`
2. If not, create it: `git worktree add ../rivet-atlas atlas-cmms` (create branch if needed)
3. cd into worktree
4. Read this entire prompt before starting

## EXISTING CODEBASE CONTEXT
Agent Factory already has significant infrastructure:
- `/agent_factory/rivet_pro/stripe_integration.py` - Stripe payments EXIST
- `/agent_factory/rivet_pro/database.py` - User DB EXIST
- `/agent_factory/rivet_pro/models.py` - Pydantic models EXIST
- `/agent_factory/integrations/telegram/` - Full Telegram bot EXISTS

You are NOT building from scratch. You're adding Atlas CMMS integration.

## YOUR TASKS (In Order)

### Task 1: Research Atlas CMMS API
```bash
# Fetch Atlas CMMS docs
curl -s https://raw.githubusercontent.com/Grashjs/cmms/main/README.md > /tmp/atlas_readme.md
```
- Understand their API structure
- Document key endpoints we need: work orders, assets, users
- Time: 30 min

### Task 2: Create Atlas Integration Module
Create: `/agent_factory/integrations/atlas/`
```
atlas/
├── __init__.py
├── client.py          # AtlasClient class
├── models.py          # Pydantic models for Atlas entities
├── config.py          # Atlas connection settings
└── sync.py            # Sync utilities
```

AtlasClient should have methods:
- `create_work_order(data: WorkOrderCreate) -> WorkOrder`
- `get_asset(asset_id: str) -> Asset`
- `upload_asset_file(asset_id: str, file: bytes) -> AssetFile`
- `create_user(email: str, tier: str) -> User`
- `list_work_orders(filters: dict) -> List[WorkOrder]`

### Task 3: Create Docker Compose for Atlas
Create: `/products/cmms/docker-compose.yml`
- Atlas backend
- Atlas frontend  
- PostgreSQL
- Configure for VPS deployment (72.60.175.144)

### Task 4: White-Label Configuration
Create: `/products/cmms/branding/`
- Logo placeholder
- Color scheme (can use existing brand if in repo)
- Environment config for custom domain

### Task 5: User Provisioning Endpoint
Add to AtlasClient:
```python
async def provision_user_from_stripe(
    self,
    email: str,
    stripe_customer_id: str,
    subscription_tier: str  # basic, pro, enterprise
) -> User:
    """Called by Stripe webhook after payment"""
```

This connects to existing `/agent_factory/rivet_pro/stripe_integration.py`

## COMMIT PROTOCOL
After EACH task:
```bash
# Generate system map
tree -L 3 --dirsfirst -I 'node_modules|__pycache__|.git|venv|.pytest_cache' > .tree_snapshot.txt

# Commit with map
git add -A
git commit -m "WS-1: [component] description

SYSTEM MAP:
$(cat .tree_snapshot.txt | head -50)"

git push origin atlas-cmms
```

## DEPENDENCIES YOU PROVIDE TO OTHER WORKSTREAMS
- WS-2 (Landing) needs: `AtlasClient.provision_user_from_stripe()`
- WS-3 (Telegram) needs: `AtlasClient.create_work_order()`
- WS-4 (Chat Print) needs: `AtlasClient.upload_asset_file()`

## UPDATE STATUS
After each task, create/update: `/sprint/STATUS_WS1.md`
```markdown
# WS-1 Status - Atlas CMMS
Last Updated: [timestamp]

## Completed
- [ ] Task 1: Research Atlas API
- [ ] Task 2: Create integration module
- [ ] Task 3: Docker compose
- [ ] Task 4: White-label config
- [ ] Task 5: User provisioning

## Current Focus
[what you're working on]

## Blockers
[any blockers]

## API Endpoints Ready
[list endpoints other workstreams can use]
```

## IF BLOCKED
1. Log blocker in STATUS_WS1.md
2. Move to next task
3. Check back in 30 min

## START NOW
Begin with Task 1. Research the Atlas API and document what we need.
