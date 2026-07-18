"""
リマインダーの日時文字列パーサー

ユーザー入力（JSTとして解釈）をUTCのdatetimeに変換する。
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")

FORMATS_FULL = ["%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"]
FORMATS_MONTH_DAY = ["%m-%d %H:%M", "%m/%d %H:%M"]
FORMATS_TIME = ["%H:%M"]


class ReminderTimeError(ValueError):
    """日時文字列のパースに失敗した場合の例外"""


def parse_datetime(text: str, now: datetime | None = None) -> datetime:
    """
    リマインダー時刻の文字列をUTCのdatetimeに変換する。

    対応フォーマット（すべてJSTとして解釈）:
      - "YYYY-MM-DD HH:MM" (例: 2026-07-15 09:00)
      - "MM-DD HH:MM"       (例: 07-15 09:00、今年として解釈)
      - "HH:MM"             (例: 09:00、今日。すでに過ぎていれば翌日)

    Raises:
        ReminderTimeError: フォーマットが不正、または過去日時の場合
    """
    text = text.strip()
    now_jst = (now or datetime.now(timezone.utc)).astimezone(JST)

    dt_jst = None

    for fmt in FORMATS_FULL:
        try:
            dt_jst = datetime.strptime(text, fmt).replace(tzinfo=JST)
            break
        except ValueError:
            continue

    if dt_jst is None:
        for fmt in FORMATS_MONTH_DAY:
            try:
                parsed = datetime.strptime(text, fmt)
                dt_jst = parsed.replace(year=now_jst.year, tzinfo=JST)
                break
            except ValueError:
                continue

    if dt_jst is None:
        for fmt in FORMATS_TIME:
            try:
                parsed = datetime.strptime(text, fmt)
                dt_jst = now_jst.replace(
                    hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
                if dt_jst <= now_jst:
                    dt_jst += timedelta(days=1)
                break
            except ValueError:
                continue

    if dt_jst is None:
        raise ReminderTimeError(
            "日時の形式が正しくありません。例: `2026-07-15 09:00` / `07-15 09:00` / `09:00`")

    if dt_jst <= now_jst:
        raise ReminderTimeError("過去の日時は指定できません。")

    return dt_jst.astimezone(timezone.utc)
