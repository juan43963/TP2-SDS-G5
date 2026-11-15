import sys, numpy as np
def load(p):
    fr=[]; cur=None
    for ln in open(p):
        if ln.startswith('FRAME'):
            t=float(ln.split()[1]); cur=[]; fr.append((t,cur)); continue
        if cur is None: continue
        a=ln.split()
        if len(a)==7: cur.append([float(x) for x in a[:6]])
    return [(t,np.array(r).reshape(-1,6)) for t,r in fr]
def exits(fr):
    n=[len(a) if len(a) else 0 for t,a in fr]
    ex=[]
    for k in range(1,len(fr)):
        ex += [fr[k][0]]*(n[k-1]-n[k]) if n[k-1]>n[k] else []
    return np.array(ex)
if __name__=='__main__':
    for p in sys.argv[1:]:
        fr=load(p); ex=exits(fr)
        print('==',p,'frames',len(fr),'exits',len(ex),'rows@0',len(fr[0][1]),'rows@last',len(fr[-1][1]))
        # rows: do frames list only agents in sala? check
        g=np.diff(ex); 
        stall=g[g>5]
        print(' t_last=%.1f; huecos>5s: n=%d suma=%.1f s (%.0f%% del t_evac); max hueco=%.1f'%(ex[-1],len(stall),stall.sum(),100*stall.sum()/ex[-1],g.max()))
        big=np.where(g>5)[0]
        print(' huecos (inicio,duracion):',[(round(ex[i],1),round(g[i],1)) for i in big])
