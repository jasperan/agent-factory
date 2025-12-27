"""
RIVET Pro Quick Reference Module

Provides tier-specific command cheat sheets for users.
Can be shown after onboarding, skipping tutorial, or via /quickstart command.

Created: 2025-12-27
Phase: Telegram Onboarding (Phase 2/6)
"""


def get_quickstart_message(tier: str) -> str:
    """
    Generate tier-specific quick reference card.

    Args:
        tier: User's subscription tier (beta, pro, team)

    Returns:
        Formatted quick reference message
    """

    # Base commands available to all tiers
    base_commands = """📋 **Quick Reference Card**

**Ask Questions:**
Just type your question naturally, or use:
• `/troubleshoot <question>` - Get AI-powered answer

**Machine Library:**
• `/add_machine` - Add equipment to your library
• `/list_machines` - View your equipment
• `/upload_print` - Upload electrical schematics
• `/upload_manual` - Add manual to shared library

**Manuals & Search:**
• `/manual_search <query>` - Search manual library

**Help & Learning:**
• `/help` - Full command list
• `/tutorial` - Replay onboarding
• `/tour` - Feature tour"""

    # Pro-specific additions
    if tier == "pro":
        base_commands += """

**Pro Features:**
• `/book_expert` - Schedule expert call ($75/hr)
• Send photos for Field Eye analysis
• `/export_session` - Export as PDF
• `/my_sessions` - View troubleshooting history"""

    # Enterprise/Team-specific additions
    if tier == "team":
        base_commands += """

**Enterprise Features:**
• `/team_dashboard` - Team admin panel
• `/team_invite` - Invite team members
• `/team_library` - Shared equipment library
• `/work_order_create` - Create work order from troubleshooting"""

    return base_commands


def get_help_message(tier: str) -> str:
    """
    Generate comprehensive help message with all commands.

    Args:
        tier: User's subscription tier

    Returns:
        Full help documentation
    """

    help_text = f"""🤖 **RIVET Pro Help**

Your plan: **{tier.upper()}**

**━━━━━━━━━━━━━━━━━━━━**

**🔧 TROUBLESHOOTING**

Ask me questions naturally:
• "Motor running hot and tripping"
• "VFD showing E210 fault"
• "How do I troubleshoot a PLC?"

Or use commands:
• `/troubleshoot <question>` - Start troubleshooting session

**━━━━━━━━━━━━━━━━━━━━**

**📚 MACHINE LIBRARY**

Manage your equipment:
• `/add_machine` - Add equipment
• `/list_machines` - View your library
• `/edit_machine <id>` - Update details
• `/delete_machine <id>` - Remove equipment

**━━━━━━━━━━━━━━━━━━━━**

**📄 PRINTS & MANUALS**

Upload & search documentation:
• `/upload_print` - Upload electrical schematics
• `/upload_manual` - Add manual to shared library
• `/manual_search <query>` - Search manuals
• `/my_prints` - View uploaded schematics

**━━━━━━━━━━━━━━━━━━━━**

**💡 HELP & LEARNING**

Get help:
• `/help` - This message
• `/tutorial` - Replay onboarding
• `/tour` - Feature tour
• `/quickstart` - Quick reference card
• `/about` - About RIVET"""

    # Add pro-specific help
    if tier in ["pro", "team"]:
        help_text += """

**━━━━━━━━━━━━━━━━━━━━**

**🔥 PRO FEATURES**

Premium capabilities:
• `/book_expert` - Schedule expert call ($75/hr)
• `/export_session` - Export session as PDF
• `/my_sessions` - View troubleshooting history
• Send photos for Field Eye analysis"""

    # Add enterprise/team-specific help
    if tier == "team":
        help_text += """

**━━━━━━━━━━━━━━━━━━━━**

**🚀 ENTERPRISE FEATURES**

Team collaboration:
• `/team_dashboard` - Admin panel
• `/team_invite <email>` - Invite team member
• `/team_library` - Shared equipment library
• `/work_order_create` - Create work order
• `/work_order_list` - View team work orders
• `/pro_stats` - Team usage analytics"""

    # Add footer
    help_text += """

**━━━━━━━━━━━━━━━━━━━━**

**Need more help?**
Email: support@rivet.com
Docs: https://docs.rivet.com"""

    return help_text


