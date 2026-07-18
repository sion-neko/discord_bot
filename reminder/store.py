"""
リマインダーのSQLiteによる永続化
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "reminders.db"


@dataclass
class Reminder:
    id: int
    guild_id: int
    channel_id: int
    user_id: int
    message: str
    remind_at: datetime  # UTC aware
    created_at: datetime  # UTC aware


class ReminderStore:
    """リマインダーのCRUDを行うSQLiteストア"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    async def init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    remind_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            await db.commit()

    async def add(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        message: str,
        remind_at: datetime,
    ) -> int:
        created_at = datetime.now(timezone.utc)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO reminders "
                "(guild_id, channel_id, user_id, message, remind_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    guild_id,
                    channel_id,
                    user_id,
                    message,
                    remind_at.isoformat(),
                    created_at.isoformat(),
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_due(self, now: datetime) -> list[Reminder]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM reminders WHERE remind_at <= ? ORDER BY remind_at ASC",
                (now.isoformat(),),
            )
            rows = await cursor.fetchall()
            return [self._row_to_reminder(row) for row in rows]

    async def list_by_guild(self, guild_id: int) -> list[Reminder]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM reminders WHERE guild_id = ? ORDER BY remind_at ASC",
                (guild_id,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_reminder(row) for row in rows]

    async def get(self, reminder_id: int) -> Reminder | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
            )
            row = await cursor.fetchone()
            return self._row_to_reminder(row) if row else None

    async def delete(self, reminder_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            await db.commit()

    @staticmethod
    def _row_to_reminder(row: aiosqlite.Row) -> Reminder:
        return Reminder(
            id=row["id"],
            guild_id=row["guild_id"],
            channel_id=row["channel_id"],
            user_id=row["user_id"],
            message=row["message"],
            remind_at=datetime.fromisoformat(row["remind_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
