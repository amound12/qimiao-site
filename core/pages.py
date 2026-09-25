"""核心页面路由：首页与关于页（属于站点本体，永远在线，不受模块启停影响）。"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core.render import render

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """首页：hero 区（模板原样）+ 实验室卡片区（由模块注册中心自动生成）。"""
    registry = request.app.state.registry
    return render(request, "home.html", home_cards=registry.home_cards())


@router.get("/about", response_class=HTMLResponse)
def about(request: Request):
    """关于页：个人简介 + 联系方式。"""
    return render(request, "about.html")
