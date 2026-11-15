import sys, numpy as np
from ana2 import load
p=sys.argv[1]; t0=float(sys.argv[2]); t1=float(sys.argv[3])
fr=load(p); T=np.array([t for t,a in fr])
def at(t):
    k=int(np.argmin(abs(T-t))); return fr[k][1]
# desplazamiento de cada agente respecto de t0 a distintos t
a0=at(t0); ids=a0[:,0].astype(int)
print('agentes en sala t=%.0f: %d'%(t0,len(ids)))
for t in np.arange(t0,t1+0.01,(t1-t0)/10):
    a=at(t); d={int(r[0]):r for r in a}
    disp=np.array([np.hypot(d[i][1]-a0[k][1],d[i][2]-a0[k][2]) for k,i in enumerate(ids) if i in d])
    sp=np.array([np.hypot(r[3],r[4]) for r in a])
    print('t=%6.1f en sala=%3d  desplaz. mediano=%.3f max=%.3f m   |v| mediana=%.3f max=%.2f   n(|v|>0.5)=%d'%(t,len(a),np.median(disp),disp.max(),np.median(sp),sp.max(),(sp>0.5).sum()))
# los agentes de la fila baja
a=at(t0); low=a[(a[:,2]<0.7)&(abs(a[:,1]-25)<1.5)]
print('fila baja (y<0.7,|x-25|<1.5) en t0:'); 
for r in low[np.argsort(low[:,1])]: print('  id %3d x=%.3f y=%.3f r=%.3f v=(%.2f,%.2f)'%(r[0],r[1],r[2],r[5],r[3],r[4]))
