# -*- coding: utf-8 -*-
"""
大乐透前区三区校验
分区口径: 一区 01-10 / 二区 11-20 / 三区 21-35
校验规则: 每期5个前区号必须三区全覆盖(每区≥1个)
数据源: 已存档 dlt_raw_21.csv (第2026059-2026079期, 共21期)
"""
import csv, os

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("DLT_DATA_DIR", os.path.join(_HERE, "..", "data"))
os.makedirs(OUT_DIR, exist_ok=True)

# ---- 读取已存档原始数据 ----
rows = []
with open(f"{OUT_DIR}/dlt_raw_21.csv", encoding="utf-8-sig") as fp:
    for row in csv.DictReader(fp):
        front = [int(row[f"前区{i}"]) for i in range(1,6)]
        rows.append((row["期号"], row["开奖日期"], front))

def zone(n):
    if 1 <= n <= 10: return "一区"
    if 11 <= n <= 20: return "二区"
    return "三区"

# ---- 逐期分区校验 ----
detail = []  # (期号, 日期, 一区数, 二区数, 三区数, 是否全覆盖)
for pid, dt, f in rows:
    c = {"一区":0,"二区":0,"三区":0}
    for n in f: c[zone(n)] += 1
    full = all(v >= 1 for v in c.values())
    detail.append((pid, dt, c["一区"], c["二区"], c["三区"], full))

N = len(detail)
pass_n = sum(1 for d in detail if d[5])
fail_n = N - pass_n
pass_rate = pass_n / N * 100

# ---- 各区总出号频次 (21期共105个前区位置) ----
zone_total = {"一区":0,"二区":0,"三区":0}
for d in detail:
    zone_total["一区"] += d[2]; zone_total["二区"] += d[3]; zone_total["三区"] += d[4]

# 分布模式统计 (如 2-2-1)
from collections import Counter
pattern = Counter(f"{d[2]}-{d[3]}-{d[4]}" for d in detail)

print(f"总期数: {N}  满足三区全覆盖: {pass_n}  不满足: {fail_n}  满足率: {pass_rate:.1f}%")
print("各区总出号:", zone_total, " 合计:", sum(zone_total.values()))
print("分布模式:", dict(pattern))

# ---- 输出CSV ----
with open(f"{OUT_DIR}/dlt_zone_check.csv","w",newline="",encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["期号","开奖日期","一区(01-10)出号数","二区(11-20)出号数","三区(21-35)出号数","三区全覆盖(每区≥1)"])
    for pid,dt,a,b,c,full in detail:
        w.writerow([pid,dt,a,b,c,"✓ 满足" if full else "✗ 缺失"])

# ---- HTML 校验报告 ----
rows_html = ""
for pid,dt,a,b,c,full in detail:
    mark = "✓" if full else "✗"
    cls = "ok" if full else "bad"
    miss = [z for z,(cnt) in zip(["一区","二区","三区"],[a,b,c]) if cnt==0]
    note = "" if full else f' <span class="miss">缺{"/".join(miss)}</span>'
    rows_html += f"<tr><td>{pid}</td><td>{dt}</td><td>{a}</td><td>{b}</td><td>{c}</td><td class='{cls}'>{mark}{note}</td></tr>\n"

pat_html = " ".join(f"<span class='tag'>{k} ×{v}</span>" for k,v in pattern.most_common())

html = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>大乐透前区三区校验</title>
<style>
 *{{box-sizing:border-box;font-family:-apple-system,"Microsoft YaHei",sans-serif}}
 body{{margin:0;background:#f5f7fa;color:#222;padding:24px}}
 .wrap{{max-width:860px;margin:0 auto}}
 h1{{font-size:22px;margin:0 0 4px}} .sub{{color:#666;font-size:13px;margin-bottom:18px}}
 .card{{background:#fff;border-radius:10px;padding:18px 20px;margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
 .kv{{display:flex;gap:22px;flex-wrap:wrap;font-size:14px;margin:8px 0}}
 .big{{font-size:30px;font-weight:700}} .ok{{color:#27ae60}} .bad{{color:#e74c3c}}
 .pill{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:13px;background:#eaf3fb;color:#2980b9;margin:2px}}
 .miss{{color:#e74c3c;font-size:12px}}
 table{{width:100%;border-collapse:collapse;font-size:13px}}
 th,td{{padding:6px 8px;border-bottom:1px solid #eee;text-align:center}}
 th{{background:#fafafa;color:#555}}
 .note{{font-size:12px;color:#888;line-height:1.7}}
 .tag{{display:inline-block;padding:2px 8px;background:#f0f0f0;border-radius:4px;font-size:12px;margin:2px}}
</style></head><body><div class="wrap">
<h1>📊 大乐透前区三区校验报告</h1>
<div class="sub">分区口径: 一区 01-10 ｜ 二区 11-20 ｜ 三区 21-35 ｜ 校验规则: 每期5个前区号须三区全覆盖(每区≥1)
｜ 数据: 第2026059–2026079期 (共{N}期)</div>

<div class="card">
  <div class="kv">
    <div><div class="big ok">{pass_n}</div><div>满足全覆盖</div></div>
    <div><div class="big bad">{fail_n}</div><div>未满足(缺失某区)</div></div>
    <div><div class="big">{pass_rate:.1f}%</div><div>历史满足率</div></div>
  </div>
  <div class="note">说明: 大乐透官方<b>无</b>"三区必须全覆盖"之规定, 此为自定义选号/过滤约束。历史{N}期中仅 {pass_n} 期满足, 即该约束会过滤掉 {fail_n} 期 ({fail_n/N*100:.1f}%) 的历史开奖组合。若作为选号硬性条件, 将系统性排除这些形态。</div>
</div>

<div class="card">
  <h3 style="margin-top:0">各区总出号频次 (21期共105个前区位置)</h3>
  <div class="kv">
    <span class="pill">一区 01-10: <b>{zone_total['一区']}</b> 次 ({zone_total['一区']/N:.2f}/期)</span>
    <span class="pill">二区 11-20: <b>{zone_total['二区']}</b> 次 ({zone_total['二区']/N:.2f}/期)</span>
    <span class="pill">三区 21-35: <b>{zone_total['三区']}</b> 次 ({zone_total['三区']/N:.2f}/期)</span>
  </div>
  <div class="note">三区号码池(15个)最大, 理论出号占比应最高; 一区/二区号码池各10个。实际分布详见下表逐期校验。</div>
</div>

<div class="card">
  <h3 style="margin-top:0">分布模式统计 (一区-二区-三区 出号数)</h3>
  <div>{pat_html}</div>
</div>

<div class="card">
  <h3 style="margin-top:0">📋 逐期分区校验明细</h3>
  <table><thead><tr><th>期号</th><th>日期</th><th>一区(01-10)</th><th>二区(11-20)</th><th>三区(21-35)</th><th>校验</th></tr></thead>
  <tbody>{rows_html}</tbody></table>
</div>

<div class="card note">
  ⚠️ <b>理性购彩提示:</b> 本校验仅描述历史开奖数据的分区形态分布, 彩票每期开奖为独立随机事件, 历史分布不预示未来。
  三区全覆盖仅为分析者自定义条件, 非官方规则。请量力而行。
  存档: dlt_zone_check.csv
</div>
</div></body></html>'''

with open(f"{OUT_DIR}/大乐透前区三区校验.html","w",encoding="utf-8") as fp:
    fp.write(html)
print("\n报告已生成。存档:", sorted(os.listdir(OUT_DIR)))
