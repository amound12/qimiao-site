"""自动化测试：模块注册机制 + 待办模块接口 + v0.2 导航/打卡/交互回归。

本地运行：pip install -r requirements-dev.txt && pytest
验收标准对应关系：
- test_disabled_module  → 「禁用示例模块，站点其余部分正常」
- test_home_page        → 「首页卡片由注册中心自动生成」
- 其余                  → 核心页面与模块接口可用
- v0.2 新增 10 例：导航四项、随笔占位、待办移出导航、打卡边界语义、
  签到幂等、streak 接口、greet 按钮、CSP 回归锁
"""
import re
import shutil
from datetime import date, timedelta
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


def make_client(monkeypatch, modules="todo,notes"):
    monkeypatch.setenv("MODULES_ENABLED", modules)
    monkeypatch.setenv("DATA_DIR", "data-test")
    monkeypatch.setenv("ENV", "development")
    from main import create_app
    return TestClient(create_app())


def nav_labels(html: str) -> list:
    """提取导航区块里的文字列表（按出现顺序）。"""
    m = re.search(r'<nav class="nav-links"[^>]*>(.*?)</nav>', html, re.S)
    assert m, "导航区块应存在"
    return re.findall(r"<a[^>]*>([^<]+)</a>", m.group(1))


# ============================================================
# 原有用例（v0.1 起锁定的回归）
# ============================================================

def test_home_page(monkeypatch):
    """首页正常渲染，且模块卡片由注册中心自动生成。

    v0.2 语义调整：「待办」已退出导航，这里改为断言新导航项
    （随笔/实验室）与卡片区仍含「每日待办」。
    """
    client = make_client(monkeypatch)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "奇妙小站" in resp.text
    assert "每日待办" in resp.text          # 卡片来自 todo 模块的 MODULE 清单
    assert "随笔" in resp.text               # 导航项同样自动注入（notes 模块）
    assert "实验室" in resp.text             # 站点本体固定导航项


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
    """验收标准：禁用模块后，主站与其余页面完全不受影响。

    实验室/随机问候属于站点本体，模块全关时导航仍应正常渲染。
    """
    client = make_client(monkeypatch, modules="")
    assert client.get("/").status_code == 200
    assert client.get("/about").status_code == 200
    assert client.get("/todo").status_code == 404            # 模块路由消失
    assert client.get("/notes").status_code == 404           # 模块路由消失
    assert "每日待办" not in client.get("/").text            # 首页卡片消失
    # 固定导航项不受模块启停影响
    assert nav_labels(client.get("/").text) == ["首页", "实验室", "关于"]


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
        ("/static/modules/notes/notes.css", "text/css"),
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

    for page in ["/", "/about", "/notes", "/todo", "/no-such-page"]:
        text = client.get(page).text
        assert "fonts.googleapis.com" not in text, page
        assert "fonts.gstatic.com" not in text, page


# ============================================================
# v0.2 新增用例
# ============================================================

def test_nav_order_and_labels(monkeypatch):
    """首页导航恰好四项且顺序固定：首页 → 随笔 → 实验室 → 关于；不含「待办」。"""
    client = make_client(monkeypatch)
    labels = nav_labels(client.get("/").text)
    assert labels == ["首页", "随笔", "实验室", "关于"]
    assert "待办" not in labels


def test_notes_page(monkeypatch):
    """随笔占位页 200、带完整导航页脚；首页出现「随笔」卡片。"""
    client = make_client(monkeypatch)
    resp = client.get("/notes")
    assert resp.status_code == 200
    assert "nav-links" in resp.text          # 导航继承
    assert "site-footer" in resp.text        # 页脚继承
    assert "还在酝酿" in resp.text           # 占位文案

    home = client.get("/").text
    assert "随笔" in home
    assert "想到什么写什么，慢慢攒。" in home  # 卡片 description 来自 MODULE 清单


def test_todo_still_reachable_without_nav(monkeypatch):
    """待办退出导航但模块保留：/todo 仍 200，首页卡片仍在，导航无「待办」。"""
    client = make_client(monkeypatch)
    assert client.get("/todo").status_code == 200
    home = client.get("/")
    assert home.status_code == 200
    assert "每日待办" in home.text
    assert "待办" not in nav_labels(home.text)


