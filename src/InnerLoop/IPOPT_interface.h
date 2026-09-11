#pragma once

#include "NLP_interface.h"
#include "NLP_sparse_derivative_layout.h"

#include <memory>

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

        private:
            class TNLPBridge;

            bool evaluatePoint(const double* scaledX,
                               bool needDerivatives);

            std::unique_ptr<SparseDerivativeLayout> derivativeLayout;
        };
    }
}