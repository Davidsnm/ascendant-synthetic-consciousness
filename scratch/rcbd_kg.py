import sqlite3, json, math, numpy as np
DB = r"c:\Users\Usuario\Documents\nuevos proyectos\Proyecto ascendant\experimeto generacional corregido\ascendant_generacional_integro.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = conn.cursor()

def chi2_sf1(x):  # df=1 -> p from F approx not needed
    return math.erfc(math.sqrt(x / 2))

def fdist_sf(F, d1, d2):
    # regularized incomplete beta via continued fraction
    x = d2 / (d2 + d1 * F)
    a, b = d2 / 2.0, d1 / 2.0
    def betacf(a, b, x):
        qab, qap, qam = a + b, a + 1, a - 1
        c, d = 1.0, 1 - qab * x / qap
        d = 1 / (d if abs(d) > 1e-30 else 1e-30)
        h = d
        for m in range(1, 400):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1 + aa * d; d = 1e-30 if abs(d) < 1e-30 else d
            c = 1 + aa / c; c = 1e-30 if abs(c) < 1e-30 else c
            d = 1 / d; h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1 + aa * d; d = 1e-30 if abs(d) < 1e-30 else d
            c = 1 + aa / c; c = 1e-30 if abs(c) < 1e-30 else c
            d = 1 / d; de = d * c; h *= de
            if abs(de - 1) < 1e-14: break
        return h
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * betacf(a, b, x) / a
    return 1 - bt * betacf(b, a, 1 - x) / b

def rcbd(tags):
    q = ",".join("'%s'" % t for t in tags)
    cur.execute(f"SELECT seed, cultural_enabled, pantry_enabled, alive_cycles, experiment_tag FROM simulation_runs WHERE experiment_tag IN ({q})")
    rows = cur.fetchall()
    seeds = sorted(set((r[0], r[4]) for r in rows))
    sid = {s: i for i, s in enumerate(seeds)}
    y = np.array([r[3] for r in rows], float)
    T = np.array([r[1] for r in rows], float)
    P = np.array([r[2] for r in rows], float)
    blk = np.array([sid[(r[0], r[4])] for r in rows])
    n = len(y); nb = len(seeds)
    gm = y.mean()
    ss_tot = ((y - gm) ** 2).sum()
    bm = np.bincount(blk, y) / np.bincount(blk)
    ss_b = (np.bincount(blk) * (bm - gm) ** 2).sum()
    def eff(m):
        return (m * (y[m == m] if False else 0))
    cells = {}
    for t in (0, 1):
        for p in (0, 1):
            m = (T == t) & (P == p)
            cells[(t, p)] = y[m].mean(); 
    nc = n / 4
    ss_T = n * ((y[T == 1].mean() - gm) ** 2 + (y[T == 0].mean() - gm) ** 2) / 2
    ss_P = n * ((y[P == 1].mean() - gm) ** 2 + (y[P == 0].mean() - gm) ** 2) / 2
    ss_cells = nc * sum((v - gm) ** 2 for v in cells.values())
    ss_TP = ss_cells - ss_T - ss_P
    df_e = n - 1 - (nb - 1) - 3
    ss_e = ss_tot - ss_b - ss_T - ss_P - ss_TP
    ms_e = ss_e / df_e
    out = {"n": n, "blocks": nb, "cells": {f"T{t}P{p}": [round(v, 2), round(float(y[(T == t) & (P == p)].std(ddof=1)), 2)] for (t, p), v in cells.items()},
           "SS": {"T": ss_T, "P": ss_P, "TP": ss_TP, "block": ss_b, "err": ss_e, "tot": ss_tot}, "df_err": df_e, "MS_err": ms_e,
           "MS_block": ss_b / (nb - 1)}
    for k, ss in (("T", ss_T), ("P", ss_P), ("TP", ss_TP)):
        F = ss / ms_e
        out[k] = {"F": round(F, 3), "p": fdist_sf(F, 1, df_e), "eta2p": round(ss / (ss + ss_e), 4)}
    Fb = (ss_b / (nb - 1)) / ms_e
    out["block_F"] = round(Fb, 3); out["block_p"] = fdist_sf(Fb, nb - 1, df_e)
    # simple effects & interaction contrast (paired by seed)
    d = {}
    for r in rows:
        d.setdefault((r[0], r[4]), {})[(r[1], r[2])] = r[3]
    I = np.array([(v[(1, 1)] - v[(1, 0)]) - (v[(0, 1)] - v[(0, 0)]) for v in d.values()], float)
    Cm = np.array([(v[(1, 0)] - v[(0, 0)]) for v in d.values()], float)
    Pm = np.array([(v[(0, 1)] - v[(0, 0)]) for v in d.values()], float)
    for nm, a in (("interaction", I), ("culture_noP", Cm), ("pantry_noT", Pm)):
        se = a.std(ddof=1) / math.sqrt(len(a))
        out[nm] = {"mean": round(a.mean(), 2), "ci95": [round(a.mean() - 1.96 * se, 1), round(a.mean() + 1.96 * se, 1)], "t": round(a.mean() / se, 3)}
    return out

res = {"K3_M100": rcbd(["K3_M100"]),
       "ALL_6": rcbd(["K3_M100", "K3_M140", "K3_M200", "K5_M100", "K5_M140", "K5_M200"])}

# Kg from engram origins
cur.execute("""SELECT sr.cultural_enabled, fm.gen_number, fm.inherited_count, fm.innate_count, fm.own_count, fm.engrams_count
FROM final_memories fm JOIN simulation_runs sr ON sr.run_id=fm.run_id WHERE sr.experiment_tag LIKE 'K%' AND fm.gen_number>0""")
rows = cur.fetchall()
kg = {}
for c, g, inh, inn, own, tot in rows:
    kg.setdefault((c, g), []).append((inh, inn, own, tot))
res["kg_raw"] = {f"cult{c}_gen{g}": [round(float(np.mean([x[i] for x in v])), 3) for i in range(4)] for (c, g), v in sorted(kg.items())}
cur.execute("SELECT engrams_json FROM final_memories fm JOIN simulation_runs sr ON sr.run_id=fm.run_id WHERE sr.experiment_tag='K3_M100' AND fm.gen_number=2 AND sr.cultural_enabled=1 LIMIT 1")
e = json.loads(cur.fetchone()[0])
res["origins_sample"] = sorted(set(str(x.get("origin")) for x in e))
conn.close()
json.dump(res, open(r"C:\Users\Usuario\.gemini\antigravity\brain\3c1c4d69-a3d2-438b-9c0e-0cb419298e5b\scratch\rcbd_kg.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
