import sys, glob, os, re, numpy as np
from ana2 import load, exits
lab=sys.argv[1]; keep=len(sys.argv)>2 and sys.argv[2]=='keep'
rows=[]
for f in sorted(glob.glob(f'res/{lab}_s*.csv'), key=lambda x:int(re.search(r'_s(\d+)\.csv',x).group(1))):
    s=int(re.search(r'_s(\d+)\.csv',f).group(1)); txt=open(f).read().strip()
    if not txt: rows.append((s,)+(None,)*9); continue
    c=txt.split(','); tr=f'traj/{lab}_s{s}.txt'
    comp=int(c[17]); tev=float(c[7]); ms=float(c[15]); oa=float(c[13]); ow=float(c[14])
    ng=tg=mg=0.0
    if comp and os.path.exists(tr):
        ex=exits(load(tr)); g=np.diff(ex); st=g[g>5]; ng=len(st); tg=st.sum(); mg=g.max()
    gs=''
    try: gs=re.search(r'sweeps_per_call=([\d.]+)',open(f'res/{lab}_s{s}.err').read()).group(1)
    except Exception: pass
    rows.append((s,tev if comp else float('nan'),comp,oa,ow,ms/1000,ng,tg,mg,gs))
print('semilla,t_evac,completa,solape_ag,solape_pared,computo_s,n_huecos>5s,t_en_huecos,max_hueco,sweeps_por_choque')
for r in rows: print(','.join('' if v is None else (f'{v:.4f}' if isinstance(v,float) else str(v)) for v in r))
ok=[r for r in rows if r[2]==1]
t=np.array([r[1] for r in ok]); n=len(t)
if n>1:
    print(f'# {lab}: completas {n}/{len(rows)}  t_evac media {t.mean():.1f} +- {t.std(ddof=1)/np.sqrt(n):.1f} (SEM)  sd {t.std(ddof=1):.1f}  mediana {np.median(t):.1f}  p25 {np.percentile(t,25):.1f} p75 {np.percentile(t,75):.1f} max {t.max():.1f}  solape_ag max {max(r[3] for r in ok):.3f} solape_pared max {max(r[4] for r in ok):.3f}  computo medio {np.mean([r[5] for r in ok]):.1f} s mediana {np.median([r[5] for r in ok]):.1f}')
    print(f'# con algun hueco>5s: {sum(1 for r in ok if r[6]>0)}/{n};  t_evac<70 s: {(t<70).sum()}/{n}')
if not keep:
    for f in glob.glob(f'traj/{lab}_s*.txt'): os.remove(f)
