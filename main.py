"""总入口：创建应用 → 装配模块 → 启动。

这个文件的职责到此为止。以后加任何新功能，都不需要动这里——
只需要在 modules/ 下新建模块目录，并在 .env 的 MODULES_ENABLED 登记。
"""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.config import load_settings
from core.registry import Registry
from core.render import render


def create_app() -> FastAPI:
    """工厂函数：每次调用重新读取配置，方便测试时切换模块组合。"""
    settings = load_settings()
    app = FastAPI(
        title=settings.site_name,
        # 自用小站不需要 API 文档面板，顺手关掉减少攻击面
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # 装配所有已启用模块：静态资源、路由、核心页面、渲染环境
    registry = Registry(settings)
    registry.apply(app)

    @app.middleware("http")
    async def security_and_cache(request: Request, call_next):
        """安全响应头 + 静态资源缓存（无论是否走 Nginx 都生效）。"""
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # 全站无外链资源，CSP 可以收紧到只允许同源；内联脚本已外置到 /static/site.js
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; font-src 'self'; frame-ancestors 'self'; "
            "base-uri 'self'; form-action 'self'"
        )
        if request.url.path.startswith("/static/"):
            # 文件名未做 hash 版本化，缓存 1 小时后须重新验证（ETag/Last-Modified 兜底）
            response.headers["Cache-Control"] = "public, max-age=3600"
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """404 走定制贴纸风页面；其他错误码原样返回。"""
        if exc.status_code == 404:
            return render(request, "404.html", status_code=404)
        return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

    return app


app = create_app()

if __name__ == "__main__":
    # 本地裸跑：python main.py（生产环境用 uvicorn / Docker，见部署手册）
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
