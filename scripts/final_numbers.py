# -*- coding: utf-8 -*-
"""
任务5: 成品号码输出
生成5组标准"5前2后"号码, 每组附带 冷热配比 + 分区详情 + 备注, 统一汇总输出
所有约束源自任务1-4:
  任务1 前区冷热分类 / 任务2 三区全覆盖 / 任务3 后区合法组合(和值9-16,非全冷全热)
  任务4 23区间强胆 + 防扎堆单区(每区<=3)
单一数据源: dlt_front_coldhot.csv / dlt_back_valid_combo.csv / dlt_23_danma.csv
"""
import csv, os
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("DLT_DATA_DIR", os.path.join(_HERE, "..", "data"))
os.makedirs(OUT_DIR, exist_ok=True)

# ---- 读取前区冷热分类 ----
front_class = {}
front_freq = {}
with open(f"{OUT_DIR}/dlt_front_coldhot.csv", encoding="utf-8-sig") as fp:
    for r in csv.DictReader(fp):
        n = int(r["号码"])
        front_class[n] = r["分类"]
        front_freq[n] = int(r["出现次数"])

# ---- 读取后区合法组合 ----
valid_back = set()
back_type = {}
with open(f"{OUT_DIR}/dlt_back_valid_combo.csv", encoding="utf-8-sig") as fp:
    for r in csv.DictReader(fp):
        a, b = map(int, r["组合"].split("+"))
        valid_back.add(tuple(sorted((a, b))))
        back_type[tuple(sorted((a, b)))] = r["类型(冷热温)"]

# ---- 读取23区间强胆 ----
strong = set()
with open(f"{OUT_DIR}/dlt_23_danma.csv", encoding="utf-8-sig") as fp:
    for r in csv.DictReader(fp):
        if "强胆" in r["胆码等级"]:
            strong.add(int(r["号码"]))

def zone(n):
    if 1 <= n <= 10: return "一区"
    if 11 <= n <= 20: return "二区"
    return "三区"

# ---- 5组手工设计 (满足全部约束) ----
groups = [
    ([4, 13, 15, 26, 27], [2, 10], "二区双强胆13/15 + 三区强胆26, 含三区2连26-27"),
    ([6, 12, 19, 21, 23], [1, 11], "二区强胆12/19 + 三区强胆21, 无连号均衡分布"),
    ([7, 15, 18, 26, 27], [4, 9],  "二区强胆15 + 三区强胆26, 含三区2连26-27, 配比含冷"),
    ([1, 12, 21, 29, 30], [5, 8],  "二区强胆12 + 三区强胆21/29, 三区偏重(1-1-3)含温号"),
    ([4, 11, 20, 22, 32], [3, 12], "二区强胆20 + 三区强胆22, 含冷号11, 配比3热1温1冷"),
]

def connec(front):
    f = sorted(front)
    segs = []
    i, n = 0, len(f)
    while i < n:
        j = i
        while j + 1 < n and f[j+1] - f[j] == 1:
            j += 1
        if j > i:
            segs.append(f"{f[i]}-{f[j]}")
        i = j + 1
    return segs

# ---- 逐组验证 + 构建明细 ----
results = []
all_ok = True
for idx, (front, back, note) in enumerate(groups, 1):
    front_s = sorted(front)
    fz = Counter(zone(n) for n in front_s)
    z1, z2, z3 = fz["一区"], fz["二区"], fz["三区"]
    full = all(v >= 1 for v in (z1, z2, z3))
    heap = max(z1, z2, z3) >= 4
    hc = Counter(front_class[n] for n in front_s)
    ratio = f"{hc.get('热',0)}热{hc.get('温',0)}温{hc.get('冷',0)}冷"
    dan = [n for n in front_s if n in strong]
    conn = connec(front_s)
    bt = tuple(sorted(back))
    back_valid = bt in valid_back
    back_typ = back_type.get(bt, "不合法")
    ok = full and (not heap) and back_valid and len(dan) >= 1
    all_ok = all_ok and ok
    results.append(dict(
        g=idx, front=front_s, back=sorted(back),
        z1=z1, z2=z2, z3=z3, ratio=ratio,
        dan=dan, conn=conn, back_typ=back_typ,
        note=note, ok=ok,
        full=full, heap=heap, back_valid=back_valid
    ))
    flag = "✓合规" if ok else "✗不合规"
    print(f"组{idx}: 前区{front_s} 后区{sorted(back)} | 分区{flag} {z1}-{z2}-{z3} | 冷热{ratio} | "
          f"强胆{dan} | 连号{conn or '无'} | 后区{back_typ} | {flag}")

