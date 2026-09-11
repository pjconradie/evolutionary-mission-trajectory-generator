#include "IPOPT_interface.h"

#include "IpIpoptApplication.hpp"

#include <stdexcept>

namespace EMTG
{
    namespace Solvers
    {
        IPOPT_interface::IPOPT_interface(problem* myProblem,
                                         const NLPoptions& myOptions) :
            NLP_interface(myProblem, myOptions)
        {
        }

        void IPOPT_interface::run_NLP(const bool&)
        {
            this->status = NLPStatus::NotRun;

            Ipopt::SmartPtr<Ipopt::IpoptApplication> application =
                IpoptApplicationFactory();
            if (application->Initialize() != Ipopt::Solve_Succeeded)
            {
                this->status = NLPStatus::Error;
                throw std::runtime_error("Failed to initialize IPOPT");
            }

            throw std::runtime_error(
                "IPOPT callback adapter is not implemented");
        }
    }
}