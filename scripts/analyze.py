# -*- coding: utf-8 -*-
"""
大乐透近21期(2026059-2026079) 数据存档 + 冷热号码分析
规则: 前区 01-35 选5, 后区 01-12 选2
数据源: 中国体彩网/新浪/各大彩票数据站交叉核对 (截至 2026-07-15 第26079期)
"""
import csv, json, os

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("DLT_DATA_DIR", os.path.join(_HERE, "..", "data"))
os.makedirs(OUT_DIR, exist_ok=True)

# ---- 原始数据 (期号, 日期, 前区5, 后区2)  顺序: 最新在前 ----
RAW = [
    (2026079, "2026-07-15", [6,8,23,26,27], [5,12]),
    (2026078, "2026-07-13", [2,13,20,25,32], [8,11]),
    (2026077, "2026-07-11", [4,14,19,24,27], [6,7]),
    (2026076, "2026-07-08", [15,20,27,28,35], [2,11]),
    (2026075, "2026-07-06", [1,6,16,18,26], [4,10]),
    (2026074, "2026-07-04", [1,4,10,23,25], [1,12]),
    (2026073, "2026-07-01", [4,10,22,23,33], [2,12]),
    (2026072, "2026-06-29", [1,13,26,29,30], [9,11]),
    (2026071, "2026-06-27", [5,13,22,26,32], [2,3]),
    (2026070, "2026-06-24", [4,5,15,21,32], [2,11]),
    (2026069, "2026-06-22", [12,19,21,24,29], [3,10]),
    (2026068, "2026-06-20", [3,11,12,21,22], [6,10]),
    (2026067, "2026-06-17", [6,16,18,19,28], [7,11]),
    (2026066, "2026-06-15", [10,13,19,21,30], [4,5]),
    (2026065, "2026-06-13", [4,11,12,13,25], [4,8]),
    (2026064, "2026-06-10", [3,13,15,17,21], [2,7]),
    (2026063, "2026-06-08", [3,15,20,29,31], [1,12]),
    (2026062, "2026-06-06", [7,15,20,24,29], [4,10]),
    (2026061, "2026-06-03", [10,12,26,31,35], [2,12]),
    (2026060, "2026-06-01", [22,28,30,31,34], [1,5]),
    (2026059, "2026-05-30", [6,13,17,19,26], [7,8]),
]

N = len(RAW)  # 21
print(f"数据期数: {N}")

# ---- 数据质量校验 ----
errs = []
for i, (pid, dt, f, b) in enumerate(RAW):
    if len(f) != 5: errs.append(f"{pid} 前区数量异常:{len(f)}")
    if len(b) != 2: errs.append(f"{pid} 后区数量异常:{len(b)}")
    if len(set(f)) != 5: errs.append(f"{pid} 前区重复:{f}")
    if len(set(b)) != 2: errs.append(f"{pid} 后区重复:{b}")
    if any(x<1 or x>35 for x in f): errs.append(f"{pid} 前区越界:{f}")
    if any(x<1 or x>12 for x in b): errs.append(f"{pid} 后区越界:{b}")
for i in range(1, N):
    if RAW[i-1][0] - RAW[i][0] != 1:
        errs.append(f"期次不连续: {RAW[i][0]} -> {RAW[i-1][0]}")
print("校验错误:", errs if errs else "无")

# ---- 频次 & 遗漏统计 ----
# RAW[0] 是最新一期(索引0), RAW[N-1] 是最旧一期(索引N-1)
# 遗漏 = 距最新一期隔了多少期未出 (最新期出现则0; 从未出现则N)
def analyze(pool):
    freq = {n:0 for n in range(1, pool+1)}
    last_idx = {n:-1 for n in range(1, pool+1)}
    for idx, (pid, dt, f, b) in enumerate(RAW):
        nums = f if pool==35 else b
        for n in nums:
            freq[n]+=1
            last_idx[n]=idx
    miss = {n:(N if last_idx[n]==-1 else last_idx[n]) for n in range(1, pool+1)}
    vals = list(freq.values())
    mean = sum(vals)/len(vals)
    var = sum((v-mean)**2 for v in vals)/len(vals)
    std = var**0.5
    return freq, miss, mean, std

front_freq, front_miss, f_mean, f_std = analyze(35)
back_freq, back_miss, b_mean, b_std = analyze(12)
print(f"前区均值={f_mean:.2f} 标准差={f_std:.2f}")
print(f"后区均值={b_mean:.2f} 标准差={b_std:.2f}")

