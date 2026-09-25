#!/usr/bin/env bash
# 备份：data/（全部模块数据库）+ .env → backups/
# 用法：./scripts/backup.sh   （建议配 crontab 每天跑，见 docs/日常维护手册.md）
set -euo pipefail
cd "$(dirname "$0")/.."

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

echo "==> 打包 data/ 与 .env"
tar -czf "$BACKUP_DIR/qimiao-$TIMESTAMP.tar.gz" data .env

echo "==> 只保留最近 14 份，更旧的自动清理"
ls -1t "$BACKUP_DIR"/qimiao-*.tar.gz 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "==> 完成：$BACKUP_DIR/qimiao-$TIMESTAMP.tar.gz"
