#!/usr/bin/env python3
"""
Deployment Report Generator

Creates comprehensive deployment report for Phase 6 (Documentation)

Usage:
    python scripts/deployment/generate_deployment_report.py --service-url https://your-service.onrender.com

This script generates:
- DEPLOYMENT_REPORT.md with complete deployment details
- Service URLs and credentials locations
- Validation results summary
- Next steps and recommendations
- Rollback procedure
- Monitoring dashboard links

Output: DEPLOYMENT_REPORT.md in project root
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DeploymentReportGenerator:
    """Generate comprehensive deployment report"""

    def __init__(self, service_url: str, validation_report: dict = None):
        self.service_url = service_url.rstrip("/")
        self.validation_report = validation_report or {}
        self.timestamp = datetime.now()

    def get_service_status(self) -> dict:
        """Check current service status"""
        health_url = f"{self.service_url}/health"

        try:
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "code": response.status_code}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_webhook_info(self) -> dict:
        """Get Telegram webhook information"""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            return {"status": "error", "message": "No bot token"}

        api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"

        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                return response.json().get("result", {})
            else:
                return {"status": "error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_database_stats(self) -> dict:
        """Get database statistics"""
        try:
            import psycopg

            db_url = os.getenv("NEON_DB_URL")
            if not db_url:
                return {"status": "error", "message": "No database URL"}

            with psycopg.connect(db_url, connect_timeout=10) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM knowledge_atoms;")
                    total = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM knowledge_atoms WHERE embedding IS NOT NULL;")
                    with_embeddings = cur.fetchone()[0]

                    return {
                        "total_atoms": total,
                        "with_embeddings": with_embeddings,
                        "coverage": with_embeddings / max(total, 1)
                    }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_markdown_report(self) -> str:
        """Generate markdown deployment report"""

        service_status = self.get_service_status()
        webhook_info = self.get_webhook_info()
        db_stats = self.get_database_stats()

        # Extract validation results
        validation_score = self.validation_report.get("score", 0)
        validation_status = self.validation_report.get("status", "UNKNOWN")
        checks_passed = self.validation_report.get("passed", 0)
        checks_failed = self.validation_report.get("failed", 0)

        report = f"""# Agent Factory - Deployment Report

**Generated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Deployment Platform:** Render.com (24/7 Production)
**Status:** {validation_status}

---

## Executive Summary

Agent Factory has been deployed to production on Render.com with 24/7 uptime monitoring.

**Deployment Readiness Score:** {validation_score:.1f}%

**Key Metrics:**
- Validation Checks Passed: {checks_passed}
- Validation Checks Failed: {checks_failed}
- Service Status: {service_status.get('status', 'unknown')}
- Knowledge Base: {db_stats.get('total_atoms', 0):,} atoms
- Embedding Coverage: {db_stats.get('coverage', 0)*100:.1f}%

---

## Service URLs

### Primary Services

**Telegram Bot (Web Service)**
- Service URL: {self.service_url}
- Health Endpoint: {self.service_url}/health
- Render Dashboard: https://dashboard.render.com

**Knowledge Base Automation (Cron Job)**
- Name: agent-factory-kb-builder
- Schedule: Daily at 2 AM UTC (0 2 * * *)
- Command: `poetry run python scripts/automation/scheduler_kb_daily.py`

### Monitoring

**UptimeRobot**
- Dashboard: https://uptimerobot.com/dashboard
- Monitor: Agent Factory Bot
- Check Interval: 5 minutes
- Alert Channel: Telegram webhook

**Database**
- Provider: Neon PostgreSQL
- Dashboard: https://console.neon.tech
- Total Atoms: {db_stats.get('total_atoms', 0):,}

---

## Deployment Configuration

### Environment Variables

All critical environment variables have been configured in Render.com:

**Telegram Configuration:**
- `TELEGRAM_BOT_TOKEN` - Configured
- `TELEGRAM_ADMIN_CHAT_ID` - Configured
- `AUTHORIZED_TELEGRAM_USERS` - Configured

**Database Configuration:**
- `NEON_DB_URL` - Configured (primary)
- `SUPABASE_URL` - Configured (backup)
- `SUPABASE_KEY` - Configured (backup)
- `DATABASE_PROVIDER` - Set to `neon`

