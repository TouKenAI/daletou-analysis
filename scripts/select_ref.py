# -*- coding: utf-8 -*-
"""
任务4: 选号参考约束
- 前区连号分析 (排序后相邻差=1)
- 23区间(二区11-20 + 三区21-35)胆码筛选
- 杜绝号码扎堆单区 (某区出号>=4 视为扎堆)
- 输出每组区间分布明细
数据源: 已存档 dlt_raw_21.csv (第2026059-2026079期, 共21期)
"""
import csv, os
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("DLT_DATA_DIR", os.path.join(_HERE, "..", "data"))
os.makedirs(OUT_DIR, exist_ok=True)

# ---- 读取已存档原始数据 ----
rows = []
with open(f"{OUT_DIR}/dlt_raw_21.csv", encoding="utf-8-sig") as fp:
    for row in csv.DictReader(fp):
        front = sorted(int(row[f"前区{i}"]) for i in range(1, 6))
        rows.append((row["期号"], row["开奖日期"], front))

def zone(n):
    if 1 <= n <= 10: return "一区"
    if 11 <= n <= 20: return "二区"
    return "三区"

N = len(rows)

# ========== 1. 前区连号分析 ==========
def connec(front_sorted):
    """提取连号段, 返回 [(start,end,length), ...], 长度>=2"""
    groups = []
    i, n = 0, len(front_sorted)
    while i < n:
        j = i
        while j + 1 < n and front_sorted[j+1] - front_sorted[j] == 1:
            j += 1
        if j > i:
            groups.append((front_sorted[i], front_sorted[j], j - i + 1))
        i = j + 1
    return groups

conn_summary = []   # 逐期连号
conn_period_count = 0          # 含连号期数
conn_seg_total = 0             # 连号段总数
conn_len_counter = Counter()   # 按长度
conn_zone_counter = Counter()  # 连号段落区 (按段内每个号码)
for pid, dt, f in rows:
    segs = connec(f)
    if segs:
        conn_period_count += 1
    for s, e, ln in segs:
        conn_seg_total += 1
        conn_len_counter[ln] += 1
        for x in range(s, e + 1):
            conn_zone_counter[zone(x)] += 1
    detail = " / ".join(f"{s}-{e}" for s, e, _ in segs) if segs else "无"
    conn_summary.append((pid, dt, "✓" if segs else "✗", detail))

# ========== 2. 23区间(二区+三区)胆码筛选 ==========
# 统计 01-35 各号21期累计频次
freq = Counter()
for _, _, f in rows:
    for n in f:
        freq[n] += 1

# 二区(11-20)+三区(21-35) = 23区间
zone23 = [n for n in range(1, 36) if 11 <= n <= 35]
danma = []   # (号码, 频次, 区)
for n in zone23:
    danma.append((n, freq[n], zone(n)))
danma.sort(key=lambda x: (-x[1], x[0]))   # 频次降序

# 强胆(>=4次) / 中胆(3次)
strong = [(n, c, z) for n, c, z in danma if c >= 4]
mid = [(n, c, z) for n, c, z in danma if c == 3]

# 23区间内各小区出号分布 (21期累计)
zone23_zone_freq = {"二区": sum(c for n, c, z in danma if z == "二区"),
                    "三区": sum(c for n, c, z in danma if z == "三区")}

# ========== 3. 区间分布明细 + 扎堆检测 ==========
detail = []  # (期号,日期,一,二,三,模式,含连号,连号明细,扎堆,扎堆区)
for (pid, dt, f), (_, _, conn_mark, conn_detail) in zip(rows, conn_summary):
    c = {"一区":0,"二区":0,"三区":0}
    for n in f: c[zone(n)] += 1
    pattern = f"{c['一区']}-{c['二区']}-{c['三区']}"
    maxz = max(c.values())
    heap = maxz >= 4
    heap_zone = [z for z, v in c.items() if v >= 4]
    detail.append((pid, dt, c["一区"], c["二区"], c["三区"], pattern,
                   conn_mark, conn_detail,
                   "✗ 是" if heap else "✓ 否",
                   "/".join(heap_zone) if heap else "-"))

heap_n = sum(1 for d in detail if d[8].startswith("✗"))
# 单区最多分布
maxdist = (max(d[2] for d in detail), max(d[3] for d in detail), max(d[4] for d in detail))

print("="*50)
print("【前区连号分析】")
print(f"含连号期数: {conn_period_count}/{N} = {conn_period_count/N*100:.1f}%")
print(f"连号段总数: {conn_seg_total}  按长度: {dict(conn_len_counter)}")
print(f"连号落区(按段内号码): {dict(conn_zone_counter)}")
print("="*50)
print("【23区间(二区+三区)胆码筛选】")
print("二区11-20累计出号:", zone23_zone_freq["二区"], " 三区21-35累计出号:", zone23_zone_freq["三区"])
print("强胆(>=4次):", strong)
print("中胆(3次):", mid)
print("="*50)
print("【区间分布 / 扎堆检测】")
print(f"扎堆单区(某区>=4码)期数: {heap_n}/{N} = {heap_n/N*100:.1f}%")
print(f"各区单期最大出号数: 一区{maxdist[0]} 二区{maxdist[1]} 三区{maxdist[2]}")
print("="*50)

