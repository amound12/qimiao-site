"""SQLite 公共工具：每个模块一个独立 .db 文件，数据天然隔离。

模块使用方式（以 todo 模块为例）：
    from core.database import connect

    with connect("todo.db") as conn:      # 事务：成功提交、异常回滚、用完自动关
        rows = conn.execute("SELECT ...").fetchall()

删除模块 = 删掉它的 db 文件，别的模块毫发无损。
库文件统一落在 DATA_DIR（生产环境是 Docker 挂载的 ./data 目录）。
"""
import sqlite3
from contextlib import contextmanager

from core.config import load_settings


@contextmanager
def connect(db_filename: str):
    """打开一个模块数据库连接，yield 出去，退出时提交/回滚并关闭。"""
    path = load_settings().data_dir / db_filename
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    # WAL：读写互不阻塞（备份脚本同时读库也不会锁住写入）；busy_timeout 兜底锁冲突
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        with conn:  # 事务块：正常退出 commit，异常 rollback
            yield conn
    finally:
        conn.close()
