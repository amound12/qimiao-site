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
    """每个测试用独立的临时数据目录，跑完即删。"""
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


def test_disabled_module(monkeypatch):
    """验收标准：禁用模块后，主站与其余页面完全不受影响。"""
    client = make_client(monkeypatch, modules="")
    assert client.get("/").status_code == 200
    assert client.get("/about").status_code == 200
    assert client.get("/todo").status_code == 404            # 模块路由消失
    assert "每日待办" not in client.get("/").text            # 首页卡片消失