# ---- 输出CSV: 区间分布明细 ----
with open(f"{OUT_DIR}/dlt_sel_ref.csv", "w", newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["期号","开奖日期","一区(01-10)","二区(11-20)","三区(21-35)","分布模式","含连号","连号明细","扎堆单区","扎堆区"])
    for d in detail:
        w.writerow(d)

# ---- 输出CSV: 23区间胆码 ----
with open(f"{OUT_DIR}/dlt_23_danma.csv", "w", newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["号码","21期累计频次","所属区","胆码等级"])
    for n, c, z in danma:
        level = "强胆(>=4)" if c >= 4 else ("中胆(3次)" if c == 3 else "观察(<3)")
        w.writerow([f"{n:02d}", c, z, level])

# ========== HTML 报告 ==========
conn_rows_html = ""
for pid, dt, mark, d in conn_summary:
    cls = "ok" if mark == "✓" else "mut"
    conn_rows_html += f"<tr><td>{pid}</td><td>{dt}</td><td class='{cls}'>{mark}</td><td>{d}</td></tr>\n"

detail_rows_html = ""
for d in detail:
    hcls = "bad" if d[8].startswith("✗") else "ok"
    ccls = "ok" if d[6] == "✓" else "mut"
    detail_rows_html += (f"<tr><td>{d[0]}</td><td>{d[1]}</td><td>{d[2]}</td><td>{d[3]}</td>"
                         f"<td>{d[4]}</td><td>{d[5]}</td><td class='{ccls}'>{d[6]}</td>"
                         f"<td>{d[7]}</td><td class='{hcls}'>{d[8]}</td><td>{d[9]}</td></tr>\n")

danma_rows = ""
for n, c, z in danma:
    lvl = "强胆" if c >= 4 else ("中胆" if c == 3 else "观察")
    badge = "badge-strong" if c >= 4 else ("badge-mid" if c == 3 else "badge-low")
    bar = "■" * c + "□" * (max(7 - c, 0))
    danma_rows += f"<tr><td>{n:02d}</td><td>{c}</td><td>{z}</td><td><span class='{badge}'>{lvl}</span></td><td style='font-family:monospace;color:#888'>{bar}</td></tr>\n"

strong_str = "  ".join(f"{n:02d}({c}次·{z})" for n, c, z in strong)
weak_str = "  ".join(f"{n:02d}({c}次)" for n, c, z in mid)

html = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>大乐透选号参考约束</title>
<style>
 *{{box-sizing:border-box;font-family:-apple-system,"Microsoft YaHei",sans-serif}}
 body{{margin:0;background:#f5f7fa;color:#222;padding:24px}}
 .wrap{{max-width:920px;margin:0 auto}}
 h1{{font-size:22px;margin:0 0 4px}} .sub{{color:#666;font-size:13px;margin-bottom:18px}}
 .card{{background:#fff;border-radius:10px;padding:18px 20px;margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
 .kv{{display:flex;gap:22px;flex-wrap:wrap;font-size:14px;margin:8px 0}}
 .big{{font-size:30px;font-weight:700}} .ok{{color:#27ae60}} .bad{{color:#e74c3c}} .mut{{color:#999}}
 .pill{{display:inline-block;padding:4px 12px;border-radius:20px;font-size:13px;background:#eaf3fb;color:#2980b9;margin:3px 2px}}
 .note{{font-size:12px;color:#888;line-height:1.7}}
 .tag{{display:inline-block;padding:2px 8px;background:#f0f0f0;border-radius:4px;font-size:12px;margin:2px}}
 table{{width:100%;border-collapse:collapse;font-size:13px}}
 th,td{{padding:6px 8px;border-bottom:1px solid #eee;text-align:center}}
 th{{background:#fafafa;color:#555}}
 .badge-strong{{background:#fde8e8;color:#e74c3c;padding:1px 8px;border-radius:10px;font-size:12px}}
 .badge-mid{{background:#fef3e0;color:#e67e22;padding:1px 8px;border-radius:10px;font-size:12px}}
 .badge-low{{background:#eee;color:#999;padding:1px 8px;border-radius:10px;font-size:12px}}
 .rule{{background:#f0f7ff;border-left:4px solid #2980b9;padding:10px 14px;border-radius:4px;margin:8px 0;font-size:13px;line-height:1.8}}
 b.blue{{color:#2980b9}}
</style></head><body><div class="wrap">
<h1>📊 大乐透选号参考约束报告</h1>
<div class="sub">口径: 前区三区 一区01-10 / 二区11-20 / 三区21-35 ｜ 连号=排序后相邻差1 ｜ 23区间=二区+三区 ｜ 数据: 第2026059–2026079期 (共{N}期)</div>

<div class="card">
  <h3 style="margin-top:0">① 前区连号分析</h3>
  <div class="kv">
    <div><div class="big ok">{conn_period_count}</div><div>含连号期数 / {N}</div></div>
    <div><div class="big">{conn_period_count/N*100:.1f}%</div><div>历史含连号率</div></div>
    <div><div class="big">{conn_seg_total}</div><div>连号段总数</div></div>
  </div>
  <div class="pill">2连段: <b>{conn_len_counter.get(2,0)}</b></div>
  <div class="pill">3连段: <b>{conn_len_counter.get(3,0)}</b></div>
  <div class="pill">连号落一区: <b>{conn_zone_counter.get('一区',0)}</b> 段次</div>
  <div class="pill">连号落二区: <b>{conn_zone_counter.get('二区',0)}</b> 段次</div>
  <div class="pill">连号落三区: <b>{conn_zone_counter.get('三区',0)}</b> 段次</div>
  <div class="note">结论: 历史约 {conn_period_count/N*100:.0f}% 的期含连号, 连号以2连为主, 且<b>多落于三区(21-35)与二区(11-20)</b>。选号时可酌情预留1组连号, 但非强制。</div>
</div>

<div class="card">
  <h3 style="margin-top:0">② 23区间(二区+三区)胆码筛选</h3>
  <div class="kv">
    <div><div class="big">{zone23_zone_freq['二区']}</div><div>二区11-20累计出号</div></div>
    <div><div class="big">{zone23_zone_freq['三区']}</div><div>三区21-35累计出号</div></div>
    <div><div class="big">{len(strong)}</div><div>强胆号码(>=4次)</div></div>
  </div>
  <div class="rule">
    <b class="blue">强胆候选 (二区+三区高频号, 21期>=4次):</b><br>{strong_str}<br><br>
    <b class="blue">中胆候选 (3次):</b> {weak_str or "无"}
  </div>
  <table><thead><tr><th>号码</th><th>21期频次</th><th>所属区</th><th>等级</th><th>频次</th></tr></thead>
  <tbody>{danma_rows}</tbody></table>
  <div class="note">胆码筛选逻辑: 仅从二区(11-20)+三区(21-35)共25个号码中, 按21期累计出号频次排序, 高频者作强胆/中胆候选。一区(01-10)不纳入胆码池——契合"23区间胆码"约束。</div>
</div>

<div class="card">
  <h3 style="margin-top:0">③ 杜绝号码扎堆单区</h3>
  <div class="kv">
    <div><div class="big bad">{heap_n}</div><div>扎堆单区期数 / {N}</div></div>
    <div><div class="big">{heap_n/N*100:.1f}%</div><div>历史扎堆率</div></div>
  </div>
  <div class="rule"><b class="blue">选号约束:</b> 5个前区号分散于三区, <b>任一区出号数不得超过3 (即禁止单区>=4)</b>。历史上仅 {heap_n} 期出现单区>=4的极端形态(如 26060 期 0-0-5 全落三区), 占比 {heap_n/N*100:.1f}%, 属小概率。选号时应主动规避"5码挤单区"。</div>
</div>

<div class="card">
  <h3 style="margin-top:0">④ 每组区间分布明细 (逐期)</h3>
  <table><thead><tr><th>期号</th><th>日期</th><th>一区</th><th>二区</th><th>三区</th><th>模式</th><th>连号</th><th>连号明细</th><th>扎堆</th><th>扎堆区</th></tr></thead>
  <tbody>{detail_rows_html}</tbody></table>
</div>

<div class="card">
  <h3 style="margin-top:0">📋 选号参考总原则</h3>
  <div class="rule">
  1. <b>胆码池:</b> 优先从二区+三区强胆候选 {strong_str} 选取核心号。<br>
  2. <b>连号参考:</b> 历史{conn_period_count/N*100:.0f}%含连号, 可预留1组2连(多落二/三区), 不作硬性要求。<br>
  3. <b>防扎堆:</b> 5码强制三区分散, 任一区<=3码, 严禁单区>=4。<br>
  4. <b>组合建议:</b> 二区2码 + 三区2码 + 一区1码, 或 二区1码 + 三区3码 + 一区1码 等均衡形态, 规避 0-x-5 / 5-0-0 类极端。
  </div>
</div>

<div class="card note">
  ⚠️ <b>理性购彩提示:</b> 上述连号率、胆码频次、扎堆率均来自历史{N}期样本, 大乐透每期开奖为独立随机事件, 历史规律不预示未来, 不产生任何选号必然性。本约束仅作数据归档与参考, 不构成购彩建议。请量力而行。<br>
  存档: dlt_sel_ref.csv (区间分布明细) ｜ dlt_23_danma.csv (23区间胆码)
</div>
</div></body></html>'''

with open(f"{OUT_DIR}/大乐透选号参考约束.html", "w", encoding="utf-8") as fp:
    fp.write(html)
print("\n报告已生成。存档:", sorted(os.listdir(OUT_DIR)))
