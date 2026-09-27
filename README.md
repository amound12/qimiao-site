# 奇妙小站

> 慢慢做，不着急。🏠 手工搭建的模块化个人小站，拒绝模板脸。

FastAPI + Jinja2 + SQLite · Docker Compose 部署 · 乐高式模块架构

## 这是个什么站

个人自用小站 v0.1.0。核心是「乐高式模块化」：每个功能是一块独立积木
（`modules/` 下一个目录），自带路由/页面/数据库/静态资源，可单独启停、
随时拆装，**新增功能永不修改核心代码**。

当前积木：
- **每日待办** `/todo` —— 增删勾选、连续打卡统计（新模块开发参考模板）

核心页面：首页（模块卡片墙）· 关于 · 404

## 本地开发

```bash
python -m venv .venv
. .venv/bin/activate                  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn main:app --reload             # 打开 http://127.0.0.1:8000
```

跑测试：

```bash
pytest
```

## 部署

照着《docs/部署手册.md》从零到上线，面向「会用 SSH 但不精通运维」的人。

## 文档索引

| 文档 | 内容 |
|---|---|
| [docs/架构说明.md](docs/架构说明.md) | 目录结构、模块注册机制、如何新增/禁用模块 |
| [docs/部署手册.md](docs/部署手册.md) | 服务器从零部署：Docker + Nginx + HTTPS（裸命令版） |
| [docs/部署手册-宝塔面板版.md](docs/部署手册-宝塔面板版.md) | 阿里云 + 宝塔面板专用版（反代/SSL/定时备份走宝塔） |
| [docs/日常维护手册.md](docs/日常维护手册.md) | 更新、备份、恢复、回滚、看日志、排障 |
| [docs/新功能开发SOP.md](docs/新功能开发SOP.md) | 从建分支到上线打 tag 的完整流程 |

## 快速上手模块化

```bash
# 新功能三步走（详见架构说明）
cp -r modules/_template modules/your_module   # 1. 复制脚手架
# 2. 改 modules/your_module/__init__.py 的 MODULE 清单
# 3. .env 里 MODULES_ENABLED=todo,your_module，重启生效
```

## 版本

- v0.1.1 —— 加固：字体自托管（不再依赖 Google Fonts）、修复模块静态资源挂载、接口 404 语义、
  空白内容校验、安全响应头 + CSP、静态缓存头、/healthz 健康检查、SQLite WAL、CI 流水线
- v0.1.0 —— 首版：核心框架 + 首页/关于/404 + 每日待办模块