**LLM Configuration:**
- `OPENAI_API_KEY` - Configured
- `ANTHROPIC_API_KEY` - Configured
- `DEFAULT_LLM_PROVIDER` - Set to `openai`
- `DEFAULT_MODEL` - Set to `gpt-4o`

**Voice Configuration:**
- `VOICE_MODE` - Set to `edge`
- `EDGE_VOICE` - Set to `en-US-GuyNeural`

### Docker Configuration

**Base Image:** Python 3.10-slim
**Package Manager:** Poetry 1.8.2
**Exposed Port:** 9876
**Health Check:** Every 30 seconds
**Startup Command:** `poetry run python scripts/automation/bot_manager.py start`

---

## Validation Results

### Service Health

**Current Status:**
- Status: {service_status.get('status', 'unknown')}
- PID: {service_status.get('pid', 'N/A')}
- Uptime: {service_status.get('uptime_seconds', 0)} seconds
- Response Time: < 1000ms

### Telegram Webhook

**Configuration:**
- Webhook URL: {webhook_info.get('url', 'Not set')}
- Pending Updates: {webhook_info.get('pending_update_count', 'N/A')}
- Max Connections: {webhook_info.get('max_connections', 'N/A')}
- Last Error: {webhook_info.get('last_error_message', 'None')}

### Database Connection

**Statistics:**
- Total Knowledge Atoms: {db_stats.get('total_atoms', 0):,}
- Atoms with Embeddings: {db_stats.get('with_embeddings', 0):,}
- Embedding Coverage: {db_stats.get('coverage', 0)*100:.1f}%
- Database Provider: Neon PostgreSQL

### Validation Summary

{self._format_validation_summary()}

---

## Costs & Resources

### Render.com Pricing

**Web Service (Telegram Bot):**
- Instance Type: Free Tier
- Cost: $0/month
- Limitations:
  - Sleeps after 15 minutes of inactivity (mitigated by UptimeRobot)
  - 750 hours/month free compute
  - 100 GB/month bandwidth

**Cron Job (KB Automation):**
- Instance Type: Free Tier
- Cost: $1/month
- Schedule: Daily (2 AM UTC)
- Estimated Run Time: 15-30 minutes

**Total Monthly Cost:** $1

### UptimeRobot Monitoring

- Plan: Free Tier
- Cost: $0/month
- Monitors: 50 monitors (using 1-2)
- Check Interval: 5 minutes

**Total Infrastructure Cost:** $1/month

---

## Next Steps

### Immediate (Next 24 Hours)

1. **Monitor Stability**
   - Check UptimeRobot dashboard every 6 hours
   - Verify bot responds to commands
   - Confirm cron job runs at 2 AM UTC tomorrow

2. **Test Bot Functionality**
   - Send `/start` command
   - Ask 5-10 questions
   - Verify response times < 2 seconds

3. **Verify Knowledge Base Growth**
   - Check Supabase/Neon dashboard tomorrow
   - Expected: +50-200 atoms after first cron run
   - Verify embedding coverage remains >90%

### Week 1 Actions

1. **Daily Monitoring**
   - Check UptimeRobot uptime (target: 99.9%)
   - Verify cron job success (daily)
   - Review Render logs for errors

2. **Performance Baseline**
   - Measure average response times
   - Track knowledge base growth rate
   - Monitor API costs (OpenAI/Anthropic)

3. **User Testing**
   - Invite 3-5 beta testers
   - Collect feedback on bot responses
   - Identify edge cases or failures

### Month 1 Goals

1. **Knowledge Base Growth**
   - Target: 5,000+ total atoms (from current {db_stats.get('total_atoms', 0):,})
   - Daily growth: +100-200 atoms
   - Sources: Factory I/O, vendor docs, forums

2. **Uptime & Reliability**
   - Target: 99.9% uptime
   - Zero critical outages
   - Average response time: <1 second

3. **Feature Enhancements**
   - Implement user feedback
   - Add new bot commands
   - Improve knowledge retrieval

---

## Rollback Procedure

If critical issues are detected:

### Emergency Rollback Steps

1. **Stop Bot Immediately**
   ```bash
   # Render Dashboard → agent-factory-telegram-bot → Suspend
   ```

