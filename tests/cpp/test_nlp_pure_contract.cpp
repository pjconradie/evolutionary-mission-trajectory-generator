#include "IPOPT_status.h"
#include "NLP_initialization_policy.h"
#include "NLP_solution_acceptance.h"
#include "NLP_solver_selection.h"
#include "NLP_sparse_derivative_layout.h"
#include "SNOPT_status.h"

#include <cassert>
#include <cmath>
#include <initializer_list>
#include <limits>
#include <stdexcept>
#include <vector>

int main()
{
    using EMTG::Solvers::IPOPTTermination;
    using EMTG::Solvers::NLPBackend;
        using EMTG::Solvers::NLPInitializationPolicy;
    using EMTG::Solvers::NLPStatus;
    using EMTG::Solvers::SparseDerivativeLayout;
    using EMTG::Solvers::acceptNLPSolution;
        using EMTG::Solvers::consumeMBHInitializationPolicy;
        using EMTG::Solvers::isEMTGFeasible;
        using EMTG::Solvers::isIncumbentCandidateSuperior;
        using EMTG::Solvers::isObjectiveSuperior;
    using EMTG::Solvers::resolveNLPBackend;
    using EMTG::Solvers::solverAcceptedSolution;
    using EMTG::Solvers::translateIPOPTTermination;
    using EMTG::Solvers::translateSNOPTInform;

    assert(!solverAcceptedSolution(NLPStatus::NotRun));
    assert(solverAcceptedSolution(NLPStatus::AcceptedSolution));
    assert(!solverAcceptedSolution(NLPStatus::IterationLimit));

    bool seededStep = true;
    assert(consumeMBHInitializationPolicy(seededStep)
           == NLPInitializationPolicy::NearFeasiblePrimalSeed);
    assert(!seededStep);
    assert(consumeMBHInitializationPolicy(seededStep)
           == NLPInitializationPolicy::Default);

    bool coldStart = false;
    assert(consumeMBHInitializationPolicy(coldStart)
           == NLPInitializationPolicy::Default);
    assert(!coldStart);

    for (int inform = 0; inform < 10; ++inform)
        assert(translateSNOPTInform(inform) == NLPStatus::AcceptedSolution);
    assert(translateSNOPTInform(-1) == NLPStatus::Error);
    assert(translateSNOPTInform(10) == NLPStatus::Infeasible);
    assert(translateSNOPTInform(20) == NLPStatus::Unbounded);
    assert(translateSNOPTInform(30) == NLPStatus::IterationLimit);
    assert(translateSNOPTInform(40) == NLPStatus::NumericalError);
    assert(translateSNOPTInform(50) == NLPStatus::EvaluationError);
    assert(translateSNOPTInform(70) == NLPStatus::UserTerminated);
    assert(translateSNOPTInform(80) == NLPStatus::Error);

    assert(translateIPOPTTermination(IPOPTTermination::SolveSucceeded)
           == NLPStatus::AcceptedSolution);
    assert(translateIPOPTTermination(IPOPTTermination::SolvedToAcceptableLevel)
           == NLPStatus::AcceptedSolution);
    assert(translateIPOPTTermination(IPOPTTermination::FeasiblePointFound)
           == NLPStatus::AcceptedSolution);
    assert(translateIPOPTTermination(IPOPTTermination::InfeasibleProblemDetected)
           == NLPStatus::Infeasible);
    assert(translateIPOPTTermination(IPOPTTermination::MaximumIterationsExceeded)
           == NLPStatus::IterationLimit);
    assert(translateIPOPTTermination(IPOPTTermination::MaximumCpuTimeExceeded)
           == NLPStatus::TimeLimit);
    assert(translateIPOPTTermination(IPOPTTermination::DivergingIterates)
           == NLPStatus::Unbounded);
    assert(translateIPOPTTermination(IPOPTTermination::UserRequestedStop)
           == NLPStatus::UserTerminated);
    assert(translateIPOPTTermination(IPOPTTermination::InvalidNumberDetected)
           == NLPStatus::EvaluationError);
    for (const IPOPTTermination termination : {
             IPOPTTermination::SearchDirectionTooSmall,
             IPOPTTermination::RestorationFailed,
             IPOPTTermination::ErrorInStepComputation })
        assert(translateIPOPTTermination(termination) == NLPStatus::NumericalError);
    for (const IPOPTTermination termination : {
             IPOPTTermination::InvalidProblemDefinition,
             IPOPTTermination::InvalidOption,
             IPOPTTermination::NotEnoughDegreesOfFreedom,
             IPOPTTermination::UnrecoverableException,
             IPOPTTermination::NonIpoptExceptionThrown,
             IPOPTTermination::InsufficientMemory,
             IPOPTTermination::InternalError })
        assert(translateIPOPTTermination(termination) == NLPStatus::Error);

    const SparseDerivativeLayout derivativeLayout(
        2,
        3,
        { 0, 1, 1 },
        { 0, 0, 1 },
        { 0, 0, 2, 2, 2 },
        { 0, 0, 0, 0, 1 });
    assert(derivativeLayout.objectiveGradient(
               { 3.0, 5.0, 7.0 },
               { 11.0, 13.0, 17.0, 19.0, 23.0 })
           == std::vector<double>({ 27.0, 0.0 }));

    const auto& entries = derivativeLayout.getConstraintEntries();
    assert(entries.size() == 4);
    assert(entries[0].row == 0 && entries[0].column == 0);
    assert(entries[1].row == 0 && entries[1].column == 1);
    assert(entries[2].row == 1 && entries[2].column == 0);
    assert(entries[3].row == 1 && entries[3].column == 1);
    assert(derivativeLayout.constraintJacobian(
               { 3.0, 5.0, 7.0 },
               { 11.0, 13.0, 17.0, 19.0, 23.0 })
           == std::vector<double>({ 5.0, 7.0, 36.0, 23.0 }));

    constexpr double tolerance = 1.0e-5;
    assert(acceptNLPSolution(true, 1.0e-6, 1.0e-6, tolerance,
                             NLPStatus::Error));
       assert(acceptNLPSolution(true, tolerance, 1.0e-6, tolerance,
                                                  NLPStatus::AcceptedSolution));
       assert(acceptNLPSolution(true, 1.0e-6, tolerance, tolerance,
                                                  NLPStatus::AcceptedSolution));
    assert(acceptNLPSolution(false, tolerance, tolerance, tolerance,
                             NLPStatus::AcceptedSolution));
       assert(acceptNLPSolution(false, tolerance, tolerance, tolerance,
                                                  NLPStatus::IterationLimit));
       assert(isEMTGFeasible(tolerance, tolerance, tolerance));
       assert(!isEMTGFeasible(
              std::nextafter(tolerance, std::numeric_limits<double>::infinity()),
              tolerance,
              tolerance));
       assert(!isEMTGFeasible(std::numeric_limits<double>::quiet_NaN(),
                                             0.0,
                                             tolerance));
       assert(!isEMTGFeasible(0.0,
                                             std::numeric_limits<double>::infinity(),
                                             tolerance));

       assert(isObjectiveSuperior(-2.0, -1.0));
       assert(!isObjectiveSuperior(-1.0, -2.0));
       assert(!isObjectiveSuperior(-1.0 - 5.0e-11, -1.0));
       assert(isObjectiveSuperior(-1.0 - 2.0e-10, -1.0));
       assert(!isObjectiveSuperior(
              std::numeric_limits<double>::quiet_NaN(), -1.0));
       assert(isObjectiveSuperior(
              -1.0, std::numeric_limits<double>::infinity()));

       assert(isIncumbentCandidateSuperior(
              10.0, tolerance, 1.0, tolerance * 2.0, tolerance));
       assert(!isIncumbentCandidateSuperior(
              1.0, tolerance * 2.0, 10.0, tolerance, tolerance));
       assert(isIncumbentCandidateSuperior(
              -2.0, tolerance, -1.0, tolerance, tolerance));
       assert(!isIncumbentCandidateSuperior(
              -1.0 - 5.0e-11, tolerance, -1.0, tolerance, tolerance));
       assert(isIncumbentCandidateSuperior(
              10.0, tolerance * 2.0, 1.0, tolerance * 3.0, tolerance));

    const auto snopt = resolveNLPBackend(0, NLPBackend::SNOPT);
    assert(snopt.backend == NLPBackend::SNOPT && !snopt.usedLegacyFallback);
    const auto legacy = resolveNLPBackend(0, NLPBackend::IPOPT);
    assert(legacy.backend == NLPBackend::IPOPT && legacy.usedLegacyFallback);
    const auto ipopt = resolveNLPBackend(2, NLPBackend::IPOPT);
    assert(ipopt.backend == NLPBackend::IPOPT && !ipopt.usedLegacyFallback);

    for (const int request : { 0, 1, 2, 3 })
    {
        bool threw = false;
        try
        {
            (void)resolveNLPBackend(request, NLPBackend::None);
        }
        catch (const std::exception&)
        {
            threw = true;
        }
        assert(threw);
    }

    return 0;
}