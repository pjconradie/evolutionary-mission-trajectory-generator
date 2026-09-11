#pragma once

#include "NLP_solver_status.h"

namespace EMTG
{
    namespace Solvers
    {
        enum class IPOPTTermination
        {
            SolveSucceeded,
            SolvedToAcceptableLevel,
            FeasiblePointFound,
            InfeasibleProblemDetected,
            MaximumIterationsExceeded,
            MaximumCpuTimeExceeded,
            DivergingIterates,
            UserRequestedStop,
            InvalidNumberDetected,
            SearchDirectionTooSmall,
            RestorationFailed,
            ErrorInStepComputation,
            InvalidProblemDefinition,
            InvalidOption,
            NotEnoughDegreesOfFreedom,
            UnrecoverableException,
            NonIpoptExceptionThrown,
            InsufficientMemory,
            InternalError
        };

        constexpr NLPStatus translateIPOPTTermination(
            const IPOPTTermination termination)
        {
            switch (termination)
            {
                case IPOPTTermination::SolveSucceeded:
                case IPOPTTermination::SolvedToAcceptableLevel:
                case IPOPTTermination::FeasiblePointFound:
                    return NLPStatus::AcceptedSolution;
                case IPOPTTermination::InfeasibleProblemDetected:
                    return NLPStatus::Infeasible;
                case IPOPTTermination::MaximumIterationsExceeded:
                    return NLPStatus::IterationLimit;
                case IPOPTTermination::MaximumCpuTimeExceeded:
                    return NLPStatus::TimeLimit;
                case IPOPTTermination::DivergingIterates:
                    return NLPStatus::Unbounded;
                case IPOPTTermination::UserRequestedStop:
                    return NLPStatus::UserTerminated;
                case IPOPTTermination::InvalidNumberDetected:
                    return NLPStatus::EvaluationError;
                case IPOPTTermination::SearchDirectionTooSmall:
                case IPOPTTermination::RestorationFailed:
                case IPOPTTermination::ErrorInStepComputation:
                    return NLPStatus::NumericalError;
                case IPOPTTermination::InvalidProblemDefinition:
                case IPOPTTermination::InvalidOption:
                case IPOPTTermination::NotEnoughDegreesOfFreedom:
                case IPOPTTermination::UnrecoverableException:
                case IPOPTTermination::NonIpoptExceptionThrown:
                case IPOPTTermination::InsufficientMemory:
                case IPOPTTermination::InternalError:
                    return NLPStatus::Error;
            }

            return NLPStatus::Error;
        }
    }
}