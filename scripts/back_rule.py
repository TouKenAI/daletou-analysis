# -*- coding: utf-8 -*-
"""
大乐透后区冷热搭配规则
规则:
  1) 划分后区冷热号 (沿用任务1口径: 频次 ≥均值+0.5std 为热, ≤均值-0.5std 为冷)
  2) 两码和值锁定 9-16 (含端点)
  3) 禁止全冷 / 全热组合 (两码不能同为冷, 也不能同为热)
数据源: 已存档 dlt_raw_21.csv (第2026059-2026079期, 共21期)
"""
import csv, os, itertools
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("DLT_DATA_DIR", os.path.join(_HERE, "..", "data"))
os.makedirs(OUT_DIR, exist_ok=True)

# ---- 读取后区数据并重算冷热 ----
backs = []
with open(f"{OUT_DIR}/dlt_raw_21.csv", encoding="utf-8-sig") as fp:
    for row in csv.DictReader(fp):
        backs.append([int(row[f"后区{i}"]) for i in range(1,3)])

freq = {n:0 for n in range(1,13)}
for b in backs:
    for n in b: freq[n]+=1
mean = sum(freq.values())/12
std = (sum((v-mean)**2 for v in freq.values())/12)**0.5
hot_thr, cold_thr = mean+0.5*std, mean-0.5*std
def cls(n):
    v=freq[n]
    return "热" if v>=hot_thr else ("冷" if v<=cold_thr else "温")

print(f"后区均值={mean:.2f} 标准差={std:.2f}  热阈≥{hot_thr:.2f} 冷阈≤{cold_thr:.2f}")
print("后区分频:", {f"{n:02d}":freq[n] for n in range(1,13)})
hot = [n for n in range(1,13) if cls(n)=="热"]
cold = [n for n in range(1,13) if cls(n)=="冷"]
warm = [n for n in range(1,13) if cls(n)=="温"]
print(f"热号:{hot}  冷号:{cold}  温号:{warm}")

# ---- 枚举全部 C(12,2)=66 组合, 应用规则 ----
all_combs = list(itertools.combinations(range(1,13),2))
def is_valid(a,b):
    if not (9 <= a+b <= 16): return False
    if cls(a)=="冷" and cls(b)=="冷": return False   # 全冷
    if cls(a)=="热" and cls(b)=="热": return False   # 全热
    return True

valid, forbidden = [], []
for a,b in all_combs:
    if is_valid(a,b): valid.append((a,b))
    else: forbidden.append((a,b))

type_cnt = Counter()
for a,b in valid:
    type_cnt["".join(sorted([cls(a),cls(b)]))]+=1

print(f"\n全部组合数:{len(all_combs)}  合法组合:{len(valid)}  被禁组合:{len(forbidden)}")
print("合法组合类型分布:", dict(type_cnt))

# ---- 历史21期回测 ----
hist_pass, hist_fail = [], []
for i,(b1,b2) in enumerate(backs):
    a,b = sorted(b1+b2 if False else (b1,b2))
    ok = is_valid(min(b1,b2), max(b1,b2))
    (hist_pass if ok else hist_fail).append((2026079-i, b1, b2, min(b1,b2)+max(b1,b2)))
print(f"历史满足规则期数:{len(hist_pass)}/{len(backs)}  不满足:{len(hist_fail)}")

# ---- CSV: 后区冷热划分 ----
with open(f"{OUT_DIR}/dlt_back_hotcold.csv","w",newline="",encoding="utf-8-sig") as fp:
    w=csv.writer(fp); w.writerow(["号码","出现次数","分类"])
    for n in range(1,13): w.writerow([f"{n:02d}",freq[n],cls(n)])

# ---- CSV: 合法组合 ----
with open(f"{OUT_DIR}/dlt_back_valid_combo.csv","w",newline="",encoding="utf-8-sig") as fp:
    w=csv.writer(fp); w.writerow(["组合","和值","类型(冷热温)"])
    for a,b in valid:
        w.writerow([f"{a:02d}+{b:02d}", a+b, "".join(sorted([cls(a),cls(b)]))])

# ---- HTML 说明报告 ----
def combo_rows_html(combs, clsmap):
    return "\n".join(
        f"<tr><td>{a:02d} + {b:02d}</td><td>{a+b}</td><td class='{clsmap(a,b)}'>{''.join(sorted([cls(a),cls(b)]))}</td></tr>"
        for a,b in combs)

def cls_class(a,b):
    t="".join(sorted([cls(a),cls(b)]))
    return {"热温":"mix","冷热":"mix","温温":"warm","冷温":"mix"}.get(t,"bad")

valid_sorted = sorted(valid, key=lambda c:(c[0]+c[1], c[0]))
valid_html = combo_rows_html(valid_sorted, cls_class)

hist_html=""
for pid,b1,b2,s in hist_pass:
    hist_html+=f"<tr><td>{pid}</td><td>{b1:02d} + {b2:02d}</td><td>{s}</td><td class='ok'>✓ 满足</td></tr>\n"
for pid,b1,b2,s in hist_fail:
    reason=[]
    if not (9<=s<=16): reason.append("和值越界")
    if cls(b1)=="热" and cls(b2)=="热": reason.append("全热")
    if cls(b1)=="冷" and cls(b2)=="冷": reason.append("全冷")
    hist_html+=f"<tr><td>{pid}</td><td>{b1:02d} + {b2:02d}</td><td>{s}</td><td class='bad'>✗ {'/'.join(reason)}</td></tr>\n"

