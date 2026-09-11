#include "NLP_solver_factory.h"
#include "NLP_solver_status.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
#include <memory>
#include <string>
#include <vector>

namespace
{
    enum class Scenario
    {
        Successful,
        Infeasible,
        NanFunction,
        InfiniteDerivative
    };

    class DeterministicProblem final : public EMTG::problem
    {
    public:
        explicit DeterministicProblem(const Scenario scenario) : scenario(scenario)
        {
            this->total_number_of_NLP_parameters = 2;
            this->total_number_of_constraints = 3;

            this->Xlowerbounds = { 0.0, 0.0 };
            this->Xupperbounds = { 10.0, 4.0 };
            this->X_scale_factors = { 10.0, 4.0 };
            this->Xdescriptions = { "x", "y" };

            const double equality = scenario == Scenario::Infeasible ? 20.0 : 3.0;
            const double productLowerBound =
                scenario == Scenario::Infeasible ? -1.0e+20 : 2.0;
            this->Flowerbounds = {
                -1.0e+20, equality, productLowerBound };
            this->Fupperbounds = { 1.0e+20, equality, 1.0e+20 };
            this->Fdescriptions = {
                "objective", "linear equality", "nonlinear inequality" };
            this->F_equality_or_inequality = { true, false };

            this->iAfun = { 1, 1 };
            this->jAvar = { 0, 1 };
            this->A = { 10.0, 4.0 };
            this->Adescriptions = { "dF1/dz0", "dF1/dz1" };

            this->iGfun = { 0, 0, 2, 2 };
            this->jGvar = { 0, 1, 0, 1 };
            this->G = std::vector<double>(4, 0.0);
            this->Gdescriptions = {
                "dF0/dz0", "dF0/dz1", "dF2/dz0", "dF2/dz1" };
            this->F = std::vector<doubleType>(3, 0.0);
        }

        void calcbounds() override {}

        std::vector<double> construct_initial_guess() override
        {
            return { 8.0, 0.25 };
        }

        void evaluate(const std::vector<doubleType>& decisionVector,
                      std::vector<doubleType>& functions,
                      std::vector<double>& derivatives,
                      const bool& needDerivatives) override
        {
            const doubleType x = decisionVector[0];
            const doubleType y = decisionVector[1];
            functions[0] = (x - 1.0) * (x - 1.0)
                           + (y - 2.0) * (y - 2.0);
            functions[1] = x + y;
            functions[2] = x * y;

            if (this->scenario == Scenario::NanFunction)
                functions[0] = std::numeric_limits<double>::quiet_NaN();

            if (needDerivatives)
            {
                derivatives[0] = 20.0 * (x _GETVALUE - 1.0);
                derivatives[1] = 8.0 * (y _GETVALUE - 2.0);
                derivatives[2] = 10.0 * (y _GETVALUE);
                derivatives[3] = 4.0 * (x _GETVALUE);
                if (this->scenario == Scenario::InfiniteDerivative)
                    derivatives[0] = std::numeric_limits<double>::infinity();
            }
        }

        void output(const std::string&) override {}

        doubleType getUnscaledObjective() override
        {
            return this->F.front();
        }

    private:
        Scenario scenario;
    };

    EMTG::Solvers::NLPoptions makeOptions(const size_t iterationLimit,
                                           const bool checkDerivatives)
    {
        EMTG::Solvers::NLPoptions options;
        options.set_check_derivatives(checkDerivatives);
        options.set_enable_NLP_chaperone(false);
        options.set_major_iterations_limit(iterationLimit);
        options.set_max_run_time_seconds(30);
        options.set_feasibility_tolerance(1.0e-8);
        options.set_optimality_tolerance(1.0e-10);
        return options;
    }

    std::unique_ptr<EMTG::Solvers::NLP_interface> solve(
        DeterministicProblem& problem,
        const EMTG::Solvers::NLPoptions& options)
    {
        std::unique_ptr<EMTG::Solvers::NLP_interface> solver =
            EMTG::Solvers::createNLPSolver(&problem, options, 2);
        solver->setX0_unscaled({ 8.0, 0.25 });
        solver->run_NLP(false);
        return solver;
    }

