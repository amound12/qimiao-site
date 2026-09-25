"""每日待办 · 数据层：独立 todo.db，与其他模块完全隔离。"""
from datetime import date, timedelta

from core.database import connect

DB_FILE = "todo.db"

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def init_db() -> None:
    with connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todo_items (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                content  TEXT    NOT NULL,
                done     INTEGER NOT NULL DEFAULT 0,
                done_at  TEXT,
                day      TEXT    NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_todo_day ON todo_items(day)")


def today_str() -> str:
    return date.today().isoformat()


def day_label(day: str | None = None) -> str:
    """页面右上角的日期文案，如「9月25日 · 星期五」。"""
    d = date.fromisoformat(day) if day else date.today()
    return f"{d.month}月{d.day}日 · {WEEKDAYS[d.weekday()]}"


def _to_dict(row) -> dict:
    return {"id": row["id"], "content": row["content"], "done": bool(row["done"]), "day": row["day"]}


def list_items(day: str) -> list[dict]:
    """某天的待办清单：未完成的在前，新添加的在前。"""
    with connect(DB_FILE) as conn:
        rows = conn.execute(
            "SELECT id, content, done, day FROM todo_items WHERE day = ? ORDER BY done, id DESC",
            (day,),
        ).fetchall()
    return [_to_dict(r) for r in rows]


def add_item(content: str, day: str | None = None) -> dict:
    day = day or today_str()
    with connect(DB_FILE) as conn:
        cur = conn.execute("INSERT INTO todo_items (content, day) VALUES (?, ?)", (content, day))
        item_id = cur.lastrowid
    return {"id": item_id, "content": content, "done": False, "day": day}


def toggle_item(item_id: int) -> dict | None:
    """切换完成状态；条目不存在时返回 None。"""
    with connect(DB_FILE) as conn:
        row = conn.execute(
            "SELECT id, content, done, day FROM todo_items WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            return None
        new_done = 0 if row["done"] else 1
        conn.execute(
            "UPDATE todo_items SET done = ?, done_at = ? WHERE id = ?",
            (new_done, today_str() if new_done else None, item_id),
        )
    return {"id": item_id, "content": row["content"], "done": bool(new_done), "day": row["day"]}


def delete_item(item_id: int) -> bool:
    with connect(DB_FILE) as conn:
        cur = conn.execute("DELETE FROM todo_items WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def day_stats(day: str) -> dict:
    """今日待办总数 / 已完成数。"""
    with connect(DB_FILE) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM todo_items WHERE day = ?",
            (day,),
        ).fetchone()
    return {"total": row["total"], "done": row["done"]}


def streak_days() -> int:
    """连续打卡天数：从今天（今天还没完成项则从昨天）往前数，每天都有完成项就 +1。"""
    with connect(DB_FILE) as conn:
        days = {r[0] for r in conn.execute("SELECT DISTINCT day FROM todo_items WHERE done = 1")}
    today = date.today()
    cursor = today if today.isoformat() in days else today - timedelta(days=1)
    streak = 0
    while cursor.isoformat() in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
