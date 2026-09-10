#pragma once

#include "NLP_solver_status.h"

namespace EMTG
{
    namespace Solvers
    {
        constexpr NLPStatus translateSNOPTInform(const int inform)
        {
            return inform < 0 ? NLPStatus::Error
                : inform < 10 ? NLPStatus::AcceptedSolution
                : inform < 20 ? NLPStatus::Infeasible
                : inform < 30 ? NLPStatus::Unbounded
                : inform < 40 ? NLPStatus::IterationLimit
                : inform < 50 ? NLPStatus::NumericalError
                : inform < 70 ? NLPStatus::EvaluationError
                : inform < 80 ? NLPStatus::UserTerminated
                : NLPStatus::Error;
        }
    }
}