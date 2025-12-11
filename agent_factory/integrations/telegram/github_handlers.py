"""
Telegram bot handlers for GitHub issue automation.

Allows solving GitHub issues directly from Telegram using OpenHands + Ollama.

Commands:
- /solve-issue <number> - Solve specific GitHub issue
- /list-issues [label] - List open issues (optional label filter)

Example:
    User: /solve-issue 52
    Bot: [Fetches, solves, asks for approval via inline buttons]
    User: [Clicks Approve]
    Bot: [Commits and pushes, issue closes]
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

# Import GitHub issue solver functions
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Store repo path for git operations
REPO_PATH = str(project_root)

from solve_github_issues import (
    create_task_from_issue,
    check_gh_cli
)
from agent_factory.core.agent_factory import AgentFactory


# =============================================================================
# GitHub CLI Functions (with proper cwd)
# =============================================================================

import subprocess
import json

def get_issue(issue_number: int) -> Optional[Dict]:
    """Fetch issue from GitHub with proper repo context."""
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number),
             "--json", "title,body,labels,number,state"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10,
            cwd=REPO_PATH  # Use repo directory
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception:
        return None


def get_issues_by_label(label: str) -> list:
    """Fetch issues by label with proper repo context."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list",
             "--label", label,
             "--json", "title,body,labels,number,state"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10,
            cwd=REPO_PATH  # Use repo directory
        )
        if result.returncode != 0:
            return []
        return json.loads(result.stdout)
    except Exception:
        return []