def test_streak_today_pending(monkeypatch):
    """昨天签过、今天还没签：current 从昨天起算 ≥1，pending_today=True（绝不能显示 0）。"""
    client = make_client(monkeypatch)
    from modules.todo import models
    yday = (date.today() - timedelta(days=1)).isoformat()
    item = models.add_item("昨天的事", day=yday)
    models.toggle_item(item["id"])
    s = models.streak_stats()
    assert s["current"] >= 1
    assert s["pending_today"] is True


def test_streak_broken_keeps_longest(monkeypatch):
    """连续 5 天后断 2 天：current 归 0，longest 保留历史峰值，total 不减。"""
    client = make_client(monkeypatch)
    from modules.todo import models
    today = date.today()
    for i in range(7, 2, -1):                # today-7 .. today-3，连续 5 天
        d = (today - timedelta(days=i)).isoformat()
        item = models.add_item("事" + d, day=d)
        models.toggle_item(item["id"])
    s = models.streak_stats()
    assert s["current"] == 0                 # 今天/昨天都没签 → 真断了
    assert s["longest"] == 5                 # 断签前峰值仍在
    assert s["total"] == 5
    assert s["longest"] >= s["current"]


def test_streak_backfill_from_existing_items(monkeypatch):
    """老库升级：只写 todo_items 历史 done 数据（不写 checkins）→ init_db 幂等回填。"""
    client = make_client(monkeypatch)
    from core.database import connect
    from modules.todo import models
    for i in range(3):                       # today-7..today-5 连续 3 天历史
        d = (date.today() - timedelta(days=7 - i)).isoformat()
        item = models.add_item("历史" + str(i), day=d)
        models.toggle_item(item["id"])
    models.init_db()                         # 模拟升级重启（幂等）
    with connect(models.DB_FILE) as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM checkins").fetchone()["n"]
    assert n == 3                            # 回填行数与历史天数一致
    s = models.streak_stats()
    assert s["total"] == 3                   # 累计天数不被清零


def test_checkin_idempotent(monkeypatch):
    """同一 day 反复 ensure_checkin：checkins 只有 1 行（主键 + INSERT OR IGNORE）。"""
    client = make_client(monkeypatch)
    from core.database import connect
    from modules.todo import models
    day = date.today().isoformat()
    for _ in range(5):
        models.ensure_checkin(day)
    with connect(models.DB_FILE) as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM checkins").fetchone()["n"]
    assert n == 1


def test_streak_api(monkeypatch):
    """GET /todo/api/streak：200、ok、recent 恰好 7 项且最后一项是今天。"""
    client = make_client(monkeypatch)
    resp = client.get("/todo/api/streak")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    s = data["streak"]
    assert len(s["recent"]) == 7
    assert s["recent"][-1]["is_today"] is True
    assert {"current", "pending_today", "last_day", "longest", "total", "recent", "milestone"} == set(s.keys())


def test_greet_button_is_button_not_link(monkeypatch):
    """「打个招呼」必须是 <button>（不跳转 /about）；页脚的 /about 链接保留。"""
    client = make_client(monkeypatch)
    text = client.get("/").text
    assert '<button type="button" class="btn btn-primary" id="greet-btn"' in text
    m = re.search(r'<button[^>]*id="greet-btn"[^>]*>', text)
    assert m and "href" not in m.group(0)    # 按钮本身无 href，点击不跳转
    assert '<a class="footer-links' in text or '/about">关于</a>' in text  # 页脚关于入口保留


def test_no_inline_script_and_no_external_refs(monkeypatch):
    """CSP 回归锁：无内联 <script>；link/script/img 标签零外部域引用。"""
    client = make_client(monkeypatch)
    for page in ["/", "/about", "/notes", "/todo", "/no-such-page"]:
        text = client.get(page).text
        # 所有 <script> 必须带 src 外置（负向前瞻：无 src 属性的内联 script 不允许）
        assert not re.search(r"<script(?![^>]*\bsrc=)", text), page
        # link/script/img 三类资源标签的 href/src 不得指向外部域
        # （只看属性值开头的协议：favicon 的 data: URI 里可能含 xmlns='http://...' 字样，那是 XML 命名空间不是请求）
        for tag in re.findall(r"<(?:link|script|img)[^>]*>", text):
            for attr in re.finditer(r'(?:href|src)=["\']([^"\']*)["\']', tag):
                url = attr.group(1)
                assert not url.startswith(("http://", "https://", "//")), (page, url)
