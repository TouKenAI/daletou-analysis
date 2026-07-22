# 仓库描述 / Repository Description (About)

> 以下内容用于 GitHub 仓库的 **About** 描述栏（建议中英文都放，或二选一）。

## 中文（推荐填这一条，≤160 字符）

```
大乐透(体彩)标准分析流程: 5步法数据存档→前区分区→后区搭配→选号约束→成品号码, 叠加最大覆盖优化引擎与蒙特卡洛复查。纯Python标准库, 可复现, 零预测力声明。
```

## English

```
Standard Super Lotto (Chinese Sports Lottery) analysis pipeline: 5-step data archival → zone check → back-number rules → selection constraints → final numbers, plus max-coverage optimizer and Monte-Carlo review. Pure stdlib, reproducible, zero-prediction disclaimer.
```

---

# 发布步骤 / How to Publish

## 前置条件
1. 一个 GitHub 账号（如 `cg38121-creator`）。
2. 生成一个 **Personal Access Token (PAT)**：
   - 路径：GitHub → 右上角头像 → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token**
   - 勾选 **`repo`**（全选该组）权限
   - 设个过期时间（如 30 天），生成后**立即复制保存**（只显示一次）
3. **不要使用 GitHub 登录密码** —— 自 2021-08 起 GitHub 已废除密码登录 git，用密码推会直接 401 失败。

## 方式 A：本机 Git Bash 一键发布（推荐）

```bash
cd /path/to/daletou-analysis        # 进入本 skill 目录
export GH_TOKEN=你的PAT             # 粘贴上面生成的令牌
bash publish.sh                     # 一键 init+commit+push
```

推送成功后，去仓库 **Settings → About** 把上面的中文/英文描述贴进去，并勾选：
- ✅ Add a README
- ✅ Add a license (已含 MIT LICENSE 文件)

## 方式 B：GitHub 网页手动上传（无需 git）

1. 浏览器打开 https://github.com/new ，仓库名填 `daletou-analysis`，选 **Public**，勾 **Add a README**。
2. 创建后点 **Add file → Upload files**，把本目录全部文件拖进去，写 commit 信息，提交。
3. 在 About 填描述。

---

# 诚实边界（已写进每个产出文件，开源也保留）

- 大乐透每期开奖为**独立随机事件**，历史冷热/分区/胆码/连号对下一期**零预测力**。
- 一等奖单注中奖概率 **1 / 21,425,712**，任何选号策略都**无法提升**该概率。
- 本仓库所有脚本与号码**仅作数据归档、算法演示与娱乐参考**，**绝不构成任何购彩建议或中奖保证**。
- 返奖率约 51%，长期购买数学期望必亏——请理性看待，量力而行。
