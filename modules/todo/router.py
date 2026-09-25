"""每日待办 · 路由层：一个页面路由 + 三个 JSON 接口（页面无刷新交互）。"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from core.render import render
from . import models

router = APIRouter()


class ItemIn(BaseModel):
    """添加待办的请求体：内容 1~200 字。"""
    content: str = Field(min_length=1, max_length=200)


@router.get("", response_class=HTMLResponse)
def index(request: Request):
    """待办主页面：今日清单 + 统计。"""
    day = models.today_str()
    return render(
        request,
        "todo/index.html",
        day_label=models.day_label(),
        items=models.list_items(day),
        stats=models.day_stats(day),
        streak=models.streak_days(),
    )


@router.post("/api/items")
def api_add(payload: ItemIn):
    item = models.add_item(payload.content.strip())
    return {"ok": True, "item": item}


@router.patch("/api/items/{item_id}")
def api_toggle(item_id: int):
    result = models.toggle_item(item_id)
    if result is None:
        return {"ok": False, "msg": "条目不存在"}
    return {"ok": True, "item": result}


@router.delete("/api/items/{item_id}")
def api_delete(item_id: int):
    return {"ok": models.delete_item(item_id)}
