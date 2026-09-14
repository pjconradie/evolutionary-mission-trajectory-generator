#pragma once

namespace EMTG
{
    namespace Solvers
    {
        enum class NLPInitializationPolicy
        {
            Default,
            NearFeasiblePrimalSeed
        };

        inline NLPInitializationPolicy consumeMBHInitializationPolicy(
            bool& seededStep)
        {
            const NLPInitializationPolicy policy = seededStep
                ? NLPInitializationPolicy::NearFeasiblePrimalSeed
                : NLPInitializationPolicy::Default;
            seededStep = false;
            return policy;
        }
    }
}