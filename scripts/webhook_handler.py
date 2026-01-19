#!/usr/bin/env python3
"""
GitHub Webhook Handler for Agent Factory

Receives GitHub webhook events (push, release, issue) and creates jobs
for the orchestrator to process.

Based on Complete GitHub Strategy:
- GitHub webhooks trigger lightweight events
- Write job to Supabase queue
- Orchestrator picks up and executes

Deployment:
- Run locally with ngrok tunnel
- Or deploy to VPS with CloudFlare Tunnel
- Configure GitHub webhook to POST to /webhook/github

Usage:
    python webhook_handler.py                 # Run on http://localhost:8000
    uvicorn webhook_handler:app --reload      # Development mode
    uvicorn webhook_handler:app --host 0.0.0.0 --port 8000  # Production

"""

import os
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment
load_dotenv()

from agent_factory.memory.storage import SupabaseMemoryStorage

# ============================================================================
# Configuration
# ============================================================================

# GitHub webhook secret (set in GitHub repo settings)
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("webhook_handler")

# FastAPI app
app = FastAPI(
    title="Agent Factory Webhook Handler",
    description="Receives GitHub webhooks and creates orchestrator jobs",
    version="1.0.0"
)

# Supabase storage
storage = SupabaseMemoryStorage()


# ============================================================================
# Models
# ============================================================================

class WebhookResponse(BaseModel):
    """Response model for webhook endpoint"""
    received: bool
    event_type: str
    job_created: Optional[str] = None
    message: str


# ============================================================================
# Webhook Verification
# ============================================================================

