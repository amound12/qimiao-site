"""随笔模块 · 路由层：目前只有一个占位页面，内容以后慢慢攒。"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core.render import render

router = APIRouter()


@router.get("", response_class=HTMLResponse)
def index(request: Request):
    return render(request, "notes/index.html")
