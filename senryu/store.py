"""
川柳のSQLiteによる永続化
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "senryu.db"


@dataclass
class Senryu:
    id: int
    guild_id: int
    channel_id: int
    user_id: int
    message_id: int
    line1: str
    line2: str
    line3: str
    created_at: datetime  # UTC aware


class SenryuStore:
    """検出した川柳のCRUDを行うSQLiteストア"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    async def init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS senryus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    line1 TEXT NOT NULL,
                    line2 TEXT NOT NULL,
                    line3 TEXT NOT NULL,
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
        message_id: int,
        lines: list[str],
    ) -> int:
        """川柳を登録し、そのサーバーで何個目の川柳かを返す"""
        created_at = datetime.now(timezone.utc)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO senryus "
                "(guild_id, channel_id, user_id, message_id, line1, line2, line3, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    guild_id,
                    channel_id,
                    user_id,
                    message_id,
                    lines[0],
                    lines[1],
                    lines[2],
                    created_at.isoformat(),
                ),
            )
            await db.commit()

            cursor = await db.execute(
                "SELECT COUNT(*) FROM senryus WHERE guild_id = ?", (guild_id,)
            )
            row = await cursor.fetchone()
            return row[0]

    async def count_by_guild(self, guild_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM senryus WHERE guild_id = ?", (guild_id,)
            )
            row = await cursor.fetchone()
            return row[0]

    async def list_by_guild(self, guild_id: int) -> list[Senryu]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM senryus WHERE guild_id = ? ORDER BY created_at ASC",
                (guild_id,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_senryu(row) for row in rows]

    @staticmethod
    def _row_to_senryu(row: aiosqlite.Row) -> Senryu:
        return Senryu(
            id=row["id"],
            guild_id=row["guild_id"],
            channel_id=row["channel_id"],
            user_id=row["user_id"],
            message_id=row["message_id"],
            line1=row["line1"],
            line2=row["line2"],
            line3=row["line3"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
