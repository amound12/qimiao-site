"""新模块脚手架 —— 复制本目录为 modules/<你的模块名>，改掉所有 TODO 即可。

完整流程见 docs/新功能开发SOP.md。核心动作只有三步：
1. cp -r modules/_template modules/my_module   （改目录名）
2. 修改本文件的 MODULE 清单（name/prefix/title 等）
3. 在 .env 的 MODULES_ENABLED 里加上模块名，重启生效
"""
from core.registry import ModuleManifest

MODULE = ModuleManifest(
    name="my_module",              # TODO: 改成目录名（英文小写下划线）
    title="我的新模块",             # TODO: 显示名（导航/首页卡片）
    prefix="/my-module",           # TODO: 路由前缀（英文短横线）
    description="一句话介绍，会显示在首页卡片上。",  # TODO
    version="0.1.0",
    nav_label="",                  # 想出现在顶部导航就填，如 "我的模块"；留空不进导航
    nav_order=50,                  # 导航排序，数字小在前
    card_badge="v0.1 · 新上",      # 首页卡片右上角徽章
)


def get_router():
    from .router import router
    return router


def setup():
    """模块初始化（建表/迁移等），启用时自动执行。用不到可以整个删掉。"""
    pass
