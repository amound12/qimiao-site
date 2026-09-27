"""自动化测试：模块注册机制 + 待办模块接口。

本地运行：pip install -r requirements-dev.txt && pytest
验收标准对应关系：
- test_disabled_module  → 「禁用示例模块，站点其余部分正常」
- test_home_page        → 「首页卡片由注册中心自动生成」
- 其余                  → 核心页面与模块接口可用
"""
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

DATA_TEST_DIR = Path(__file__).resolve().parent.parent / "data-test"


@pytest.fixture(autouse=True)
def _cleanup_data():
    """每个测试用独立的临时数据目录：跑前清残留（上次崩溃可能留下），跑完即删。"""
    if DATA_TEST_DIR.exists():
        shutil.rmtree(DATA_TEST_DIR)
    yield
    if DATA_TEST_DIR.exists():
        shutil.rmtree(DATA_TEST_DIR)


def make_client(monkeypatch, modules="todo"):
    monkeypatch.setenv("MODULES_ENABLED", modules)
    monkeypatch.setenv("DATA_DIR", "data-test")
    monkeypatch.setenv("ENV", "development")
    from main import create_app
    return TestClient(create_app())


def test_home_page(monkeypatch):
    """首页正常渲染，且模块卡片由注册中心自动生成。"""
    client = make_client(monkeypatch)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "奇妙小站" in resp.text
    assert "每日待办" in resp.text          # 卡片来自 todo 模块的 MODULE 清单
    assert "待办" in resp.text               # 导航项同样自动注入


def test_about_and_404(monkeypatch):
    client = make_client(monkeypatch)
    assert client.get("/about").status_code == 200
    resp = client.get("/no-such-page")
    assert resp.status_code == 404
    assert "404" in resp.text


def test_todo_page_and_api_flow(monkeypatch):
    """待办模块页面 + 增/勾/删全流程。"""
    client = make_client(monkeypatch)
    assert client.get("/todo").status_code == 200

    resp = client.post("/todo/api/items", json={"content": "写一条测试待办"})
    assert resp.status_code == 200 and resp.json()["ok"] is True
    item_id = resp.json()["item"]["id"]

    resp = client.patch(f"/todo/api/items/{item_id}")
    assert resp.json()["item"]["done"] is True

    resp = client.delete(f"/todo/api/items/{item_id}")
    assert resp.json()["ok"] is True

    # 非法输入：空内容被 422 拦截
    assert client.post("/todo/api/items", json={"content": ""}).status_code == 422

    # 不存在的条目：返回 404（而不是 200 + ok:false）
    assert client.patch("/todo/api/items/99999").status_code == 404
    assert client.delete("/todo/api/items/99999").status_code == 404


def test_disabled_module(monkeypatch):
    """验收标准：禁用模块后，主站与其余页面完全不受影响。"""
    client = make_client(monkeypatch, modules="")
    assert client.get("/").status_code == 200
    assert client.get("/about").status_code == 200
    assert client.get("/todo").status_code == 404            # 模块路由消失
    assert "每日待办" not in client.get("/").text            # 首页卡片消失


def test_module_static_assets_reachable(monkeypatch):
    """回归：模块静态资源必须真实可访问。

    曾经的 bug：核心 /static 挂载先于模块挂载注册，前缀匹配把
    /static/modules/todo/* 吞掉返回 404，todo 页面裸奔且 JS 失效。
    """
    client = make_client(monkeypatch)
    for url, expect in [
        ("/static/site.css", "text/css"),
        ("/static/modules/todo/todo.css", "text/css"),
        ("/static/modules/todo/todo.js", "javascript"),
    ]:
        resp = client.get(url)
        assert resp.status_code == 200, f"{url} 应可访问，实际 {resp.status_code}"
        assert expect in resp.headers["content-type"], url


def test_blank_content_rejected(monkeypatch):
    """回归：纯空白内容不允许入库（校验必须发生在 trim 之后）。"""
    client = make_client(monkeypatch)
    for bad in ["", "   ", "\t\n  "]:
        assert client.post("/todo/api/items", json={"content": bad}).status_code == 422

    # 正常内容照常入库，且入库前已 trim
    resp = client.post("/todo/api/items", json={"content": "  前后有空格  "})
    assert resp.status_code == 200
    assert resp.json()["item"]["content"] == "前后有空格"


def test_ops_endpoints_and_headers(monkeypatch):
    """健康检查 / robots 可用；安全响应头与静态缓存头生效。"""
    client = make_client(monkeypatch)
    assert client.get("/healthz").status_code == 200
    assert client.get("/robots.txt").status_code == 200

    resp = client.get("/")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "Content-Security-Policy" in resp.headers

    resp = client.get("/static/site.css")
    assert resp.headers["Cache-Control"] == "public, max-age=3600"


def test_fonts_self_hosted(monkeypatch):
    """回归：字体自托管，任何页面不得再引用 Google Fonts（国内访问会卡首屏）。"""
    client = make_client(monkeypatch)
    resp = client.get("/static/fonts/fonts.css")
    assert resp.status_code == 200
    assert "fonts.gstatic.com" not in resp.text      # CSS 里的 url() 已全部本地化

    for page in ["/", "/about", "/todo", "/no-such-page"]:
        text = client.get(page).text
        assert "fonts.googleapis.com" not in text, page
        assert "fonts.gstatic.com" not in text, page
