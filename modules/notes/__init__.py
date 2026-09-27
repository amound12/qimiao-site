"""随笔模块 —— v0.2 新增的占位骨架，后续在这里攒零碎想法。

一个模块对外只暴露三样东西：
- MODULE   模块清单（注册中心据此生成导航项与首页卡片）
- get_router()  返回本模块路由（挂载到 MODULE.prefix 下）
- setup()  模块初始化（建表/迁移），启用时自动执行，可省略
"""
from core.registry import ModuleManifest

MODULE = ModuleManifest(
    name="notes",
    title="随笔",
    prefix="/notes",
    description="想到什么写什么，慢慢攒。",
    version="0.2.0",
    nav_label="随笔",
    nav_order=20,          # 排在「实验室」之前（实验室是固定导航项 order=30）
    card_badge="v0.2 · 新上",
)


def get_router():
    from .router import router
    return router
