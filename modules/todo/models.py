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
        # v0.2 签到表：只新增，绝不动既有 todo_items（幂等，可重复执行）
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkins (
                day        TEXT PRIMARY KEY,   -- YYYY-MM-DD
                streak     INTEGER NOT NULL,   -- 签到当天的连续天数（用于历史查询）
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_checkins_day ON checkins(day)")
        _backfill_checkins(conn)


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
    """兼容包装：老调用方只拿当前连续天数。新代码请用 streak_stats()。"""
    return streak_stats()["current"]


# ============================================================
# v0.2 · 连续打卡：签到表 + 历史回填 + 语义化统计
# ============================================================

MILESTONES = [3, 7, 14, 30, 100, 365]


def _done_days(conn) -> set:
    """todo_items 里出现过「已完成」的日期集合。"""
    return {r[0] for r in conn.execute("SELECT DISTINCT day FROM todo_items WHERE done = 1")}


def _checkin_days(conn) -> set:
    """checkins 表里已登记的签到日期集合。"""
    return {r[0] for r in conn.execute("SELECT day FROM checkins")}


def _all_checkin_days(conn) -> set:
    """打卡判定口径：当天有任意一项待办完成，或当天已有签到记录 —— 两个来源取并集。"""
    return _done_days(conn) | _checkin_days(conn)


def _backfill_checkins(conn) -> None:
    """老库升级兼容：从 todo_items 的历史 done 数据回填签到记录。

    幂等（INSERT OR IGNORE），保证升级后老用户的连续天数不会突然归零。
    回填的 streak 字段按日期顺序累计计算，作为历史快照。
    """
    days = sorted(_done_days(conn))
    if not days:
        return
    known = _checkin_days(conn)
    streak = 0
    prev: date | None = None
    for d in days:
        cur = date.fromisoformat(d)
        streak = streak + 1 if (prev is not None and (cur - prev).days == 1) else 1
        prev = cur
        if d not in known:
            conn.execute(
                "INSERT OR IGNORE INTO checkins (day, streak, created_at) VALUES (?, ?, ?)",
                (d, streak, today_str()),
            )


def ensure_checkin(day: str | None = None) -> dict:
    """某天完成任意一项待办时记一次签到；重复调用幂等（day 是主键，INSERT OR IGNORE）。"""
    day = day or today_str()
    with connect(DB_FILE) as conn:
        # 写入当时的连续天数快照（含当天），供历史查询
        days = _all_checkin_days(conn) | {day}
        streak = 0
        cursor = date.fromisoformat(day)
        while cursor.isoformat() in days:
            streak += 1
            cursor -= timedelta(days=1)
        conn.execute(
            "INSERT OR IGNORE INTO checkins (day, streak, created_at) VALUES (?, ?, ?)",
            (day, streak, today_str()),
        )
        row = conn.execute("SELECT day, streak FROM checkins WHERE day = ?", (day,)).fetchone()
    return {"day": row["day"], "streak": row["streak"]}


def streak_stats(day: str | None = None) -> dict:
    """连续打卡完整状态（语义见各字段注释，测试已锁死边界行为）。"""
    today = date.fromisoformat(day) if day else date.today()
    today_s = today.isoformat()
    with connect(DB_FILE) as conn:
        dayset = _all_checkin_days(conn)

    # 当前连续：今天已签 → 从今天往前数；今天没签但昨天签了 → 从昨天往前数
    # （pending_today：连续没断，等今天续上，页面显示「连续 N 天 · 今天还没打卡」而不是 0）
    pending_today = today_s not in dayset and (today - timedelta(days=1)).isoformat() in dayset
    cursor = today if today_s in dayset else today - timedelta(days=1)
    current = 0
    while cursor.isoformat() in dayset:
        current += 1
        cursor -= timedelta(days=1)

    # 历史最长：对全部打卡日排序，扫一遍连续区间（断签前攒的纪录必须保留）
    longest = 0
    run = 0
    prev: date | None = None
    for d in sorted(dayset):
        cur = date.fromisoformat(d)
        run = run + 1 if (prev is not None and (cur - prev).days == 1) else 1
        prev = cur
        if run > longest:
            longest = run
    longest = max(longest, current)

    # 最近 7 天（含今天），从旧到新
    recent = []
    for offset in range(6, -1, -1):
        d = today - timedelta(days=offset)
        ds = d.isoformat()
        recent.append(
            {
                "day": ds,
                "label": "一二三四五六日"[d.weekday()],
                "checked": ds in dayset,
                "is_today": offset == 0,
            }
        )

    # 里程碑：hit = 已达成的最大里程碑；next/to_next = 下一个目标
    hit = 0
    for m in MILESTONES:
        if current >= m:
            hit = m
    nxt = next((m for m in MILESTONES if m > current), None)
    milestone = {"hit": hit, "next": nxt, "to_next": (nxt - current) if nxt is not None else None}

    return {
        "current": current,
        "pending_today": pending_today,
        "last_day": max(dayset) if dayset else None,
        "longest": longest,
        "total": len(dayset),
        "recent": recent,
        "milestone": milestone,
    }
