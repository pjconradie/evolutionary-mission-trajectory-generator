#pragma once

#include "NLP_interface.h"

#include <memory>

namespace EMTG
{
    namespace Solvers
    {
        std::unique_ptr<NLP_interface> createNLPSolver(problem* myProblem,
                                                       const NLPoptions& options,
                                                       int requestedSolver);
    }
}