import csv, glob, collections, statistics as st, re, sys
def load(d, alpha):
    out=collections.defaultdict(list)
    for f in glob.glob(f'{d}/runs/*-hybrid-*.csv'):
        if f.endswith('.pop.csv'): continue
        rows=list(csv.DictReader(open(f)))
        if not rows or 'simulation_ms' not in rows[0]: continue
        r=rows[0]
        if abs(float(r['hybrid_alpha'])-alpha)>1e-9: continue
        key=(r['study'],r['mode'],int(r['N']),float(r['L']),float(r['hybrid_T']))
        out[key].append(r)
    return out
A2=load('data/studies',2.0); A1=load('data/studies_alpha1',1.0)
def ms(v):
    if not v: return "   -   "
    m=st.mean(v); e=st.stdev(v)/len(v)**.5 if len(v)>1 else 0
    return f"{m:7.1f}±{e:4.1f}"
print("estudio                         n(a2/a1) completas(a2/a1)  t_evac a2        t_evac a1        cpu_s a2         cpu_s a1         prom a2 / a1")
for k in sorted(set(A1)|set(A2)):
    r2,r1=A2.get(k,[]),A1.get(k,[])
    c2=[r for r in r2 if r['completed']=='1']; c1=[r for r in r1 if r['completed']=='1']
    f=lambda rs,c:[float(r[c]) for r in rs]
    pm=lambda rs: st.mean(f(rs,'promotions')) if rs else float('nan')
    print(f"{str(k):38s} {len(r2):2d}/{len(r1):2d}  {len(c2):2d}/{len(c1):2d}   {ms(f(c2,'t_evac'))} {ms(f(c1,'t_evac'))} {ms([x/1000 for x in f(c2,'simulation_ms')])} {ms([x/1000 for x in f(c1,'simulation_ms')])}  {pm(r2):7.0f} / {pm(r1):7.0f}")
