#pragma once

#include "NLP_solver_status.h"

namespace EMTG
{
    namespace Solvers
    {
        constexpr bool acceptNLPSolution(const bool chaperoneEnabled,
                                         const double normalizedFeasibility,
                                         const double decisionVariableInfeasibility,
                                         const double tolerance,
                                         const NLPStatus status)
        {
            const bool emtgFeasible = normalizedFeasibility < tolerance
                && decisionVariableInfeasibility < tolerance;
            return emtgFeasible
                || (!chaperoneEnabled && solverAcceptedSolution(status));
        }
    }
}