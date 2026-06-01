#!/usr/bin/env python3
"""
Session cleanup script for LearnPyByAI authentication system.

This script removes expired sessions and revoked sessions older than 30 days.
Should be run as a daily cron job.

Usage:
    python scripts/cleanup_sessions.py [--dry-run]

Options:
    --dry-run    Show what would be deleted without actually deleting
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.auth.models import Session as SessionModel
from src.database import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def cleanup_sessions(db: Session, dry_run: bool = False) -> dict:
    """
    Clean up expired and old revoked sessions.

    Args:
        db: Database session
        dry_run: If True, only count sessions without deleting

    Returns:
        Dictionary with cleanup statistics
    """
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # Find sessions to delete:
    # 1. Expired sessions (expires_at < now)
    # 2. Revoked sessions older than 30 days (revoked_at < 30 days ago)
    sessions_to_delete = (
        db.query(SessionModel)
        .filter(
            or_(
                SessionModel.expires_at < now,
                and_(
                    SessionModel.revoked_at.isnot(None),
                    SessionModel.revoked_at < thirty_days_ago,
                ),
            )
        )
        .all()
    )

    expired_count = sum(1 for s in sessions_to_delete if s.expires_at < now and s.revoked_at is None)
    revoked_count = sum(1 for s in sessions_to_delete if s.revoked_at is not None)
    total_count = len(sessions_to_delete)

    stats = {
        "expired_sessions": expired_count,
        "old_revoked_sessions": revoked_count,
        "total_deleted": total_count,
        "dry_run": dry_run,
    }

    if dry_run:
        logger.info(f"[DRY RUN] Would delete {total_count} sessions:")
        logger.info(f"  - {expired_count} expired sessions")
        logger.info(f"  - {revoked_count} old revoked sessions (>30 days)")
        return stats

    # Delete sessions
    if total_count > 0:
        for session in sessions_to_delete:
            db.delete(session)
        db.commit()
        logger.info(f"Deleted {total_count} sessions:")
        logger.info(f"  - {expired_count} expired sessions")
        logger.info(f"  - {revoked_count} old revoked sessions (>30 days)")
    else:
        logger.info("No sessions to clean up")

    return stats


def get_session_statistics(db: Session) -> dict:
    """
    Get current session statistics.

    Args:
        db: Database session

    Returns:
        Dictionary with session statistics
    """
    now = datetime.now(timezone.utc)

    total_sessions = db.query(SessionModel).count()
    active_sessions = (
        db.query(SessionModel)
        .filter(
            and_(
                SessionModel.expires_at > now,
                SessionModel.revoked_at.is_(None),
            )
        )
        .count()
    )
    expired_sessions = (
        db.query(SessionModel)
        .filter(
            and_(
                SessionModel.expires_at < now,
                SessionModel.revoked_at.is_(None),
            )
        )
        .count()
    )
    revoked_sessions = db.query(SessionModel).filter(SessionModel.revoked_at.isnot(None)).count()

    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "expired_sessions": expired_sessions,
        "revoked_sessions": revoked_sessions,
    }


def main():
    """Main entry point for the cleanup script."""
    parser = argparse.ArgumentParser(
        description="Clean up expired and old revoked sessions from the database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show session statistics before and after cleanup",
    )
    args = parser.parse_args()

    logger.info("Starting session cleanup script")

    db = SessionLocal()
    try:
        # Show statistics before cleanup
        if args.stats:
            logger.info("Session statistics before cleanup:")
            stats_before = get_session_statistics(db)
            for key, value in stats_before.items():
                logger.info(f"  {key}: {value}")

        # Perform cleanup
        cleanup_stats = cleanup_sessions(db, dry_run=args.dry_run)

        # Show statistics after cleanup
        if args.stats and not args.dry_run:
            logger.info("Session statistics after cleanup:")
            stats_after = get_session_statistics(db)
            for key, value in stats_after.items():
                logger.info(f"  {key}: {value}")

        logger.info("Session cleanup completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}", exc_info=True)
        db.rollback()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
