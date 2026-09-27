"""站点配置：全部来自 .env（参考 .env.example），密钥永不入 Git。

可配置项：
- SITE_NAME / SITE_SLOGAN / SITE_OWNER / SITE_INTRO  站点基本信息
- MODULES_ENABLED    启用的模块清单（逗号分隔目录名），禁用模块 = 从这里删名字
- DATA_DIR           数据目录（SQLite 库文件都落在这里）
- ENV                production / development
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（qimiao/）
BASE_DIR = Path(__file__).resolve().parent.parent

# .env 与代码分离；没有 .env 时使用下方默认值，本地开发也能直接跑
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    site_name: str
    site_slogan: str
    site_owner: str
    site_intro: str
    env: str
    modules_enabled: tuple[str, ...]
    data_dir: Path


def load_settings() -> Settings:
    """每次调用都重新读取环境变量（测试和热切换模块组合时用）。"""
    raw = os.getenv("MODULES_ENABLED", "todo")
    modules = tuple(
        item.strip() for item in raw.split(",") if item.strip()
    )
    return Settings(
        site_name=os.getenv("SITE_NAME", "奇妙小站"),
        site_slogan=os.getenv("SITE_SLOGAN", "慢慢做，不着急。"),
        site_owner=os.getenv("SITE_OWNER", "搭子"),
        site_intro=os.getenv(
            "SITE_INTRO",
            "这里是我折腾各种小东西的地方——写点随笔、做点小工具，偶尔冒出一些奇思妙想。",
        ),
        env=os.getenv("ENV", "production"),
        modules_enabled=modules,
        data_dir=BASE_DIR / os.getenv("DATA_DIR", "data"),
    )


# 注意：这里刻意不提供模块级 settings 单例。
# 历史上存在「create_app 现读环境变量、其他模块用导入时刻单例」两套真相，
# 环境变量改了之后容易出现配置漂移。统一入口：from core.config import load_settings
