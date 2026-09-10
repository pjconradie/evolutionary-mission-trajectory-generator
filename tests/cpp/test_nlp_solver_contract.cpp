#include "NLP_interface.h"
#include "NLP_solution_acceptance.h"
#include "NLP_solver_selection.h"
#include "SNOPT_status.h"

#include <cassert>
#include <initializer_list>
#include <memory>

namespace
{
    class RecordingNLP final : public EMTG::Solvers::NLP_interface
    {
    public:
        explicit RecordingNLP(bool& wasDestroyed) : wasDestroyed(wasDestroyed) {}

        ~RecordingNLP() override
        {
            this->wasDestroyed = true;
        }

        void run_NLP(const bool&) override
        {
            this->status = EMTG::Solvers::NLPStatus::AcceptedSolution;
        }

        void setConstraintBounds(const std::vector<double>& lower,
                                 const std::vector<double>& upper)
        {
            this->Flowerbounds = lower;
            this->Fupperbounds = upper;
        }

    private:
        bool& wasDestroyed;
    };
}

int main()
{
    using EMTG::Solvers::NLPStatus;
    using EMTG::Solvers::NLPBackend;
    using EMTG::Solvers::acceptNLPSolution;
    using EMTG::Solvers::resolveNLPBackend;
    using EMTG::Solvers::solverAcceptedSolution;
    using EMTG::Solvers::translateSNOPTInform;

    assert(!solverAcceptedSolution(NLPStatus::NotRun));
    assert(solverAcceptedSolution(NLPStatus::AcceptedSolution));
    assert(!solverAcceptedSolution(NLPStatus::IterationLimit));

    bool wasDestroyed = false;
    {
        std::unique_ptr<EMTG::Solvers::NLP_interface> recordingNLP =
            std::make_unique<RecordingNLP>(wasDestroyed);
        assert(recordingNLP->getStatus() == NLPStatus::NotRun);

        static_cast<RecordingNLP&>(*recordingNLP)
            .setConstraintBounds({ -2.0, -1.0 }, { 3.0, 4.0 });
        assert(recordingNLP->getFlowerbounds()
               == std::vector<double>({ -2.0, -1.0 }));
        assert(recordingNLP->getFupperbounds()
               == std::vector<double>({ 3.0, 4.0 }));

        recordingNLP->run_NLP();
        assert(recordingNLP->getStatus() == NLPStatus::AcceptedSolution);
    }
    assert(wasDestroyed);

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

    constexpr double tolerance = 1.0e-5;
    assert(acceptNLPSolution(true, 1.0e-6, 1.0e-6, tolerance,
                             NLPStatus::Error));
    assert(!acceptNLPSolution(true, tolerance, 1.0e-6, tolerance,
                              NLPStatus::AcceptedSolution));
    assert(!acceptNLPSolution(true, 1.0e-6, tolerance, tolerance,
                              NLPStatus::AcceptedSolution));
    assert(acceptNLPSolution(false, tolerance, tolerance, tolerance,
                             NLPStatus::AcceptedSolution));
    assert(!acceptNLPSolution(false, tolerance, tolerance, tolerance,
                              NLPStatus::IterationLimit));

    const auto snopt = resolveNLPBackend(0, NLPBackend::SNOPT);
    assert(snopt.backend == NLPBackend::SNOPT);
    assert(!snopt.usedLegacyFallback);

    const auto legacyFallback = resolveNLPBackend(0, NLPBackend::IPOPT);
    assert(legacyFallback.backend == NLPBackend::IPOPT);
    assert(legacyFallback.usedLegacyFallback);

    const auto ipopt = resolveNLPBackend(2, NLPBackend::IPOPT);
    assert(ipopt.backend == NLPBackend::IPOPT);
    assert(!ipopt.usedLegacyFallback);

    for (const int unavailableRequest : { 0, 1, 2, 3 })
    {
        bool threw = false;
        try
        {
            (void)resolveNLPBackend(unavailableRequest, NLPBackend::None);
        }
        catch (const std::exception&)
        {
            threw = true;
        }
        assert(threw);
    }

    return 0;
}