"""脚手架路由：一个最简单的页面路由示例。

模块需要数据库时，参考 modules/todo/models.py 的做法：
    from core.database import connect
    with connect("my_module.db") as conn:   # 独立 db 文件，天然隔离
        conn.execute("CREATE TABLE IF NOT EXISTS ...")
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core.render import render

router = APIRouter()


@router.get("", response_class=HTMLResponse)
def index(request: Request):
    # 模板放在本模块 templates/<模块名>/index.html
    return render(request, "my_module/index.html")
