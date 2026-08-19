#include "generator.h"

// RED (TDD): placeholder implementation, intentionally incorrect.
// Every particle is default-constructed (id=0, x=y=theta=0) instead of being
// drawn from a seeded RNG. testGenerator()/testGridMatchesBruteForce() in
// selftest.cpp must fail against this stub; the real implementation lands in
// the GREEN commit.
std::vector<VicsekParticle> generateVicsekParticles(int N, double L, unsigned long long seed) {
    (void)L;
    (void)seed;
    return std::vector<VicsekParticle>(static_cast<size_t>(N));
}
