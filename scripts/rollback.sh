#!/usr/bin/env bash
# 一键回滚到上一个 Git tag（用法见 docs/日常维护手册.md）
# 原理：tag 是每个可上线版本的快照 → checkout 上一个 tag → 重建容器
set -euo pipefail
cd "$(dirname "$0")/.."

CURRENT=$(git describe --tags --abbrev=0 2>/dev/null || echo "（无tag，工作区状态）")
PREV=$(git tag --sort=-creatordate | sed -n '2p')

if [ -z "$PREV" ]; then
    echo "没有更早的版本可回滚（当前至少是第一个 tag）"
    exit 1
fi

echo "==> 当前版本：$CURRENT"
echo "==> 将回滚到：$PREV"
read -r -p "确认回滚？(y/N) " ans
if [ "$ans" != "y" ]; then
    echo "已取消"
    exit 0
fi

git checkout "$PREV"
docker compose -f deploy/docker-compose.yml up -d --build

echo "==> 已回滚到 $PREV 并重启完成"
echo "==> 数据不受影响（data/ 目录独立于代码版本）"
echo "==> 如果想再滚回来：git checkout $CURRENT && docker compose -f deploy/docker-compose.yml up -d --build"
