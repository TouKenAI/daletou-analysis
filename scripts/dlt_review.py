# -*- coding: utf-8 -*-
"""大乐透「最大覆盖优化」复查脚本
1. 更大样本(均匀开奖)重测三组「至少中某奖」概率 + 95%CI
2. 组间比例 z 检验
3. 单注理论中奖率验证(应≈6.68%)
4. 重验5组号码是否满足5步法硬约束
"""
import csv, itertools, random, math, os
from collections import Counter

SEED = 20260719
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("DLT_DATA_DIR", os.path.join(_HERE, "..", "data"))
os.makedirs(DATA, exist_ok=True)

raw = []
with open(f"{DATA}/dlt_raw_21.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        fnums = [int(row[f'前区{i}']) for i in range(1, 6)]
        bnums = [int(row[f'后区{i}']) for i in range(1, 3)]
        raw.append((fnums, bnums))

back_pool, btype_map = [], {}
with open(f"{DATA}/dlt_back_valid_combo.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        a, b = row['组合'].split('+')
        back_pool.append((int(a), int(b)))
        btype_map[row['组合']] = row['类型(冷热温)']

strong = [13, 26, 15, 19, 21, 12, 20, 22, 29]
front_cnt = Counter(); back_cnt = Counter()
for fnums, bnums in raw:
    front_cnt.update(fnums); back_cnt.update(bnums)
fc = [front_cnt.get(i, 0) for i in range(1, 36)]
mean_f = sum(fc) / 35.0
std_f = (sum((x - mean_f) ** 2 for x in fc) / 35.0) ** 0.5
hot_f = set(i for i in range(1, 36) if front_cnt.get(i, 0) >= mean_f + 0.5 * std_f)
cold_f = set(i for i in range(1, 36) if front_cnt.get(i, 0) <= mean_f - 0.5 * std_f)

def zone(n):
    return 0 if 1 <= n <= 10 else (1 if 11 <= n <= 20 else 2)

# ---- 复现优化组(与 maxcover.py 一致) ----
front_candidates = []
for combo in itertools.combinations(range(1, 36), 5):
    z = [0, 0, 0]
    for n in combo: z[zone(n)] += 1
    if min(z) < 1 or max(z) > 3: continue
    if not any(n in strong for n in combo): continue
    h = sum(1 for n in combo if n in hot_f); c = sum(1 for n in combo if n in cold_f)
    if h == 5 or c == 5: continue
    front_candidates.append(combo)

LAMBDA = 0.03
selected_front, covered_front = [], set()
while len(selected_front) < 5:
    best, best_score = None, -1
    for combo in front_candidates:
        new = len(set(combo) - covered_front)
        heat = sum(front_cnt.get(n, 0) for n in combo)
        s = new + LAMBDA * heat
        if s > best_score: best_score, best = s, combo
    selected_front.append(best); covered_front.update(best)

selected_back, covered_back = [], set()
while len(selected_back) < 5:
    best, best_score = None, -1
    for (a, b) in back_pool:
        new = len({a, b} - covered_back)
        if new == 0: continue
        if new > best_score: best_score, best = new, (a, b)
    selected_back.append(best); covered_back.update(best)

groups = list(zip(selected_front, selected_back))

std_groups = [([4,13,15,26,27],[2,10]),([6,12,19,21,23],[1,11]),
              ([7,15,18,26,27],[4,9]),([1,12,21,29,30],[5,8]),([4,11,20,22,32],[3,12])]

random.seed(SEED + 1)
rand_groups = [(random.sample(range(1, 36), 5), random.sample(range(1, 13), 2)) for _ in range(5)]

WIN_SET = {(5,2),(5,1),(5,0),(4,2),(4,1),(3,2),(4,0),(3,1),(2,2),(3,0),(1,2),(2,1),(0,2)}
def is_win(fh, bh): return (fh, bh) in WIN_SET

def simulate(N, grps, seed):
    random.seed(seed)
    w = 0
    for _ in range(N):
        df = set(random.sample(range(1, 36), 5)); db = set(random.sample(range(1, 13), 2))
        if any(is_win(len(set(fc) & df), len(set(bc) & db)) for fc, bc in grps): w += 1
    return w / N

def single_rate(N, seed):
    random.seed(seed)
    w = 0
    for _ in range(N):
        df = set(random.sample(range(1, 36), 5)); db = set(random.sample(range(1, 13), 2))
        if is_win(len(set([1,2,3,4,5]) & df), len(set([1,2]) & db)): w += 1
    return w / N

def ci(p, N):
    se = math.sqrt(p * (1 - p) / N)
    return (p - 1.96 * se, p + 1.96 * se)

def ztest(p1, n1, p2, n2):
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return (p1 - p2) / se

MC_N = 400000
mine = simulate(MC_N, groups, 100)
std = simulate(MC_N, std_groups, 200)
rand = simulate(MC_N, rand_groups, 300)
sr = single_rate(200000, 400)

print("=" * 66)
print("大乐透最大覆盖优化 · 复查 (均匀开奖蒙特卡洛)")
print("=" * 66)
theory_single = 1431197 / 21425712
print(f"单注理论中奖率: {theory_single*100:.4f}%  | 模拟(固定单注1-5+1-2): {sr*100:.4f}%")
print(f"5注 union-bound 上限: {5*theory_single*100:.2f}%  | 5注独立近似: {(1-(1-theory_single)**5)*100:.2f}%")
print(f"前区去重覆盖: {len(covered_front)}/35  后区去重覆盖: {len(covered_back)}/12")
print("-" * 66)
for name, rate in [("优化组", mine), ("标准流程组", std), ("随机组", rand)]:
    lo, hi = ci(rate, MC_N)
    print(f"{name}: {rate*100:.3f}%  (95%CI {lo*100:.3f}%-{hi*100:.3f}%)  N={MC_N:,}")
print("-" * 66)
print(f"优化 vs 随机: +{(mine-rand)*100:.3f}pp  z={ztest(mine,MC_N,rand,MC_N):.2f}  {'显著' if abs(ztest(mine,MC_N,rand,MC_N))>1.96 else '不显著'}")
print(f"标准 vs 随机: +{(std-rand)*100:.3f}pp  z={ztest(std,MC_N,rand,MC_N):.2f}  {'显著' if abs(ztest(std,MC_N,rand,MC_N))>1.96 else '不显著'}")
print(f"优化 vs 标准: +{(mine-std)*100:.3f}pp  z={ztest(mine,MC_N,std,MC_N):.2f}  {'显著' if abs(ztest(mine,MC_N,std,MC_N))>1.96 else '不显著'}")
print("=" * 66)

print("\n[5步法硬约束重验 - 优化组5注]")
for i, (fc, bc) in enumerate(groups, 1):
    z = [0, 0, 0]
    for n in fc: z[zone(n)] += 1
    ok_zone = (min(z) >= 1 and max(z) <= 3)
    ok_strong = any(n in strong for n in fc)
    combo_str = f"{bc[0]:02d}+{bc[1]:02d}"
    ok_back = combo_str in btype_map
    h = sum(1 for n in fc if n in hot_f); c = sum(1 for n in fc if n in cold_f)
    ok_mix = not (h == 5 or c == 5)
    print(f"组{i}: {fc}+{bc} 三区{z}({'OK' if ok_zone else 'FAIL'}) 强胆{'OK' if ok_strong else 'FAIL'} 后区{'OK' if ok_back else 'FAIL'}({btype_map.get(combo_str,'?')}) 冷热混合{'OK' if ok_mix else 'FAIL'}")
