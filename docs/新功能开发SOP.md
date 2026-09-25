# 新功能开发 SOP

> 从一个想法到上线打 tag 的完整流程。全程**不改 core/**。

## 流程总览

```
想法 → feature 分支 → 复制 _template → 开发+测试 → 合入 develop → 验证 → 合入 main → 打 tag → 服务器更新
```

## 第 1 步：拉最新代码，建功能分支

```bash
cd 你的工作目录/qimiao
git checkout develop
git pull
git checkout -b feature/daily-notes        # 分支名用英文，见名知意
```

> 什么时候用哪种分支：`main` = 线上在跑的版本，只进发过的 tag；`develop` = 开发主线；
> `feature/*` = 一个功能一条分支；`fix/*` = 修 bug。

## 第 2 步：复制脚手架，起个名字

```bash
cp -r modules/_template modules/daily_notes        # 目录名：英文小写下划线
```

模块命名规范：目录名/manifest 的 `name` 用 `snake_case`；`prefix` 用 `/short-name`（短横线）。

## 第 3 步：改模块清单

编辑 `modules/daily_notes/__init__.py`：

```python
MODULE = ModuleManifest(
    name="daily_notes",
    title="每日随笔",
    prefix="/daily-notes",
    description="每天记三句，攒一本小书。",
    version="0.1.0",
    nav_label="随笔",
    nav_order=20,
    card_badge="v0.1 · 新上",
)
```

## 第 4 步：写功能

按需改这几个文件（脚手架已备好骨架）：

| 文件 | 写什么 |
|---|---|
| `router.py` | 页面路由 + JSON 接口 |
| `templates/daily_notes/index.html` | 页面（extends "base.html"，全局导航页脚自动有） |
| `static/daily_notes.css` | 模块私有样式（只用全站设计令牌，别定义全局规则） |
| 新增 `models.py` | 需要存数据时（参考 todo 模块：`with connect("daily_notes.db") as conn`） |

`.env` 里登记启用（本地开发用）：

```
MODULES_ENABLED=todo,daily_notes
```

## 第 5 步：本地验证

```bash
# 装依赖（首次）
python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt

# 跑起来看效果（改代码自动重载）
uvicorn main:app --reload

# 跑全量测试（确保没弄坏别的模块）
pytest
```

顺手验证三件事：新模块页面正常、首页出现新卡片、把 `.env` 里新模块删掉后整站依旧正常。

建议在 `tests/test_app.py` 加一条你的模块的测试（复制 `test_todo_page_and_api_flow` 改改）。

## 第 6 步：提交（Conventional Commits）

```bash
git add modules/daily_notes tests/
git commit -m "feat(daily-notes): 每日随笔模块——页面+接口+独立数据库"
```

类型速查：`feat` 新功能 · `fix` 修 bug · `docs` 只改文档 · `chore` 构建/工具 · `refactor` 重构 · `test` 补测试。

范围（括号里）写模块名；一行说清楚「做了什么」，不看代码也能懂。

## 第 7 步：合入 develop，自测通过后合入 main

```bash
git checkout develop
git merge --no-ff feature/daily-notes
# … 在 develop 上把玩一阵子，确认没问题 …
git checkout main
git merge --no-ff develop
git push origin main develop
```

## 第 8 步：打 tag 发版

版本号规则（语义化版本）：`v主版本.次版本.修订号`
- 加了新模块/新页面 → 次版本 +1（v0.1.0 → v0.2.0）
- 修 bug / 小调整 → 修订号 +1（v0.1.0 → v0.1.1）
- 大改架构 → 主版本 +1（v1.0.0）

```bash
git tag -a v0.2.0 -m "新增每日随笔模块"
git push origin v0.2.0
```

## 第 9 步：服务器更新

SSH 到服务器：

```bash
cd /opt/qimiao
git pull
docker compose -f deploy/docker-compose.yml up -d --build
```

顺手把 `.env` 的 `MODULES_ENABLED` 加上新模块名（如果还没加）：
`nano .env` → 改 `MODULES_ENABLED=todo,daily_notes` → 保存后 `docker compose -f deploy/docker-compose.yml restart`。

浏览器验证，收工。

---

## 上线前自查清单

- [ ] `pytest` 全绿
- [ ] 首页出现新模块卡片，点击可进入
- [ ] 新模块页面在手机上（或浏览器窄窗口）显示正常
- [ ] 从 `.env` 临时去掉新模块名重启后，整站其余功能正常
- [ ] 没有动过 `core/` 下的任何文件（`git diff main -- core/` 应为空）
- [ ] 打了 tag 并推送

## 万一线上出问题

```bash
bash scripts/rollback.sh     # 一键回到上一个版本
```

详细说明见《日常维护手册.md》。