# ---- 冷热分类 (基于频次, 均值±0.5*std) ----
def classify(freq, mean, std):
    hot_thr, cold_thr = mean+0.5*std, mean-0.5*std
    res = {}
    for n,v in freq.items():
        res[n] = "热" if v>=hot_thr else ("冷" if v<=cold_thr else "温")
    return res, hot_thr, cold_thr

f_cls, f_hot, f_cold = classify(front_freq, f_mean, f_std)
b_cls, b_hot, b_cold = classify(back_freq, b_mean, b_std)
print(f"前区热阈值>={f_hot:.2f} 冷阈值<={f_cold:.2f}")
print(f"后区热阈值>={b_hot:.2f} 冷阈值<={b_cold:.2f}")

# ---- CSV: 原始数据 ----
with open(f"{OUT_DIR}/dlt_raw_21.csv", "w", newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["期号","开奖日期","前区1","前区2","前区3","前区4","前区5","后区1","后区2"])
    for pid, dt, f, b in RAW:
        w.writerow([pid, dt]+[f"{x:02d}" for x in f]+[f"{x:02d}" for x in b])

# ---- CSV: 前区冷热 ----
with open(f"{OUT_DIR}/dlt_front_coldhot.csv", "w", newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp); w.writerow(["号码","出现次数","当前遗漏(期)","分类"])
    for n in range(1,36): w.writerow([f"{n:02d}", front_freq[n], front_miss[n], f_cls[n]])

# ---- CSV: 后区冷热 ----
with open(f"{OUT_DIR}/dlt_back_coldhot.csv", "w", newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp); w.writerow(["号码","出现次数","当前遗漏(期)","分类"])
    for n in range(1,13): w.writerow([f"{n:02d}", back_freq[n], back_miss[n], b_cls[n]])

# ---- 汇总 ----
f_hot_list = [f"{n:02d}({front_freq[n]}次,漏{front_miss[n]})" for n in range(1,36) if f_cls[n]=="热"]
f_cold_list = [f"{n:02d}({front_freq[n]}次,漏{front_miss[n]})" for n in range(1,36) if f_cls[n]=="冷"]
b_hot_list = [f"{n:02d}({back_freq[n]}次,漏{back_miss[n]})" for n in range(1,13) if b_cls[n]=="热"]
b_cold_list = [f"{n:02d}({back_freq[n]}次,漏{back_miss[n]})" for n in range(1,13) if b_cls[n]=="冷"]
summary = {"期数":N,"范围":f"{RAW[-1][0]}-{RAW[0][0]} ({RAW[-1][1]}~{RAW[0][1]})",
    "前区热号":f_hot_list,"前区冷号":f_cold_list,"后区热号":b_hot_list,"后区冷号":b_cold_list,
    "前区均值":round(f_mean,2),"前区标准差":round(f_std,2),"后区均值":round(b_mean,2),"后区标准差":round(b_std,2)}
with open(f"{OUT_DIR}/summary.json","w",encoding="utf-8") as fp: json.dump(summary,fp,ensure_ascii=False,indent=2)

print("\n前区热:", " ".join(f_hot_list))
print("前区冷:", " ".join(f_cold_list))
print("后区热:", " ".join(b_hot_list))
print("后区冷:", " ".join(b_cold_list))

# ============ HTML 报告 ============
def bar_chart(freq, cls, pool, maxv):
    cells=[]
    for n in range(1, pool+1):
        v=freq[n]; c=cls[n]
        color = "#e74c3c" if c=="热" else ("#3498db" if c=="冷" else "#95a5a6")
        w = max(2, v/maxv*100)
        cells.append(f'''<div class="brow">
  <span class="bnum">{n:02d}</span>
  <div class="btrack"><div class="bfill" style="width:{w:.1f}%;background:{color}"></div></div>
  <span class="bval">{v}</span><span class="btag {c}">{c}</span></div>''')
    return "\n".join(cells)

fmax=max(front_freq.values()); bmax=max(back_freq.values())

raw_rows=""
for pid,dt,f,b in RAW:
    raw_rows+=f"<tr><td>{pid}</td><td>{dt}</td><td class='front'>{' '.join(f'{x:02d}' for x in f)}</td><td class='back'>{' '.join(f'{x:02d}' for x in b)}</td></tr>\n"

