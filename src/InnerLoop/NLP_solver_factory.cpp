#include "NLP_solver_factory.h"

#include "NLP_solver_selection.h"

#ifdef EMTG_NLP_SOLVER_SNOPT
#include "SNOPT_interface.h"
#endif

#include <iostream>
#include <stdexcept>

namespace EMTG
{
    namespace Solvers
    {
        namespace
        {
            NLPBackend compiledNLPBackend()
            {
#ifdef EMTG_NLP_SOLVER_SNOPT
                return NLPBackend::SNOPT;
#elif defined(EMTG_NLP_SOLVER_IPOPT)
                return NLPBackend::IPOPT;
#else
                return NLPBackend::None;
#endif
            }
        }

        std::unique_ptr<NLP_interface> createNLPSolver(problem* myProblem,
                                                       const NLPoptions& options,
                                                       const int requestedSolver)
        {
            const NLPBackendResolution resolution = resolveNLPBackend(
                requestedSolver,
                compiledNLPBackend());

            if (resolution.usedLegacyFallback)
            {
                std::cout << "NLP_solver_type 0 requested legacy SNOPT; "
                          << "using the build-default IPOPT backend instead."
                          << std::endl;
            }

            switch (resolution.backend)
            {
                case NLPBackend::SNOPT:
#ifdef EMTG_NLP_SOLVER_SNOPT
                    return std::unique_ptr<NLP_interface>(
                        new SNOPT_interface(myProblem, options));
#else
                    break;
#endif
                case NLPBackend::IPOPT:
                    throw std::runtime_error("IPOPT adapter is not implemented");
                case NLPBackend::None:
                    break;
            }

            throw std::runtime_error("Requested NLP backend is not available");
        }
    }
}