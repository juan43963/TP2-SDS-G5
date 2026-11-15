import sys, numpy as np
from ana2 import load
p=sys.argv[1]; ts=[float(x) for x in sys.argv[2].split(',')]
fr=load(p); T=np.array([t for t,a in fr])
for t in ts:
    a=fr[int(np.argmin(abs(T-t)))][1]
    near=a[(abs(a[:,1]-25)<1.3)&(a[:,2]<0.6)]
    near=near[np.argsort(near[:,1])]
    print('t=%.1f:'%t, ' '.join('[id%d x=%.3f y=%.3f d=%.3f]'%(r[0],r[1],r[2],2*r[5]) for r in near))
    # hueco libre: agentes cuyo borde invade la boca; el mas bajo, y sus vecinos laterales
    # clearance min entre pares de agentes bajos que flanquean x=25
    L=near[near[:,1]<25]; R=near[near[:,1]>=25]
    if len(L) and len(R):
        best=min(((np.hypot(l[1]-r_[1],l[2]-r_[2])-l[5]-r_[5],l[0],r_[0]) for l in L for r_ in R))
        print('   hueco libre minimo izq-der = %.3f m (ids %d,%d); puerta 0.8'%best)
