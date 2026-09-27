"""每日待办 · 路由层：一个页面路由 + 三个 JSON 接口（页面无刷新交互）。"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from core.render import render
from . import models

router = APIRouter()


class ItemIn(BaseModel):
    """添加待办的请求体：内容 trim 后 1~200 字（纯空白会被拒绝）。"""
    content: str = Field(min_length=1, max_length=200)

    @field_validator("content")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("内容不能为空")
        return v


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
        streak=models.streak_stats(),
    )


@router.get("/api/streak")
def api_streak():
    """打卡状态：前端勾选后增量刷新打卡卡片与 7 天圆点，避免整页重载。"""
    return {"ok": True, "streak": models.streak_stats()}


@router.post("/api/items")
def api_add(payload: ItemIn):
    # content 已在校验器里 trim 过
    item = models.add_item(payload.content)
    return {"ok": True, "item": item}


@router.patch("/api/items/{item_id}")
def api_toggle(item_id: int):
    result = models.toggle_item(item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="条目不存在")
    if result["done"]:
        # 勾成完成 → 记一次当天签到（幂等）；取消勾选不回滚签到记录：
        # 误触不该有把 30 天纪录清零的代价，签到事实一旦发生就保留（产品判断）
        models.ensure_checkin(result["day"])
    return {"ok": True, "item": result}


@router.delete("/api/items/{item_id}")
def api_delete(item_id: int):
    if not models.delete_item(item_id):
        raise HTTPException(status_code=404, detail="条目不存在")
    return {"ok": True}
