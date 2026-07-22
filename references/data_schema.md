# 数据格式与更新方法（大乐透）

## 单一数据源

所有分析从 `analyze.py` 生成的 `dlt_raw_21.csv` 出发，下游脚本全部读取它（及彼此产出的 CSV），保证口径一致。

## 原始数据格式（`dlt_raw_21.csv`）

UTF-8 with BOM，表头：

```
期号,开奖日期,前区1,前区2,前区3,前区4,前区5,后区1,后区2
2026079,2026-07-15,06,08,23,26,27,05,12
...
```

- 期号：整数（如 2026079）
- 前区：5 个 01–35 不重复两位数
- 后区：2 个 01–12 不重复两位数
- **顺序：最新一期在前**（索引 0 = 最新），`analyze.py` 的遗漏计算依赖此约定

## 内置默认数据

`analyze.py` 的 `RAW` 列表硬编码了默认 21 期（第 2026059–2026079 期，截至 2026-07-15），便于开箱即用与复现。更新方法：

1. 打开 `scripts/analyze.py`，找到 `RAW = [ ... ]`
2. 把最新一期插入列表**最前**（`(期号, "日期", [前区5], [后区2])`）
3. 删除列表**最后**一行（维持 21 期窗口）
4. 重跑 `analyze.py` → `zone_check.py` → `back_rule.py` → `select_ref.py` → `final_numbers.py`（及可选优化）

## 关键中间产物（下游脚本读取）

| 文件 | 生产者 | 被谁消费 |
|---|---|---|
| `dlt_raw_21.csv` | analyze | 所有步骤 |
| `dlt_front_coldhot.csv` | analyze | final_numbers |
| `dlt_back_coldhot.csv` | analyze | back_rule, final_numbers |
| `dlt_zone_check.csv` | zone_check | — |
| `dlt_back_valid_combo.csv` | back_rule | final_numbers, dlt_maxcover, dlt_review |
| `dlt_sel_ref.csv` | select_ref | — |
| `dlt_23_danma.csv` | select_ref | final_numbers, dlt_maxcover, dlt_review |
| `dlt_final_groups.csv` | final_numbers | — |
| `dlt_maxcover_groups.csv` | dlt_maxcover | — |

## 路径与可移植性

- 所有脚本默认把数据/产出写入「脚本同级 `../data/`」
- 可用环境变量覆盖：`DLT_DATA_DIR=/your/path python analyze.py`
- 无第三方依赖，仅 Python 标准库

## 数据质量校验（analyze.py 内置）

- 期次连续（相邻期号差 1）
- 每期前区 5 个 / 后区 2 个，且无重复
- 前区 01–35、后区 01–12 无越界
- 任何异常会打印 `校验错误: [...]`；为空则 `无`
