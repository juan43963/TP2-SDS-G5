p = 'src/engine/edmd.cpp'
s = open(p, encoding='utf8').read()
old = "    const double depth = separatePair(xa, xb, n, contact, mass, mass);\n"
new = old + '''    if (depth > 0.02) {
        std::fprintf(stderr,
            "DEEP t=%.4f a=%zu b=%zu depth=%.4f u=%.3f dSinceLast=%.5f pulseA=%.4f pulseB=%.4f cntA=%llu cntB=%llu\\n",
            now_, a, b, depth, u, now_ - previous, ra.pulseEnd - now_, rb.pulseEnd - now_,
            (unsigned long long)ra.collisionCount, (unsigned long long)rb.collisionCount);
    }
'''
assert old in s
s = s.replace(old, new, 1)
if '#include <cstdio>' not in s:
    s = s.replace('#include <cmath>', '#include <cmath>\n#include <cstdio>', 1)
open(p, 'w', encoding='utf8').write(s)
print('ok')