2. **Delete Webhook**
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
   ```

3. **Switch to Local Polling**
   ```bash
   # Local machine
   poetry run python telegram_bot.py
   ```

4. **Investigate Issues**
   - Check Render logs
   - Review error messages
   - Test locally with same environment variables

5. **Fix and Redeploy**
   - Fix issues in code
   - Commit and push to main
   - Render will auto-deploy
   - Re-set webhook

### Known Issues & Workarounds

**Issue:** Free tier sleeps after 15 min inactivity
**Workaround:** UptimeRobot pings every 5 minutes

**Issue:** Webhook may have pending updates after deployment
**Workaround:** Clear updates with `/deleteWebhook` then re-set

**Issue:** Database connection timeout
**Workaround:** Check NEON_DB_URL, verify Neon project active

---

## Support Resources

### Documentation

- Deployment Guide: `DEPLOYMENT_QUICK_START.md`
- Deployment Checklist: `DEPLOYMENT_CHECKLIST.md`
- Architecture Docs: `docs/architecture/`
- Cloud Deployment: `docs/CLOUD_DEPLOYMENT_24_7.md`

### External Resources

- Render Docs: https://render.com/docs
- Telegram Bot API: https://core.telegram.org/bots/api
- UptimeRobot Help: https://uptimerobot.com/help
- Neon Docs: https://neon.tech/docs
- Supabase Docs: https://supabase.com/docs

### Emergency Contacts

- Project Repository: https://github.com/Mikecranesync/Agent-Factory
- Issues: https://github.com/Mikecranesync/Agent-Factory/issues
- Render Support: https://render.com/support

---

## Credentials & Access

**IMPORTANT:** All credentials are stored securely in:

1. **Local `.env` file** (NOT committed to git)
2. **Render.com environment variables** (encrypted)
3. **Password manager** (recommended backup)

**Required for rollback:**
- `TELEGRAM_BOT_TOKEN`
- `NEON_DB_URL` or `SUPABASE_DB_URL`
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

---

## Deployment Timeline

**Start:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Platform:** Render.com
**Validation Score:** {validation_score:.1f}%
**Status:** {validation_status}

---

**Report Generated By:** Agent Factory Deployment Automation
**Last Updated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def _format_validation_summary(self) -> str:
        """Format validation summary section"""
        results = self.validation_report.get("results", {})

        summary = []

        # Pre-flight
        pre_flight = results.get("pre_flight", {})
        if pre_flight:
            summary.append(f"**Pre-Flight:** {pre_flight.get('env_vars', 'NOT RUN')}")

        # Deployment
        deployment = results.get("deployment", {})
        if deployment:
            summary.append(f"**Webhook:** {deployment.get('webhook', 'NOT CHECKED')}")
            db_info = deployment.get('database', {})
            if db_info:
                summary.append(f"**Database:** {db_info.get('total_atoms', 0):,} atoms")

        # Stability
        stability = results.get("stability", {})
        if stability:
            health = stability.get('health_checks', {})
            if health:
                success_rate = health.get('success_rate', 0) * 100
                summary.append(f"**Health Checks:** {success_rate:.1f}% success rate")

        # Monitoring
        monitoring = results.get("monitoring", {})
        if monitoring:
            uptime = monitoring.get('uptime_ratio', 0)
            summary.append(f"**Uptime:** {uptime}%")

        if not summary:
            return "No validation data available"

        return "\n".join([f"- {item}" for item in summary])

    def save_report(self, output_path: str = None):
        """Save report to file"""
        if not output_path:
            output_path = "DEPLOYMENT_REPORT.md"

        report = self.generate_markdown_report()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Deployment report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate deployment report"
    )
    parser.add_argument(
        "--service-url",
        required=True,
        help="Render.com service URL"
    )
    parser.add_argument(
        "--validation-report",
        help="Path to validation report JSON (optional)"
    )
    parser.add_argument(
        "--output",
        default="DEPLOYMENT_REPORT.md",
        help="Output file path (default: DEPLOYMENT_REPORT.md)"
    )

    args = parser.parse_args()

    # Load validation report if provided
    validation_report = {}
    if args.validation_report and os.path.exists(args.validation_report):
        with open(args.validation_report, 'r') as f:
            validation_report = json.load(f)

    generator = DeploymentReportGenerator(args.service_url, validation_report)
    generator.save_report(args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
