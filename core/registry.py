"""模块注册中心 —— 全站的「乐高底座」，本项目的灵魂。

规则三句话：
1. 每个模块目录（modules/<name>/）必须在 __init__.py 里声明 MODULE: ModuleManifest，
   可选提供 get_router()（路由）与 setup()（初始化，如建表）。
2. .env 的 MODULES_ENABLED 决定谁上线；禁用模块 = 从清单移除名字 + 重启，
   导航项、首页卡片、路由会一并消失，主站与其他模块不受影响。
3. 新增模块两步：复制 modules/_template → 在 MODULES_ENABLED 登记。core/ 永不修改。

单个模块导入或初始化失败只会被跳过并记日志，不会拖垮整站。
"""
import importlib
import logging
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("qimiao.registry")

MODULES_PACKAGE = "modules"


@dataclass(frozen=True)
class ModuleManifest:
    """模块清单：一个模块对外界的全部声明，注册中心只认这个。"""

    name: str                 # 模块标识（=目录名，英文小写下划线）
    title: str                # 显示名（导航/卡片）
    prefix: str               # 路由前缀，如 /todo
    description: str = ""     # 一句话介绍，显示在首页卡片
    version: str = "0.1.0"    # 模块自己的版本号
    nav_label: str = ""       # 顶部导航文字；留空 = 不进导航
    nav_order: int = 100      # 导航排序，数字小在前
    card_badge: str = ""      # 首页卡片徽章，如 "v0.1 · 上线"
    show_on_home: bool = True # 是否在首页实验室区展示卡片


@dataclass
class LoadedModule:
    """加载完成的一个模块实例。"""

    manifest: ModuleManifest
    templates_dir: Path | None
    static_dir: Path | None
    router: object | None


class Registry:
    """模块注册中心：加载 → 装配 → 对外提供导航项与首页卡片。"""

    def __init__(self, settings):
        self.settings = settings
        self.loaded: list[LoadedModule] = []

    # ---------- 加载 ----------

    def load(self) -> list[LoadedModule]:
        self.loaded = []
        for name in self.settings.modules_enabled:
            try:
                mod = importlib.import_module(f"{MODULES_PACKAGE}.{name}")
            except Exception:
                logger.exception("模块 %s 导入失败，已跳过（不影响其他模块）", name)
                continue

            manifest = getattr(mod, "MODULE", None)
            if not isinstance(manifest, ModuleManifest):
                logger.warning("模块 %s 缺少合法的 MODULE 清单，已跳过", name)
                continue

            base = Path(mod.__file__).parent
            try:
                if hasattr(mod, "setup"):
                    mod.setup()
                router = mod.get_router() if hasattr(mod, "get_router") else None
            except Exception:
                logger.exception("模块 %s 初始化失败，已跳过", name)
                continue

            self.loaded.append(
                LoadedModule(
                    manifest=manifest,
                    templates_dir=base / "templates" if (base / "templates").is_dir() else None,
                    static_dir=base / "static" if (base / "static").is_dir() else None,
                    router=router,
                )
            )
            logger.info("模块已加载：%s v%s（%s）", manifest.name, manifest.version, manifest.prefix)
        return self.loaded

    # ---------- 装配 ----------

    def apply(self, app: FastAPI) -> None:
        """把所有已启用模块装配到应用上，并初始化全局渲染环境。"""
        self.load()

        from core.pages import router as pages_router
        from core.render import init as render_init

        core_dir = Path(__file__).parent

        # 各模块：静态资源挂到 /static/modules/<name>，路由挂到各自 prefix
        # 注意顺序：模块静态必须先于核心 /static 挂载。Starlette 按注册顺序匹配，
        # /static 是前缀挂载，先注册会把 /static/modules/<name>/xxx 整个吞掉 → 404。
        for lm in self.loaded:
            if lm.static_dir is not None:
                app.mount(
                    f"/static/modules/{lm.manifest.name}",
                    StaticFiles(directory=lm.static_dir),
                    name=f"static_{lm.manifest.name}",
                )
            if lm.router is not None:
                app.include_router(lm.router, prefix=lm.manifest.prefix)

        # 全站静态资源（设计令牌样式、头像等）——兜底挂载放最后
        app.mount("/static", StaticFiles(directory=core_dir / "static"), name="static")

        # 核心页面（首页/关于）永远在线
        app.include_router(pages_router)
        app.state.registry = self

        # 渲染环境：核心模板目录 + 各模块模板目录合并，模块页面可直接 extends base.html
        render_init(
            [core_dir / "templates"] + [lm.templates_dir for lm in self.loaded if lm.templates_dir],
            self,
        )

    # ---------- 对外查询 ----------

    def home_cards(self) -> list[dict]:
        """首页实验室区的卡片列表，按 nav_order 排序。"""
        modules = sorted(self.loaded, key=lambda lm: lm.manifest.nav_order)
        return [
            {
                "title": lm.manifest.title,
                "description": lm.manifest.description,
                "url": lm.manifest.prefix,
                "badge": lm.manifest.card_badge,
            }
            for lm in modules
            if lm.manifest.show_on_home
        ]