print(f"\n全部合规: {'是' if all_ok else '否'}")

# ---- 输出CSV ----
with open(f"{OUT_DIR}/dlt_final_groups.csv", "w", newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["组号","前区号码(5)","后区号码(2)","前区冷热配比","分区详情(一-二-三)",
                "含强胆","含连号","后区类型","合规状态","备注"])
    for r in results:
        w.writerow([f"组{r['g']}", " ".join(f"{n:02d}" for n in r['front']),
                    " ".join(f"{n:02d}" for n in r['back']),
                    r['ratio'], f"{r['z1']}-{r['z2']}-{r['z3']}",
                    " ".join(f"{n:02d}" for n in r['dan']),
                    " / ".join(r['conn']) if r['conn'] else "无",
                    r['back_typ'], "✓合规" if r['ok'] else "✗不合规", r['note']])

# ---- 汇总统计 ----
all_dan = sorted(set(d for r in results for d in r['dan']))
conn_groups = sum(1 for r in results if r['conn'])
ratio_dist = Counter(r['ratio'] for r in results)

# ---- HTML 成品报告 ----
cards = ""
for r in results:
    zcls = "bad" if (r['heap'] or not r['full']) else "ok"
    zone_badges = (f"<span class='zb one'>{r['z1']}</span>"
                   f"<span class='zb two'>{r['z2']}</span>"
                   f"<span class='zb three'>{r['z3']}</span>")
    front_balls = " ".join(
        f"<span class='ball f-{front_class[n]}'>{n:02d}</span>" for n in r['front'])
    back_balls = " ".join(f"<span class='ball bk'>{n:02d}</span>" for n in r['back'])
    dan_str = " ".join(f"<span class='dan'>{n:02d}</span>" for n in r['dan']) or "无"
    conn_str = " / ".join(r['conn']) if r['conn'] else "无"
    badge = "ok-badge" if r['ok'] else "bad-badge"
    cards += f"""
    <div class="grp">
      <div class="ghead"><span class="gnum">第 {r['g']} 组</span>
        <span class="badge {badge}">{'✓ 全部合规' if r['ok'] else '✗ 不合规'}</span></div>
      <div class="balls">{front_balls} <span class="plus">+</span> {back_balls}</div>
      <div class="meta">
        <div><b>冷热配比</b> {r['ratio']}</div>
        <div><b>分区详情</b> {zone_badges} <span class="zlab">(一-二-三)</span></div>
        <div><b>含强胆</b> {dan_str}</div>
        <div><b>含连号</b> {conn_str}</div>
        <div><b>后区类型</b> {r['back_typ']}</div>
      </div>
      <div class="note">📝 {r['note']}</div>
    </div>"""

html = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>大乐透成品号码</title>
<style>
 *{{box-sizing:border-box;font-family:-apple-system,"Microsoft YaHei",sans-serif}}
 body{{margin:0;background:#f5f7fa;color:#222;padding:24px}}
 .wrap{{max-width:960px;margin:0 auto}}
 h1{{font-size:22px;margin:0 0 4px}} .sub{{color:#666;font-size:13px;margin-bottom:18px}}
 .card{{background:#fff;border-radius:10px;padding:18px 20px;margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
 .sum{{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}}
 .sum .it{{background:#f0f7ff;border-radius:8px;padding:10px 14px}}
 .sum .big{{font-size:24px;font-weight:700;color:#2980b9}}
 .grp{{border:1px solid #eef0f3;border-radius:10px;padding:14px 16px;margin:12px 0}}
 .ghead{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}}
 .gnum{{font-size:16px;font-weight:700}}
 .badge{{padding:2px 10px;border-radius:12px;font-size:12px}}
 .ok-badge{{background:#e8f8ef;color:#27ae60}} .bad-badge{{background:#fdeaea;color:#e74c3c}}
 .balls{{font-size:0;margin:6px 0}}
 .ball{{display:inline-block;width:34px;height:34px;line-height:34px;text-align:center;border-radius:50%;
   font-size:15px;font-weight:700;color:#fff;margin:0 4px 4px 0}}
 .f-热{{background:#e74c3c}} .f-温{{background:#f39c12}} .f-冷{{background:#3498db}} .bk{{background:#8e44ad}}
 .plus{{display:inline-block;width:24px;text-align:center;color:#999;font-weight:700;font-size:18px;vertical-align:middle}}
 .meta{{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;margin:6px 0}}
 .meta b{{color:#666;font-weight:600;margin-right:4px}}
 .zb{{display:inline-block;padding:1px 9px;border-radius:10px;font-size:12px;color:#fff;margin:0 1px}}
 .one{{background:#3498db}} .two{{background:#2980b9}} .three{{background:#1f618d}}
 .zlab{{color:#999;font-size:11px}}
 .dan{{display:inline-block;padding:1px 7px;border-radius:8px;background:#fde8e8;color:#e74c3c;font-size:12px;margin:0 2px}}
 .note{{font-size:12px;color:#777;background:#fafafa;padding:6px 10px;border-radius:6px;margin-top:6px}}
 table{{width:100%;border-collapse:collapse;font-size:13px}}
 th,td{{padding:6px 8px;border-bottom:1px solid #eee;text-align:center}}
 th{{background:#fafafa;color:#555}}
 .warn{{background:#fff8e1;border-left:4px solid #f39c12;padding:10px 14px;border-radius:4px;font-size:12px;line-height:1.7;color:#7a5b00}}
</style></head><body><div class="wrap">
<h1>🎯 大乐透成品号码输出 (5组)</h1>
<div class="sub">口径: 前区三区01-10/11-20/21-35 ｜ 后区和值9-16且非全冷全热 ｜ 23区间强胆池 ｜ 数据窗口: 第2026059–2026079期(21期)</div>

<div class="card">
  <h3 style="margin-top:0">📊 汇总概览</h3>
  <div class="sum">
    <div class="it"><div class="big">5</div>输出组数</div>
    <div class="it"><div class="big">{len(all_dan)}</div>覆盖强胆号码</div>
    <div class="it"><div class="big">{conn_groups}/5</div>含连号组数</div>
    <div class="it"><div class="big">{'全合规' if all_ok else '有异常'}</div>约束校验</div>
  </div>
  <div class="note" style="font-size:12px;color:#888;margin-top:10px">
    覆盖强胆: {' '.join(f'{n:02d}' for n in all_dan)} ｜ 冷热配比分布: {dict(ratio_dist)}
  </div>
</div>

<div class="card">
  <h3 style="margin-top:0">🎱 5组成品号码 (每组: 5前区 + 2后区)</h3>
  {cards}
</div>

<div class="card">
  <h3 style="margin-top:0">📋 汇总明细表</h3>
  <table><thead><tr><th>组号</th><th>前区(5)</th><th>后区(2)</th><th>冷热配比</th><th>分区(一-二-三)</th>
    <th>强胆</th><th>连号</th><th>后区类型</th><th>合规</th></tr></thead><tbody>
  {''.join(f"<tr><td>组{r['g']}</td><td>{' '.join(f'{n:02d}' for n in r['front'])}</td><td>{' '.join(f'{n:02d}' for n in r['back'])}</td><td>{r['ratio']}</td><td>{r['z1']}-{r['z2']}-{r['z3']}</td><td>{' '.join(f'{n:02d}' for n in r['dan']) or '无'}</td><td>{' / '.join(r['conn']) or '无'}</td><td>{r['back_typ']}</td><td>{'✓' if r['ok'] else '✗'}</td></tr>" for r in results)}
  </tbody></table>
</div>

<div class="card warn">
  ⚠️ <b>理性购彩提示:</b> 本成品号码由历史21期数据的<b>自定义约束</b>(冷热配比、三区均衡、强胆参考、后区合法组合)生成,
  大乐透每期开奖为<b>独立随机事件</b>, 历史规律不预示未来, 任何组合中奖概率完全均等。
  以上仅为数据归档与参考演示, <b>绝不构成任何购彩建议</b>。请理性投注, 量力而行。
  存档: dlt_final_groups.csv
</div>
</div></body></html>'''

with open(f"{OUT_DIR}/大乐透成品号码.html", "w", encoding="utf-8") as fp:
    fp.write(html)
print("\n报告已生成。存档:", sorted(os.listdir(OUT_DIR)))
