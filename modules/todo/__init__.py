"""每日待办模块 —— 以后所有新模块都以它为模板。

一个模块对外只暴露三样东西：
- MODULE   模块清单（注册中心据此生成导航项与首页卡片）
- get_router()  返回本模块路由（挂载到 MODULE.prefix 下）
- setup()  模块初始化（建表/迁移），启用时自动执行，可省略
"""
from core.registry import ModuleManifest

MODULE = ModuleManifest(
    name="todo",
    title="每日待办",
    prefix="/todo",
    description="今天的事今天管——勾掉一项算一项。",
    version="0.2.0",
    nav_label="",              # v0.2 起退出顶部导航；留空 = 不进导航，从首页实验室卡片进入
    nav_order=10,
    card_badge="v0.2 · 已优化",
)


def get_router():
    from .router import router
    return router


def setup():
    """启用模块时自动建表（幂等，重复执行无害）。"""
    from .models import init_db
    init_db()