def get_all_issues() -> list:
    """Fetch all open issues with proper repo context."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list",
             "--json", "title,body,labels,number,state"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10,
            cwd=REPO_PATH  # Use repo directory
        )
        if result.returncode != 0:
            return []
        return json.loads(result.stdout)
    except Exception:
        return []


# =============================================================================
# Helper Functions
# =============================================================================

async def send_progress(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send progress update to user."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message
    )


async def send_typing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show typing indicator."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )


def truncate_code(code: str, max_length: int = 3500) -> str:
    """
    Truncate code to fit in Telegram message (4096 char limit).

    Args:
        code: Code to truncate
        max_length: Max length (leave room for formatting)

    Returns:
        Truncated code with indicator if trimmed
    """
    if len(code) <= max_length:
        return code

    return code[:max_length] + f"\n\n... ({len(code) - max_length} more characters)"


# =============================================================================
# Command Handlers
# =============================================================================

async def solve_issue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /solve-issue command.

    Usage:
        /solveissue 52

    Workflow:
        1. Parse issue number from command
        2. Fetch issue from GitHub
        3. Create OpenHands task
        4. Solve with FREE Ollama
        5. Send code preview to user
        6. Show approval buttons
        7. Wait for user decision
        8. Commit if approved

    Example:
        User: /solveissue 52
        Bot: 🔍 Fetching issue #52...
             📋 Issue: Add logging to auth module
             ⚙️ Solving...
             ✅ Done! Approve?
             [✅ Approve] [❌ Reject]
    """
    chat_id = update.effective_chat.id

    # Check GitHub CLI
    if not check_gh_cli():
        await update.message.reply_text(
            "❌ GitHub CLI not ready\n\n"
            "Requirements:\n"
            "1. Install: https://cli.github.com/\n"
            "2. Authenticate: `gh auth login`"
        )
        return

    # Parse issue number
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /solveissue <number>\n\n"
            "Example: /solveissue 52"
        )
        return

    try:
        issue_number = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid issue number: {context.args[0]}\n\n"
            "Must be a number, e.g., /solveissue 52"
        )
        return

    # Step 1: Fetch issue
    await send_progress(update, context, f"🔍 Fetching issue #{issue_number}...")
    await send_typing(update, context)

    issue = await asyncio.to_thread(get_issue, issue_number)

    if not issue:
        await update.message.reply_text(
            f"❌ Could not fetch issue #{issue_number}\n\n"
            "Make sure:\n"
            "- Issue number is correct\n"
            "- You're in a git repository\n"
            "- GitHub CLI is authenticated"
        )
        return

    if issue["state"] != "OPEN":
        await update.message.reply_text(
            f"⚠️ Issue #{issue_number} is {issue['state']}\n\n"
            "Only OPEN issues can be solved."
        )
        return

    # Show issue details
    labels = [l["name"] for l in issue.get("labels", [])]
    labels_text = ", ".join(labels) if labels else "None"

    await send_progress(
        update,
        context,
        f"📋 *Issue #{issue_number}*\n\n"
        f"*Title:* {issue['title']}\n"
        f"*Labels:* {labels_text}"
    )

    # Step 2: Create task
    await send_progress(update, context, "⚙️ Creating OpenHands task...")
    await send_typing(update, context)

    task = await asyncio.to_thread(create_task_from_issue, issue)

    # Step 3: Solve with OpenHands
    await send_progress(
        update,
        context,
        "🤖 Solving with OpenHands + FREE Ollama...\n"
        "⏱️ This may take 30-60 seconds..."
    )
    await send_typing(update, context)

    # Get or create OpenHands worker
    bot_instance = context.bot_data.get("bot_instance")
    if not bot_instance:
        await update.message.reply_text("❌ Bot not initialized")
        return

    try:
        factory = AgentFactory()
        worker = factory.create_openhands_agent(
            model="deepseek-coder:6.7b"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Failed to create OpenHands worker\n\n"
            f"Error: {e}\n\n"
            "Make sure Ollama is running with deepseek-coder:6.7b"
        )
        return

    # Run task
    import time
    start_time = time.time()

    try:
        result = await asyncio.to_thread(
            worker.run_task,
            task,
            timeout=300
        )
        elapsed = time.time() - start_time
    except Exception as e:
        await update.message.reply_text(
            f"❌ OpenHands failed\n\n"
            f"Error: {e}"
        )
        return

    if not result.success:
        await update.message.reply_text(
            f"❌ OpenHands could not solve issue\n\n"
            f"Message: {result.message}\n\n"
            "Try:\n"
            "- Simpler issue\n"
            "- More detailed issue description\n"
            "- Manual solving"
        )
        return

    # Success!
    await send_progress(
        update,
        context,
        f"✅ Solved in {elapsed:.1f}s\n"
        f"💰 Cost: $0.00 (FREE with Ollama!)"
    )

    # Step 4: Show generated code
    if result.code:
        code_preview = truncate_code(result.code)
        code_message = (
            f"📄 *Generated Code:*\n\n"
            f"```python\n{code_preview}\n```"
        )
    else:
        code_message = "📄 *Generated solution* (no code file created)"

    # Show approval keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Approve & Commit",
                callback_data=f"gh_approve_{issue_number}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"gh_reject_{issue_number}"
            )
        ]
    ]

    # Store result in context for callback
    if "pending_github_solutions" not in context.bot_data:
        context.bot_data["pending_github_solutions"] = {}

    context.bot_data["pending_github_solutions"][f"{chat_id}_{issue_number}"] = {
        "issue": issue,
        "result": result,
        "task": task
    }

    await update.message.reply_text(
        code_message + "\n\n*Approve this solution?*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def list_issues_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /list-issues command.

    Usage:
        /listissues           # List all open issues
        /listissues bug       # List issues with "bug" label
        /listissues agent-task

    Example:
        User: /listissues bug
        Bot: 📋 Open issues with label 'bug':

             #52 - Authentication fails for special chars
             #47 - Memory leak in session manager
             #43 - Error handling breaks on timeout

             Use /solve-issue <number> to solve one
    """
    # Check GitHub CLI
    if not check_gh_cli():
        await update.message.reply_text(
            "❌ GitHub CLI not ready\n\n"
            "Requirements:\n"
            "1. Install: https://cli.github.com/\n"
            "2. Authenticate: `gh auth login`"
        )
        return

    await send_typing(update, context)

    # Get label filter if provided
    label_filter = context.args[0] if context.args else None

    # Fetch issues
    if label_filter:
        await send_progress(update, context, f"🔍 Fetching issues with label '{label_filter}'...")
        issues = await asyncio.to_thread(get_issues_by_label, label_filter)
        header = f"📋 *Open issues with label '{label_filter}':*\n\n"
    else:
        await send_progress(update, context, "🔍 Fetching all open issues...")
        issues = await asyncio.to_thread(get_all_issues)
        header = "📋 *All open issues:*\n\n"

    if not issues:
        no_issues_msg = (
            f"No open issues found"
            + (f" with label '{label_filter}'" if label_filter else "")
        )
        await update.message.reply_text(no_issues_msg)
        return

    # Format issues list
    issues_text = header

    for i, issue in enumerate(issues[:20]):  # Limit to 20 to avoid message size limit
        issue_num = issue["number"]
        title = issue["title"]

        # Truncate title if too long
        if len(title) > 60:
            title = title[:60] + "..."

        issues_text += f"*#{issue_num}* - {title}\n"

    if len(issues) > 20:
        issues_text += f"\n... and {len(issues) - 20} more\n"

    issues_text += f"\n💡 Use `/solveissue <number>` to solve one"

    await update.message.reply_text(
        issues_text,
        parse_mode="Markdown"
    )


# =============================================================================
# Callback Handlers
# =============================================================================

async def github_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle approval/rejection callbacks for GitHub issue solutions.

    Called when user clicks [Approve] or [Reject] buttons.

    If approved:
        1. Commit solution
        2. Push to GitHub
        3. Issue auto-closes

    If rejected:
        1. Discard solution
        2. Notify user
    """
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    callback_data = query.data

    # Parse callback data: gh_approve_52 or gh_reject_52
    if not callback_data.startswith("gh_"):
        return  # Not a GitHub callback

    parts = callback_data.split("_")
    if len(parts) != 3:
        await query.edit_message_text("❌ Invalid callback data")
        return

    action = parts[1]  # "approve" or "reject"
    issue_number = int(parts[2])

    # Get stored solution
    solution_key = f"{chat_id}_{issue_number}"
    pending_solutions = context.bot_data.get("pending_github_solutions", {})

    if solution_key not in pending_solutions:
        await query.edit_message_text(
            "❌ Solution not found or expired\n\n"
            "Please run /solve-issue again"
        )
        return

    solution_data = pending_solutions[solution_key]
    issue = solution_data["issue"]
    result = solution_data["result"]

    if action == "reject":
        # User rejected
        del pending_solutions[solution_key]

        await query.edit_message_text(
            f"❌ *Rejected*\n\n"
            f"Solution for issue #{issue_number} discarded.\n\n"
            f"You can try again with `/solveissue {issue_number}`",
            parse_mode="Markdown"
        )
        return

    # User approved - commit and push
    await query.edit_message_text(
        f"✅ *Approved!*\n\n"
        f"Committing solution for issue #{issue_number}...",
        parse_mode="Markdown"
    )

    await send_typing(update, context)

    # Save code to file (if exists)
    if result.code:
        # Determine filename from issue or result
        filename = f"issue_{issue_number}_solution.py"
        filepath = Path(REPO_PATH) / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result.code)
        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Failed to save code: {e}"
            )
            return

    # Git commit
    try:
        import subprocess

        # Add file
        if result.code:
            subprocess.run(
                ["git", "add", filename],
                check=True,
                capture_output=True,
                encoding='utf-8',
                errors='ignore',
                cwd=REPO_PATH  # Run in repo directory
            )

        # Commit with closes #N message
        commit_message = f"feat: {issue['title']} (closes #{issue_number})"

        subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=REPO_PATH  # Run in repo directory
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text="📝 Committed!"
        )

        # Push
        subprocess.run(
            ["git", "push", "origin", "main"],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=REPO_PATH  # Run in repo directory
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🚀 Pushed to GitHub!\n\n"
                 f"✅ Issue #{issue_number} will auto-close.\n\n"
                 f"*Commit:* {commit_message}",
            parse_mode="Markdown"
        )

        # Clean up
        del pending_solutions[solution_key]

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') and e.stderr else str(e)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Git operation failed\n\n"
                 f"Error: {error_msg}\n\n"
                 f"You may need to commit manually."
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Unexpected error: {e}"
        )
