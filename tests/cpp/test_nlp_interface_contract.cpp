#include "NLP_interface.h"

#include <cassert>
#include <memory>
#include <vector>

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

    return 0;
}