"""核心页面路由：首页与关于页（属于站点本体，永远在线，不受模块启停影响）。"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

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


@router.get("/healthz")
def healthz():
    """健康检查：Docker healthcheck / 运维探活用，永远返回 200。"""
    return PlainTextResponse("ok")


@router.get("/robots.txt")
def robots():
    """robots：小站内容欢迎收录。"""
    return PlainTextResponse("User-agent: *\nAllow: /\n")
