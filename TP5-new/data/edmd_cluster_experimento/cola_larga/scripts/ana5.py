import numpy as np
from ana2 import load
fr=load('traj/c_s3.txt')
print('t   x27 y27 | x112 y112 | x23 y23 | clearance 112-23 (centro a centro - r112 - r23) vs diam27')
for t,a in fr:
    if t<36 or t>100: continue
    if abs(t*10-round(t*10))>1e-6 or round(t*10)%50: continue
    d={int(r[0]):r for r in a}
    if 27 not in d: print(t,'27 out'); continue
    r27,r112,r23=d[27],d[112],d[23]
    cl=np.hypot(r112[1]-r23[1],r112[2]-r23[2])-r112[5]-r23[5]
    print('%5.1f  27(%.3f,%.3f)  112(%.3f,%.3f) 23(%.3f,%.3f)  libre=%.3f  diam27=%.3f'%(t,r27[1],r27[2],r112[1],r112[2],r23[1],r23[2],cl,2*r27[5]))
