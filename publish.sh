#!/usr/bin/env bash
# ============================================================
# 大乐透标准分析流程 (daletou-analysis) — 一键发布到 GitHub
# ============================================================
# 重要: GitHub 自 2021-08 起已废除「账号密码」登录 git 操作,
#        必须使用 Personal Access Token (PAT, 勾选 repo 权限)。
#        本脚本绝不硬编码任何密码, 令牌只从环境变量/参数读取。
#
# 用法:
#   export GH_TOKEN=你的PAT
#   bash publish.sh
#   或: GH_TOKEN=你的PAT bash publish.sh
#   或: bash publish.sh 你的PAT
#
# 默认推到 (把下面 REPO_URL 改成你自己的仓库):
#   https://github.com/TouKenAI/daletou-analysis.git
# ============================================================
set -e

# ---- 可配置项 ----
REPO_URL="${REPO_URL:-https://github.com/TouKenAI/daletou-analysis.git}"
COMMIT_MSG="${COMMIT_MSG:-feat: 大乐透标准分析流程 skill v1 (5步法+最大覆盖优化+蒙特卡洛复查)}"

# ---- 读取令牌 ----
TOKEN="${GH_TOKEN:-$1}"
if [ -z "$TOKEN" ]; then
  echo "❌ 未提供 GitHub Personal Access Token (PAT, 需 repo 权限)"
  echo "   用法: GH_TOKEN=你的PAT bash publish.sh"
  echo "   生成地址: GitHub → Settings → Developer settings → Personal access tokens"
  exit 1
fi

# ---- 构造带令牌的远端地址 (仅运行时内存中存在) ----
AUTH_URL="https://${TOKEN}@${REPO_URL#https://}"

echo "📦 初始化仓库..."
git init -q
git branch -M main

echo "➕ 添加全部文件..."
git add -A

echo "💬 提交..."
git commit -q -m "$COMMIT_MSG"

echo "🔗 配置远端: $REPO_URL"
git remote remove origin 2>/dev/null || true
git remote add origin "$AUTH_URL"

echo "🚀 推送 main 分支..."
git push -u origin main

# 推送后清理远端里的令牌 (避免 git remote -v 泄露)
git remote set-url origin "$REPO_URL"

echo "✅ 已发布到 $REPO_URL"
echo "🌐 访问你的仓库查看, 并在 Settings → About 填写下方描述文本 (见 REPO_ABOUT.md)"
