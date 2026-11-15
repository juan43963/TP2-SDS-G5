import sys, numpy as np
from ana2 import load
p=sys.argv[1]; t0=float(sys.argv[2]); t1=float(sys.argv[3]); ids=[int(x) for x in sys.argv[4].split(',')]
fr=load(p)
door=(24.6,25.4)
for t,a in fr:
    if t<t0 or t>t1: continue
    d={int(r[0]):r for r in a}
    s='t=%6.2f '%t
    for i in ids:
        if i in d: s+=' | %d (%.3f,%.3f)'%(i,d[i][1],d[i][2])
        else: s+=' | %d out'%i
    # hueco libre entre los dos agentes que flanquean (112 y 23)
    print(s)