    template<typename Value>
    void assertFinite(const std::vector<Value>& values)
    {
        assert(std::all_of(
            values.begin(), values.end(),
            [](const Value& value)
            {
                return std::isfinite(value _GETVALUE);
            }));
    }

    void assertFiniteResults(const EMTG::Solvers::NLP_interface& solver)
    {
        assertFinite(solver.getX_scaled());
        assertFinite(solver.getX_unscaled());
        assertFinite(solver.getF());
        assertFinite(solver.getG());
        assert(std::isfinite(solver.getfeasibility_metric() _GETVALUE));
    }
}

int main()
{
    using EMTG::Solvers::NLPStatus;
    using EMTG::Solvers::solverAcceptedSolution;

    DeterministicProblem successfulProblem(Scenario::Successful);
    std::unique_ptr<EMTG::Solvers::NLP_interface> solver =
        solve(successfulProblem, makeOptions(200, true));

    assert(solver->getStatus() == NLPStatus::AcceptedSolution);
    assert(solverAcceptedSolution(solver->getStatus()));
    assertFiniteResults(*solver);
    const std::vector<doubleType> solution = solver->getX_unscaled();
    const std::vector<doubleType> scaledSolution = solver->getX_scaled();
    const std::vector<doubleType> functions = solver->getF();

    assert(std::abs(solution[0] _GETVALUE - 1.0) <= 1.0e-5);
    assert(std::abs(solution[1] _GETVALUE - 2.0) <= 1.0e-5);
    assert(std::abs(scaledSolution[0] _GETVALUE
                    - solution[0] _GETVALUE / 10.0) <= 1.0e-12);
    assert(std::abs(scaledSolution[1] _GETVALUE
                    - solution[1] _GETVALUE / 4.0) <= 1.0e-12);
    assert(functions[0] _GETVALUE <= 1.0e-10);
    assert(std::abs(functions[1] _GETVALUE - 3.0) <= 1.0e-8);
    assert(functions[2] _GETVALUE >= 2.0 - 1.0e-8);
    std::cout << "EMTG_IPOPT_SCENARIO successful=passed\n";

    DeterministicProblem infeasibleProblem(Scenario::Infeasible);
    solver = solve(infeasibleProblem, makeOptions(200, false));
    assert(solver->getStatus() == NLPStatus::Infeasible);
    assert(!solverAcceptedSolution(solver->getStatus()));
    assertFiniteResults(*solver);
    assert(std::abs(solver->getfeasibility_metric() _GETVALUE) > 1.0);
    std::cout << "EMTG_IPOPT_SCENARIO infeasible=passed\n";

    DeterministicProblem iterationLimitProblem(Scenario::Successful);
    solver = solve(iterationLimitProblem, makeOptions(1, false));
    assert(solver->getStatus() == NLPStatus::IterationLimit);
    assert(!solverAcceptedSolution(solver->getStatus()));
    assertFiniteResults(*solver);
    std::cout << "EMTG_IPOPT_SCENARIO iteration_limit=passed\n";

    DeterministicProblem nanProblem(Scenario::NanFunction);
    solver = solve(nanProblem, makeOptions(200, false));
    assert(solver->getStatus() == NLPStatus::EvaluationError);
    assert(!solverAcceptedSolution(solver->getStatus()));
    std::cout << "EMTG_IPOPT_SCENARIO nan_function=passed\n";

    DeterministicProblem infiniteDerivativeProblem(Scenario::InfiniteDerivative);
    solver = solve(infiniteDerivativeProblem, makeOptions(200, false));
    assert(solver->getStatus() == NLPStatus::EvaluationError);
    assert(!solverAcceptedSolution(solver->getStatus()));
    std::cout << "EMTG_IPOPT_SCENARIO infinite_derivative=passed\n";

    return 0;
}