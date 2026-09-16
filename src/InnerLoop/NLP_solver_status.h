#pragma once

namespace EMTG
{
    namespace Solvers
    {
        enum class NLPStatus
        {
            NotRun,
            AcceptedSolution,
            IterationLimit,
            TimeLimit,
            Infeasible,
            Unbounded,
            UserTerminated,
            NumericalError,
            EvaluationError,
            Error
        };

        constexpr bool solverAcceptedSolution(const NLPStatus status)
        {
            return status == NLPStatus::AcceptedSolution;
        }
    }
}