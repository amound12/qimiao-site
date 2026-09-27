"""全局模板渲染：站点信息与导航自动注入，核心页面与模块页面共用同一套环境。

模块页面里直接写：
    from core.render import render
    return render(request, "todo/index.html", 自定义上下文...)
模板目录在 Registry.apply 时合并（core/templates + 各模块 templates/），
所以模块模板可以直接 {% extends "base.html" %}。
"""
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

_env: Jinja2Templates | None = None
_registry = None


def init(template_dirs: list, registry) -> None:
    """由 Registry.apply 调用：合并核心与各模块的模板目录。"""
    global _env, _registry
    _env = Jinja2Templates(directory=list(template_dirs))
    _registry = registry


def render(request: Request, name: str, status_code: int = 200, **ctx: Any):
    """渲染模板并返回响应。nav_items / 站点信息自动注入，无需每个页面重复传。"""
    from core.config import load_settings

    settings = load_settings()

    # 导航 = 首页 + 各模块（带 nav_label 的）+ 实验室（首页锚点，站点本体）+ 关于，按 order 排序
    items: list[dict] = [{"url": "/", "label": "首页", "order": 0}]
    for lm in _registry.loaded:
        mf = lm.manifest
        if mf.nav_label:
            items.append({"url": mf.prefix, "label": mf.nav_label, "order": mf.nav_order})
    # 实验室属于站点本体（首页卡片区锚点），不随模块启停变化
    items.append({"url": "/#lab", "label": "实验室", "order": 30})
    items.append({"url": "/about", "label": "关于", "order": 999})
    items.sort(key=lambda x: x["order"])

    path = request.url.path
    nav_items = [
        {
            **it,
            # 高亮判定先剥掉 #fragment：request.url.path 不含 fragment，
            # /#lab 这类锚点项必须按 path 部分比对，否则首页时实验室永远不亮
            # 按「整段路径」判断高亮，避免 /todo-xxx 也点亮「待办」
            "active": path == it["url"].split("#", 1)[0]
            or (
                it["url"].split("#", 1)[0] != "/"
                and path.startswith(it["url"].split("#", 1)[0] + "/")
            ),
        }
        for it in items
    ]

    return _env.TemplateResponse(
        request,
        name,
        {
            "site_name": settings.site_name,
            "site_slogan": settings.site_slogan,
            "site_owner": settings.site_owner,
            "site_intro": settings.site_intro,
            "site_version": settings.site_version,
            "nav_items": nav_items,
            **ctx,
        },
        status_code=status_code,
    )
