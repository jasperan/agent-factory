"""
KB Feedback Monitor - Track gap resolution feedback loop

Monitors KB gap → research → ingestion completion cycle.
Tracks which gaps were researched, which atoms were created,
and generates health reports.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class KBFeedbackMonitor:
    """
    Monitors KB gap → research → ingestion feedback loop.

    Tracks:
    - Which gaps triggered research
    - Which gaps completed ingestion
    - How many atoms were created
    - Gap closure times
    - KB health metrics
    """

    def __init__(self, db):
        """
        Initialize feedback monitor.

        Args:
            db: DatabaseManager instance
        """
        self.db = db
        logger.info("KBFeedbackMonitor initialized")

    def mark_ingestion_complete(
        self,
        gap_id: int,
        atoms_created: int
    ) -> bool:
        """
        Mark gap as resolved after ingestion completes.

        Args:
            gap_id: Gap ID that triggered ingestion
            atoms_created: Number of atoms created from ingestion

        Returns:
            True if successful, False otherwise
        """
        try:
            sql = """
                UPDATE gap_requests
                SET ingestion_completed = TRUE,
                    ingestion_completed_at = NOW(),
                    atoms_created = $1
                WHERE id = $2
            """
            self.db.execute_query(sql, (atoms_created, gap_id), fetch_mode="none")

            logger.info(
                f"Gap {gap_id} marked complete: {atoms_created} atoms created"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to mark gap {gap_id} complete: {e}")
            return False

    def get_weekly_health_report(self) -> Dict:
        """
        Generate weekly KB health report.

        Returns:
            Dictionary with:
            - total_gaps_detected: int
            - gaps_researched: int
            - gaps_completed: int
            - atoms_created: int
            - avg_completion_time_hours: float
            - top_equipment_gaps: List[(equipment, count)]
        """
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)

            # Summary stats
            summary_sql = """
                SELECT
                    COUNT(*) as total_gaps,
                    COUNT(*) FILTER (WHERE ingestion_started = TRUE) as researched,
                    COUNT(*) FILTER (WHERE ingestion_completed = TRUE) as completed,
                    SUM(atoms_created) as total_atoms,
                    AVG(EXTRACT(EPOCH FROM (ingestion_completed_at - ingestion_started_at))/3600) as avg_hours
                FROM gap_requests
                WHERE created_at >= $1
            """
            result = self.db.execute_query(summary_sql, (week_ago,))

            if not result:
                return {}

            row = result[0]

            # Top equipment gaps
            equipment_sql = """
                SELECT equipment_detected, COUNT(*) as gap_count
                FROM gap_requests
                WHERE created_at >= $1
                GROUP BY equipment_detected
                ORDER BY gap_count DESC
                LIMIT 10
            """
            equipment_result = self.db.execute_query(equipment_sql, (week_ago,))

            return {
                "period": "Last 7 days",
                "total_gaps_detected": row[0] or 0,
                "gaps_researched": row[1] or 0,
                "gaps_completed": row[2] or 0,
                "atoms_created": row[3] or 0,
                "avg_completion_time_hours": float(row[4]) if row[4] else None,
                "top_equipment_gaps": [
                    {"equipment": r[0], "count": r[1]}
                    for r in equipment_result
                ]
            }

        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")
            return {}

    def get_open_gaps(self, limit: int = 20) -> List[Dict]:
        """
        Get open gaps that haven't been completed.

        Returns:
            List of gap dictionaries sorted by priority
        """
        try:
            sql = """
                SELECT id, query_text, equipment_detected, priority_score,
                       request_count, created_at, ingestion_started,
                       ingestion_started_at, weakness_type
                FROM gap_requests
                WHERE ingestion_completed = FALSE
                ORDER BY priority_score DESC, request_count DESC
                LIMIT $1
            """
            result = self.db.execute_query(sql, (limit,))

            return [
                {
                    "gap_id": row[0],
                    "query": row[1],
                    "equipment": row[2],
                    "priority": row[3],
                    "request_count": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "ingestion_started": row[6],
                    "ingestion_started_at": row[7].isoformat() if row[7] else None,
                    "weakness_type": row[8]
                }
                for row in result
            ]

        except Exception as e:
            logger.error(f"Failed to get open gaps: {e}")
            return []

    def get_stuck_gaps(self, hours_threshold: int = 24) -> List[Dict]:
        """
        Get gaps that started ingestion but haven't completed.

        Useful for detecting stuck/failed ingestion jobs.

        Args:
            hours_threshold: Consider gaps stuck if started > N hours ago

        Returns:
            List of stuck gap dictionaries
        """
        try:
            sql = """
                SELECT id, query_text, equipment_detected, priority_score,
                       ingestion_started_at,
                       EXTRACT(EPOCH FROM (NOW() - ingestion_started_at))/3600 as hours_stuck
                FROM gap_requests
                WHERE ingestion_started = TRUE
                  AND ingestion_completed = FALSE
                  AND ingestion_started_at < NOW() - INTERVAL '%s hours'
                ORDER BY ingestion_started_at ASC
            """ % hours_threshold

            result = self.db.execute_query(sql)

            return [
                {
                    "gap_id": row[0],
                    "query": row[1],
                    "equipment": row[2],
                    "priority": row[3],
                    "started_at": row[4].isoformat() if row[4] else None,
                    "hours_stuck": float(row[5]) if row[5] else 0
                }
                for row in result
            ]

        except Exception as e:
            logger.error(f"Failed to get stuck gaps: {e}")
            return []

    def get_completion_rate(self, days: int = 7) -> Dict:
        """
        Get gap completion rate for last N days.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with completion metrics
        """
        try:
            lookback = datetime.utcnow() - timedelta(days=days)

            sql = """
                SELECT
                    COUNT(*) as total_gaps,
                    COUNT(*) FILTER (WHERE ingestion_completed = TRUE) as completed_gaps,
                    COUNT(*) FILTER (WHERE ingestion_started = TRUE AND ingestion_completed = FALSE) as in_progress_gaps,
                    COUNT(*) FILTER (WHERE ingestion_started = FALSE) as not_started_gaps
                FROM gap_requests
                WHERE created_at >= $1
            """
            result = self.db.execute_query(sql, (lookback,))

            if not result:
                return {}

            row = result[0]
            total = row[0] or 0
            completed = row[1] or 0

            completion_rate = (completed / total * 100) if total > 0 else 0.0

            return {
                "period_days": days,
                "total_gaps": total,
                "completed": completed,
                "in_progress": row[2] or 0,
                "not_started": row[3] or 0,
                "completion_rate": completion_rate
            }

        except Exception as e:
            logger.error(f"Failed to get completion rate: {e}")
            return {}

    def print_health_summary(self):
        """
        Print formatted health summary to console.

        Useful for monitoring scripts and dashboards.
        """
        print("\n" + "=" * 70)
        print("KB FEEDBACK LOOP HEALTH SUMMARY")
        print("=" * 70)

        # Weekly report
        weekly = self.get_weekly_health_report()
        if weekly:
            print(f"\n[{weekly['period']}]")
            print(f"  Total Gaps Detected: {weekly['total_gaps_detected']}")
            print(f"  Gaps Researched: {weekly['gaps_researched']}")
            print(f"  Gaps Completed: {weekly['gaps_completed']}")
            print(f"  Atoms Created: {weekly['atoms_created']}")

            if weekly['avg_completion_time_hours']:
                print(f"  Avg Completion Time: {weekly['avg_completion_time_hours']:.1f} hours")

            if weekly['top_equipment_gaps']:
                print("\n  Top Equipment Gaps:")
                for item in weekly['top_equipment_gaps'][:5]:
                    print(f"    - {item['equipment']}: {item['count']} gaps")

        # Completion rate
        completion = self.get_completion_rate(7)
        if completion:
            print(f"\n[Completion Rate - {completion['period_days']} days]")
            print(f"  Completion Rate: {completion['completion_rate']:.1f}%")
            print(f"  In Progress: {completion['in_progress']}")
            print(f"  Not Started: {completion['not_started']}")

        # Stuck gaps
        stuck = self.get_stuck_gaps(24)
        if stuck:
            print(f"\n[ALERT] {len(stuck)} Stuck Gaps (>24 hours):")
            for gap in stuck[:3]:
                print(f"  - Gap {gap['gap_id']}: {gap['equipment']} ({gap['hours_stuck']:.1f}h stuck)")

        # Open high-priority gaps
        open_gaps = self.get_open_gaps(5)
        high_priority_open = [g for g in open_gaps if g['priority'] >= 70]
        if high_priority_open:
            print(f"\n[High Priority Open Gaps]")
            for gap in high_priority_open:
                status = "In Progress" if gap['ingestion_started'] else "Not Started"
                print(f"  - Gap {gap['gap_id']}: {gap['equipment']} (priority={gap['priority']}, {status})")

        print("\n" + "=" * 70 + "\n")