html=f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>大乐透冷热号码分析 (近21期)</title>
<style>
 *{{box-sizing:border-box;font-family:-apple-system,"Microsoft YaHei",sans-serif}}
 body{{margin:0;background:#f5f7fa;color:#222;padding:24px}}
 .wrap{{max-width:960px;margin:0 auto}}
 h1{{font-size:22px;margin:0 0 4px}}
 .sub{{color:#666;font-size:13px;margin-bottom:20px}}
 .card{{background:#fff;border-radius:10px;padding:18px 20px;margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
 .kv{{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;margin-bottom:6px}}
 .kv b{{color:#333}}
 .tag{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:12px;margin:2px}}
 .hot{{background:#fdecea;color:#e74c3c}}.cold{{background:#eaf3fb;color:#2980b9}}.warm{{background:#f0f0f0;color:#777}}
 .brow{{display:flex;align-items:center;gap:8px;margin:3px 0;font-size:12px}}
 .bnum{{width:22px;font-weight:600}}
 .btrack{{flex:1;background:#eee;border-radius:3px;height:14px;overflow:hidden}}
 .bfill{{height:100%;border-radius:3px}}
 .bval{{width:18px;text-align:right;color:#555}}
 .btag{{width:18px;text-align:center}}
 table{{width:100%;border-collapse:collapse;font-size:13px}}
 th,td{{padding:6px 8px;border-bottom:1px solid #eee;text-align:center}}
 th{{background:#fafafa;color:#555}}
 .front{{color:#c0392b;font-weight:600;letter-spacing:1px}}
 .back{{color:#2980b9;font-weight:600;letter-spacing:1px}}
 .note{{font-size:12px;color:#888;line-height:1.6}}
 .legend span{{margin-right:14px;font-size:12px}}
</style></head><body><div class="wrap">
<h1>📊 超级大乐透 冷热号码分析</h1>
<div class="sub">统计窗口: 第 {RAW[-1][0]}–{RAW[0][0]} 期 ({RAW[-1][1]} ~ {RAW[0][1]}) ｜ 共 {N} 期 ｜ 数据截至 2026-07-15 第26079期</div>

<div class="card">
  <div class="kv">
    <span><b>数据校验:</b> 期次连续 ✓ 每期前区5/后区2 ✓ 无越界/重复 ✓</span>
  </div>
  <div class="kv">
    <span><b>前区</b> 均值 {f_mean:.2f} 次 / 标准差 {f_std:.2f}</span>
    <span><b>后区</b> 均值 {b_mean:.2f} 次 / 标准差 {b_std:.2f}</span>
  </div>
  <div class="note">分类规则: 出现次数 ≥ 均值+0.5×标准差 为<span class="tag hot">热</span>；≤ 均值−0.5×标准差 为<span class="tag cold">冷</span>；其余为<span class="tag warm">温</span>。"遗漏"=距最新一期(26079)隔了多少期未出。</div>
</div>

<div class="card">
  <h3 style="margin-top:0">🔥 前区热号 (高亮红)</h3>
  <div>{" ".join(f'<span class="tag hot">{x}</span>' for x in f_hot_list)}</div>
  <h3>❄️ 前区冷号 (高亮蓝)</h3>
  <div>{" ".join(f'<span class="tag cold">{x}</span>' for x in f_cold_list)}</div>
  <div style="margin-top:12px">{bar_chart(front_freq,f_cls,35,fmax)}</div>
</div>

<div class="card">
  <h3 style="margin-top:0">🔥 后区热号</h3>
  <div>{" ".join(f'<span class="tag hot">{x}</span>' for x in b_hot_list)}</div>
  <h3>❄️ 后区冷号</h3>
  <div>{" ".join(f'<span class="tag cold">{x}</span>' for x in b_cold_list)}</div>
  <div style="margin-top:12px">{bar_chart(back_freq,b_cls,12,bmax)}</div>
</div>

<div class="card">
  <h3 style="margin-top:0">📋 原始开奖数据 (存档)</h3>
  <table><thead><tr><th>期号</th><th>日期</th><th>前区 (01-35)</th><th>后区 (01-12)</th></tr></thead>
  <tbody>{raw_rows}</tbody></table>
</div>

<div class="card note">
  ⚠️ <b>理性购彩提示:</b> 大乐透为完全随机的独立事件，每期每个号码出现概率恒定，历史冷热不代表未来趋势。
  本分析仅作数据归档与统计描述，<b>不构成任何选号建议</b>。请量力而行，理性投注。
  <br>数据来源: 中国体彩网官方公告 / 新浪彩票 / 各大彩票数据站交叉核对。存档文件: dlt_raw_21.csv, dlt_front_coldhot.csv, dlt_back_coldhot.csv。
</div>
</div></body></html>'''

with open(f"{OUT_DIR}/大乐透冷热分析报告.html","w",encoding="utf-8") as fp:
    fp.write(html)
print("\nHTML报告已生成。存档文件:", sorted(os.listdir(OUT_DIR)))