def get_about_message() -> str:
    """
    Generate "About RIVET" message.

    Returns:
        About RIVET information
    """

    about_text = """🤖 **About RIVET**

**What is RIVET?**

RIVET is an AI-powered industrial troubleshooting assistant built for field technicians.

**Our Knowledge Base:**
• 1,964+ validated maintenance solutions
• Covering VFDs, PLCs, motors, sensors, and more
• Backed by official manuals and real-world experience

**How It Works:**

1️⃣ **You ask** - Type your troubleshooting question
2️⃣ **We analyze** - AI classifies equipment, fault codes, symptoms
3️⃣ **We search** - Query our validated knowledge base
4️⃣ **You get answers** - Step-by-step troubleshooting with citations

**Why Trust RIVET?**

✅ All answers cite official documentation
✅ Safety warnings included
✅ Connect with expert technicians for complex issues
✅ Built by technicians, for technicians

**Pricing Tiers:**

🆓 **Beta** - 5 questions/day (free during beta)
💼 **Pro** - Unlimited questions, Field Eye, PDF export ($29/mo)
🚀 **Enterprise** - Everything + team features ($499/mo)

**Contact:**
• Email: support@rivet.com
• Website: https://landing-zeta-plum.vercel.app
• Docs: https://docs.rivet.com

**━━━━━━━━━━━━━━━━━━━━**

Ready to start troubleshooting? Just ask me a question!"""

    return about_text


def get_tier_comparison() -> str:
    """
    Generate pricing tier comparison table.

    Returns:
        Tier comparison message
    """

    comparison = """💰 **RIVET Pricing Tiers**

**━━━━━━━━━━━━━━━━━━━━**

🆓 **BETA** - FREE (Limited Time)

✅ 5 questions/day
✅ AI-powered answers
✅ Community knowledge base
✅ Equipment library
✅ Manual search

**━━━━━━━━━━━━━━━━━━━━**

💼 **PRO** - $29/month

✅ **UNLIMITED questions**
✅ Field Eye (image analysis)
✅ PDF export of solutions
✅ Priority email support
✅ Advanced search filters
✅ Troubleshooting history

**━━━━━━━━━━━━━━━━━━━━**

🚀 **ENTERPRISE** - $499/month

✅ **Everything in Pro**
✅ Up to 10 team members
✅ Shared equipment library
✅ Work order management
✅ Admin dashboard
✅ Team analytics
✅ Phone support
✅ Dedicated account manager

**━━━━━━━━━━━━━━━━━━━━**

**Upgrade anytime:**
• `/upgrade` - Choose your plan

**Need custom pricing?**
Email: sales@rivet.com"""

    return comparison


def get_upgrade_prompt(tier: str, trigger: str = "question_limit") -> str:
    """
    Generate upgrade prompt message based on trigger.

    Args:
        tier: User's current tier
        trigger: Why upgrade prompt is shown (question_limit, feature_locked, etc.)

    Returns:
        Upgrade prompt message
    """

    if trigger == "question_limit":
        message = """⚠️ **Daily Question Limit Reached**

You've used all 5 questions for today (Beta plan).

**Upgrade to Pro for:**
✅ **UNLIMITED questions**
✅ Field Eye image analysis
✅ PDF export of solutions
✅ Priority support

**Only $29/month** - Cancel anytime

Click `/upgrade` to unlock unlimited troubleshooting!"""

    elif trigger == "field_eye":
        message = """🔒 **Pro Feature: Field Eye**

Image analysis is available on Pro and Enterprise plans.

**Upgrade to Pro for:**
✅ Field Eye image analysis
✅ UNLIMITED questions
✅ PDF export
✅ Priority support

**Only $29/month**

Click `/upgrade` to unlock Field Eye!"""

    elif trigger == "pdf_export":
        message = """🔒 **Pro Feature: PDF Export**

Session export is available on Pro and Enterprise plans.

**Upgrade to Pro for:**
✅ PDF export of sessions
✅ Field Eye image analysis
✅ UNLIMITED questions
✅ Priority support

**Only $29/month**

Click `/upgrade` to unlock PDF export!"""

    elif trigger == "team_features":
        message = """🔒 **Enterprise Feature: Team Management**

Team features are available on Enterprise plan.

**Upgrade to Enterprise for:**
✅ Up to 10 team members
✅ Shared equipment library
✅ Work order management
✅ Admin dashboard
✅ Phone support

**Only $499/month**

Contact sales@rivet.com for Enterprise access!"""

    else:
        # Generic upgrade prompt
        message = """💼 **Upgrade to RIVET Pro**

Get unlimited troubleshooting with Pro!

**Pro Features:**
✅ UNLIMITED questions
✅ Field Eye image analysis
✅ PDF export of solutions
✅ Priority email support
✅ Advanced search filters

**Only $29/month** - Cancel anytime

Click `/upgrade` to get started!"""

    return message
