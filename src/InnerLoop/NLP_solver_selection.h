#pragma once

#include <stdexcept>

namespace EMTG
{
    namespace Solvers
    {
        enum class NLPBackend
        {
            None,
            SNOPT,
            IPOPT
        };

        struct NLPBackendResolution
        {
            NLPBackend backend;
            bool usedLegacyFallback;
        };

        inline NLPBackendResolution resolveNLPBackend(const int requestedSolver,
                                                      const NLPBackend compiledBackend)
        {
            switch (requestedSolver)
            {
                case 0:
                    if (compiledBackend == NLPBackend::SNOPT)
                        return { NLPBackend::SNOPT, false };
                    if (compiledBackend == NLPBackend::IPOPT)
                        return { NLPBackend::IPOPT, true };
                    throw std::runtime_error(
                        "NLP_solver_type 0 requests SNOPT, but no NLP backend is available");
                case 1:
                    throw std::runtime_error(
                        "NLP_solver_type 1 requests WORHP, which is no longer supported");
                case 2:
                    if (compiledBackend == NLPBackend::IPOPT)
                        return { NLPBackend::IPOPT, false };
                    throw std::runtime_error(
                        "NLP_solver_type 2 requests IPOPT, but IPOPT is not available in this build");
                default:
                    throw std::out_of_range("Unknown NLP_solver_type");
            }
        }
    }
}