type_pills = " ".join(f"<span class='pill'>{k}: <b>{v}</b></span>" for k,v in type_cnt.most_common())

html=f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>大乐透后区冷热搭配说明</title>
<style>
 *{{box-sizing:border-box;font-family:-apple-system,"Microsoft YaHei",sans-serif}}
 body{{margin:0;background:#f5f7fa;color:#222;padding:24px}}
 .wrap{{max-width:880px;margin:0 auto}}
 h1{{font-size:22px;margin:0 0 4px}} .sub{{color:#666;font-size:13px;margin-bottom:18px}}
 .card{{background:#fff;border-radius:10px;padding:18px 20px;margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
 .kv{{display:flex;gap:20px;flex-wrap:wrap;font-size:14px;margin:8px 0}}
 .pill{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:13px;background:#eaf3fb;color:#2980b9;margin:2px}}
 .hot{{color:#e74c3c;font-weight:700}} .cold{{color:#2980b9;font-weight:700}} .warm{{color:#7f8c8d}}
 .ok{{color:#27ae60}} .bad{{color:#e74c3c}} .mix{{color:#8e44ad}} .warmc{{color:#7f8c8d}}
 table{{width:100%;border-collapse:collapse;font-size:13px}}
 th,td{{padding:5px 8px;border-bottom:1px solid #eee;text-align:center}}
 th{{background:#fafafa;color:#555}}
 .note{{font-size:12px;color:#888;line-height:1.7}}
 .rule{{background:#f8f9fb;border-left:4px solid #3498db;padding:8px 12px;margin:6px 0;border-radius:4px;font-size:13px}}
</style></head><body><div class="wrap">
<h1>📊 大乐透后区冷热搭配说明</h1>
<div class="sub">规则口径: ①后区冷热划分(频次均值±0.5std) ②两码和值锁定9-16 ③禁止全冷/全热组合 ｜ 数据: 第2026059–2026079期 (共21期)</div>

<div class="card">
  <h3 style="margin-top:0">① 后区冷热号划分</h3>
  <div class="kv">
    <span class="pill hot">热号 {len(hot)}个: {' '.join(f'{n:02d}' for n in hot)}</span>
    <span class="pill cold">冷号 {len(cold)}个: {' '.join(f'{n:02d}' for n in cold)}</span>
    <span class="pill">温号 {len(warm)}个: {' '.join(f'{n:02d}' for n in warm)}</span>
  </div>
  <div class="note">划分依据: 21期后区共42个出号位置, 均值{mean:.2f}次/号, 标准差{std:.2f}。热号=频次≥{hot_thr:.2f}(即≥5次); 冷号=频次≤{cold_thr:.2f}(即≤2次); 其余为温号。</div>
</div>

<div class="card">
  <h3 style="margin-top:0">② + ③ 组合规则与合法搭配池</h3>
  <div class="rule">规则A: 两码和值必须 ∈ [9, 16]</div>
  <div class="rule">规则B: 禁止<b>全冷</b>(两码皆冷) 与<b>全热</b>(两码皆热); 允许 热+温 / 冷+温 / 温+温 / 热+冷 混合</div>
  <div class="kv">
    <span>全部组合 C(12,2) = <b>66</b></span>
    <span class="ok">合法组合 = <b>{len(valid)}</b></span>
    <span class="bad">被禁组合 = <b>{len(forbidden)}</b></span>
  </div>
  <div>合法组合类型分布: {type_pills}</div>
  <p class="note">注: "热冷"实为热+冷混合(一热一冷), 满足"非全冷非全热", 故允许; 仅"冷冷""热热"两种被禁。</p>
</div>

<div class="card">
  <h3 style="margin-top:0">📋 合法后区两码组合清单 ({len(valid)}组)</h3>
  <table><thead><tr><th>组合</th><th>和值</th><th>类型</th></tr></thead><tbody>{valid_html}</tbody></table>
</div>

<div class="card">
  <h3 style="margin-top:0">历史21期回测 (规则过滤率)</h3>
  <div class="kv">
    <span class="ok">满足规则: <b>{len(hist_pass)}</b> 期 ({len(hist_pass)/len(backs)*100:.1f}%)</span>
    <span class="bad">被规则剔除: <b>{len(hist_fail)}</b> 期 ({len(hist_fail)/len(backs)*100:.1f}%)</span>
  </div>
  <table><thead><tr><th>期号</th><th>后区组合</th><th>和值</th><th>校验</th></tr></thead><tbody>{hist_html}</tbody></table>
  <p class="note">说明: 历史21期仅 {len(hist_pass)/len(backs)*100:.1f}% 满足本规则集, 即该规则为较强过滤条件, 会系统性排除约 {len(hist_fail)/len(backs)*100:.1f}% 的历史开奖组合。</p>
</div>

<div class="card note">
  ⚠️ <b>理性购彩提示:</b> 上述冷热划分、和值区间、搭配禁忌均为分析者自定义的<b>选号/过滤约束</b>, 大乐透官方并无此类规定。
  每期开奖为独立随机事件, 历史分布与搭配规律不预示未来。本说明仅作数据归档与规则演示, <b>不构成任何选号建议</b>。请量力而行。
  存档: dlt_back_hotcold.csv, dlt_back_valid_combo.csv
</div>
</div></body></html>'''

with open(f"{OUT_DIR}/大乐透后区冷热搭配说明.html","w",encoding="utf-8") as fp:
    fp.write(html)
print("\n报告已生成。存档:", sorted(os.listdir(OUT_DIR)))