def verify_github_signature(payload_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Verify GitHub webhook signature.

    Args:
        payload_body: Raw request body bytes
        signature_header: X-Hub-Signature-256 header value

    Returns:
        bool: True if signature is valid
    """
    if not GITHUB_WEBHOOK_SECRET:
        logger.warning("GITHUB_WEBHOOK_SECRET not set, skipping signature verification")
        return True  # Allow in development

    if not signature_header:
        logger.warning("No signature header provided")
        return False

    # Extract signature from header (format: "sha256=<signature>")
    try:
        hash_algorithm, signature = signature_header.split("=", 1)
    except ValueError:
        logger.warning(f"Invalid signature format: {signature_header}")
        return False

    if hash_algorithm != "sha256":
        logger.warning(f"Unsupported hash algorithm: {hash_algorithm}")
        return False

    # Compute expected signature
    mac = hmac.new(GITHUB_WEBHOOK_SECRET, msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()

    # Compare signatures (constant-time comparison to prevent timing attacks)
    return hmac.compare_digest(signature, expected_signature)


# ============================================================================
# Job Creation Logic
# ============================================================================

def create_job_from_push_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create orchestrator job from GitHub push event.

    Args:
        payload: GitHub push event payload

    Returns:
        Job record to insert into agent_jobs table
    """
    ref = payload.get("ref", "")
    commits = payload.get("commits", [])

    # Only process pushes to main branch
    if ref != "refs/heads/main":
        logger.info(f"Ignoring push to {ref} (not main)")
        return {}

    # Check commit messages for keywords
    commit_messages = [commit.get("message", "") for commit in commits]
    all_messages = " ".join(commit_messages).lower()

    # Determine job type based on commit content
    if "video" in all_messages or "script" in all_messages:
        job_type = "full_video_pipeline"
        priority = 3
    elif "atom" in all_messages or "knowledge" in all_messages:
        job_type = "sync_and_generate_content"
        priority = 5
    else:
        # Default: just sync and check for work
        job_type = "sync_and_generate_content"
        priority = 7

    return {
        "job_type": job_type,
        "payload": {
            "trigger": "github_push",
            "ref": ref,
            "commits": len(commits),
            "messages": commit_messages[:3]  # First 3 commit messages
        },
        "priority": priority
    }


def create_job_from_release_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create orchestrator job from GitHub release event.

    Args:
        payload: GitHub release event payload

    Returns:
        Job record to insert into agent_jobs table
    """
    action = payload.get("action")
    release = payload.get("release", {})
    tag_name = release.get("tag_name", "")

    if action != "published":
        logger.info(f"Ignoring release action: {action}")
        return {}

    # Release published → generate content and publish
    return {
        "job_type": "full_video_pipeline",
        "payload": {
            "trigger": "github_release",
            "tag": tag_name,
            "action": action
        },
        "priority": 1  # High priority
    }


def create_job_from_issue_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create orchestrator job from GitHub issue event.

    Args:
        payload: GitHub issue event payload

    Returns:
        Job record to insert into agent_jobs table
    """
    action = payload.get("action")
    issue = payload.get("issue", {})
    title = issue.get("title", "")
    labels = [label["name"] for label in issue.get("labels", [])]

    # Only process opened issues with specific labels
    if action != "opened":
        return {}

    if "agent-task" in labels:
        # Issue is a task for an agent
        return {
            "job_type": "manage_tasks",  # AI Chief of Staff processes this
            "payload": {
                "trigger": "github_issue",
                "issue_number": issue.get("number"),
                "title": title,
                "labels": labels
            },
            "priority": 5
        }

    return {}  # Ignore other issues


# ============================================================================
# Webhook Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Agent Factory Webhook Handler",
        "status": "operational",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check with Supabase connection test"""
    try:
        # Test Supabase connection
        storage.client.table("agent_status").select("agent_name").limit(1).execute()
        return {"status": "healthy", "supabase": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "supabase": f"error: {str(e)}"}


@app.post("/webhook/github", response_model=WebhookResponse)
async def handle_github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    Handle GitHub webhook events.

    Headers:
        X-GitHub-Event: Event type (push, release, issues, etc.)
        X-Hub-Signature-256: HMAC signature for verification

    Returns:
        WebhookResponse: Status and job ID if created
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature
    if not verify_github_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse JSON payload
    payload = await request.json()

    logger.info(f"Received GitHub {x_github_event} event")

    # Create job based on event type
    job_data = {}

    if x_github_event == "push":
        job_data = create_job_from_push_event(payload)
    elif x_github_event == "release":
        job_data = create_job_from_release_event(payload)
    elif x_github_event == "issues":
        job_data = create_job_from_issue_event(payload)
    else:
        logger.info(f"Unsupported event type: {x_github_event}")
        return WebhookResponse(
            received=True,
            event_type=x_github_event,
            message=f"Event {x_github_event} not configured for job creation"
        )

    # If no job needed, return early
    if not job_data:
        return WebhookResponse(
            received=True,
            event_type=x_github_event,
            message="Event received but no job created (filtered)"
        )

    # Insert job into database
    try:
        # Log webhook event (for audit trail)
        storage.client.table("webhook_events").insert({
            "source": "github",
            "event_type": x_github_event,
            "payload": payload,
            "processed": False,
            "received_at": datetime.now().isoformat()
        }).execute()

        # Create job
        result = storage.client.table("agent_jobs").insert(job_data).execute()

        job_id = result.data[0]["id"] if result.data else None

        logger.info(f"Created job {job_id} for {x_github_event} event")

        return WebhookResponse(
            received=True,
            event_type=x_github_event,
            job_created=job_id,
            message=f"Job created: {job_data['job_type']}"
        )

    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@app.post("/webhook/manual")
async def handle_manual_trigger(job_type: str, payload: Dict[str, Any] = None):
    """
    Manual webhook endpoint for testing or triggering jobs directly.

    Args:
        job_type: Type of job to create
        payload: Optional job payload

    Returns:
        WebhookResponse: Status and job ID
    """
    logger.info(f"Manual trigger: {job_type}")

    job_data = {
        "job_type": job_type,
        "payload": payload or {"trigger": "manual"},
        "priority": 5
    }

    try:
        # Log event
        storage.client.table("webhook_events").insert({
            "source": "manual",
            "event_type": job_type,
            "payload": payload or {},
            "processed": False,
            "received_at": datetime.now().isoformat()
        }).execute()

        # Create job
        result = storage.client.table("agent_jobs").insert(job_data).execute()

        job_id = result.data[0]["id"] if result.data else None

        logger.info(f"Created manual job {job_id}")

        return WebhookResponse(
            received=True,
            event_type=job_type,
            job_created=job_id,
            message="Manual job created"
        )

    except Exception as e:
        logger.error(f"Failed to create manual job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Check environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        exit(1)

    # Run server
    logger.info("=" * 70)
    logger.info("Starting Agent Factory Webhook Handler")
    logger.info("=" * 70)
    logger.info("Endpoints:")
    logger.info("  POST /webhook/github   - GitHub webhook receiver")
    logger.info("  POST /webhook/manual   - Manual job trigger")
    logger.info("  GET  /health           - Health check")
    logger.info("=" * 70)

    uvicorn.run(
        "webhook_handler:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
