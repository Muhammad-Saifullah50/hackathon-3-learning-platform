"""Mastery snapshot repository — append-only time-series of mastery scores."""

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession


class MasterySnapshotRepository:
    """Repository for the mastery_snapshots append-only table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_snapshot(self, user_id: str, module_id: int, score: float) -> None:
        """Append a new mastery snapshot row."""
        await self.session.execute(
            text(
                "INSERT INTO mastery_snapshots (user_id, module_id, score) "
                "VALUES (:user_id, :module_id, :score)"
            ),
            {"user_id": str(user_id), "module_id": module_id, "score": score},
        )
        await self.session.commit()

    async def get_daily_averages(self, user_id: str) -> list[dict[str, Any]]:
        """Return daily average mastery score for a student, ordered by day ASC."""
        result = await self.session.execute(
            text(
                "SELECT DATE(recorded_at) AS day, AVG(score) AS avg_score "
                "FROM mastery_snapshots "
                "WHERE user_id = :user_id "
                "GROUP BY DATE(recorded_at) "
                "ORDER BY day ASC"
            ),
            {"user_id": str(user_id)},
        )
        rows = result.fetchall()
        return [{"day": row[0], "avg_score": float(row[1])} for row in rows]
