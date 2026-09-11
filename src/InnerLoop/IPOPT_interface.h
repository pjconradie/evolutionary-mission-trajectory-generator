#pragma once

#include "NLP_interface.h"

namespace EMTG
{
    namespace Solvers
    {
        class IPOPT_interface final : public NLP_interface
        {
        public:
            IPOPT_interface(problem* myProblem,
                            const NLPoptions& myOptions);

            void run_NLP(const bool& X0_is_scaled = true) override;
        };
    }
}