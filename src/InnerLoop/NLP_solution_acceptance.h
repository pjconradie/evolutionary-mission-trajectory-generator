#pragma once

#include "NLP_solver_status.h"

#include <algorithm>
#include <cmath>

namespace EMTG
{
    namespace Solvers
    {
        inline bool isEMTGFeasible(const double normalizedFeasibility,
                                   const double decisionVariableInfeasibility,
                                   const double tolerance)
        {
            return std::isfinite(normalizedFeasibility)
                && std::isfinite(decisionVariableInfeasibility)
                && std::isfinite(tolerance)
                && tolerance >= 0.0
                && normalizedFeasibility <= tolerance
                && decisionVariableInfeasibility <= tolerance;
        }

        inline bool isObjectiveSuperior(const double candidate,
                                        const double incumbent,
                                        const double absoluteTolerance = 1.0e-12,
                                        const double relativeTolerance = 1.0e-10)
        {
            if (!std::isfinite(candidate))
                return false;
            if (!std::isfinite(incumbent))
                return true;

            const double comparisonBand = absoluteTolerance
                + relativeTolerance * std::max(std::abs(candidate),
                                               std::abs(incumbent));
            return candidate < incumbent - comparisonBand;
        }

        inline bool isIncumbentCandidateSuperior(
            const double candidateObjective,
            const double candidateFeasibility,
            const double incumbentObjective,
            const double incumbentFeasibility,
            const double feasibilityTolerance)
        {
            const bool candidateFeasible = std::isfinite(candidateFeasibility)
                && candidateFeasibility <= feasibilityTolerance;
            const bool incumbentFeasible = std::isfinite(incumbentFeasibility)
                && incumbentFeasibility <= feasibilityTolerance;

            if (candidateFeasible != incumbentFeasible)
                return candidateFeasible;
            if (candidateFeasible)
                return isObjectiveSuperior(candidateObjective,
                                           incumbentObjective);
            return std::isfinite(candidateFeasibility)
                && (!std::isfinite(incumbentFeasibility)
                    || candidateFeasibility < incumbentFeasibility);
        }

        inline bool acceptNLPSolution(const bool chaperoneEnabled,
                                      const double normalizedFeasibility,
                                      const double decisionVariableInfeasibility,
                                      const double tolerance,
                                      const NLPStatus status)
        {
            const bool emtgFeasible = isEMTGFeasible(
                normalizedFeasibility,
                decisionVariableInfeasibility,
                tolerance);
            return emtgFeasible
                || (!chaperoneEnabled && solverAcceptedSolution(status));
        }
    }
}