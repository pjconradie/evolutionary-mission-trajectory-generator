#include "IPOPT_interface.h"

#include "IPOPT_status.h"
#include "IpIpoptApplication.hpp"
#include "IpTNLP.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace EMTG
{
    namespace Solvers
    {
        namespace
        {
            IPOPTTermination translateApplicationStatus(
                const Ipopt::ApplicationReturnStatus status)
            {
                switch (status)
                {
                    case Ipopt::Solve_Succeeded:
                        return IPOPTTermination::SolveSucceeded;
                    case Ipopt::Solved_To_Acceptable_Level:
                        return IPOPTTermination::SolvedToAcceptableLevel;
                    case Ipopt::Infeasible_Problem_Detected:
                        return IPOPTTermination::InfeasibleProblemDetected;
                    case Ipopt::Search_Direction_Becomes_Too_Small:
                        return IPOPTTermination::SearchDirectionTooSmall;
                    case Ipopt::Diverging_Iterates:
                        return IPOPTTermination::DivergingIterates;
                    case Ipopt::User_Requested_Stop:
                        return IPOPTTermination::UserRequestedStop;
                    case Ipopt::Feasible_Point_Found:
                        return IPOPTTermination::FeasiblePointFound;
                    case Ipopt::Maximum_Iterations_Exceeded:
                        return IPOPTTermination::MaximumIterationsExceeded;
                    case Ipopt::Restoration_Failed:
                        return IPOPTTermination::RestorationFailed;
                    case Ipopt::Error_In_Step_Computation:
                        return IPOPTTermination::ErrorInStepComputation;
                    case Ipopt::Maximum_CpuTime_Exceeded:
                        return IPOPTTermination::MaximumCpuTimeExceeded;
                    case Ipopt::Not_Enough_Degrees_Of_Freedom:
                        return IPOPTTermination::NotEnoughDegreesOfFreedom;
                    case Ipopt::Invalid_Problem_Definition:
                        return IPOPTTermination::InvalidProblemDefinition;
                    case Ipopt::Invalid_Option:
                        return IPOPTTermination::InvalidOption;
                    case Ipopt::Invalid_Number_Detected:
                        return IPOPTTermination::InvalidNumberDetected;
                    case Ipopt::Unrecoverable_Exception:
                        return IPOPTTermination::UnrecoverableException;
                    case Ipopt::NonIpopt_Exception_Thrown:
                        return IPOPTTermination::NonIpoptExceptionThrown;
                    case Ipopt::Insufficient_Memory:
                        return IPOPTTermination::InsufficientMemory;
                    case Ipopt::Internal_Error:
                        return IPOPTTermination::InternalError;
                }

                return IPOPTTermination::InternalError;
            }
        }

        class IPOPT_interface::TNLPBridge final : public Ipopt::TNLP
        {
        public:
            explicit TNLPBridge(IPOPT_interface& owner) : owner(owner) {}

            bool get_nlp_info(Ipopt::Index& n,
                              Ipopt::Index& m,
                              Ipopt::Index& nnz_jac_g,
                              Ipopt::Index& nnz_h_lag,
                              IndexStyleEnum& index_style) override
            {
                n = static_cast<Ipopt::Index>(this->owner.nX);
                m = static_cast<Ipopt::Index>(this->owner.nF - 1);
                nnz_jac_g = static_cast<Ipopt::Index>(
                    this->owner.derivativeLayout->getConstraintEntries().size());
                nnz_h_lag = 0;
                index_style = C_STYLE;
                return true;
            }

            bool get_bounds_info(Ipopt::Index n,
                                 Ipopt::Number* x_l,
                                 Ipopt::Number* x_u,
                                 Ipopt::Index m,
                                 Ipopt::Number* g_l,
                                 Ipopt::Number* g_u) override
            {
                if (n != static_cast<Ipopt::Index>(this->owner.nX)
                    || m != static_cast<Ipopt::Index>(this->owner.nF - 1))
                    return false;

                for (size_t index = 0; index < this->owner.nX; ++index)
                {
                    x_l[index] = 0.0;
                    x_u[index] =
                        (this->owner.myProblem->Xupperbounds[index]
                         - this->owner.myProblem->Xlowerbounds[index])
                        / this->owner.myProblem->X_scale_factors[index];
                }
                for (size_t index = 1; index < this->owner.nF; ++index)
                {
                    g_l[index - 1] = this->owner.Flowerbounds[index];
                    g_u[index - 1] = this->owner.Fupperbounds[index];
                }
                return true;
            }

            bool get_starting_point(Ipopt::Index n,
                                    bool init_x,
                                    Ipopt::Number* x,
                                    bool init_z,
                                    Ipopt::Number*,
                                    Ipopt::Number*,
                                    Ipopt::Index,
                                    bool init_lambda,
                                    Ipopt::Number*) override
            {
                if (n != static_cast<Ipopt::Index>(this->owner.nX)
                    || !init_x || init_z || init_lambda)
                    return false;

                for (size_t index = 0; index < this->owner.nX; ++index)
                    x[index] = this->owner.X0_scaled[index] _GETVALUE;
                return true;
            }

            bool eval_f(Ipopt::Index n,
                        const Ipopt::Number* x,
                        bool,
                        Ipopt::Number& objective) override
            {
                if (n != static_cast<Ipopt::Index>(this->owner.nX)
                    || !this->owner.evaluatePoint(x, false))
                    return false;
                objective = this->owner.F.front() _GETVALUE;
                return std::isfinite(objective);
            }

            bool eval_grad_f(Ipopt::Index n,
                             const Ipopt::Number* x,
                             bool,
                             Ipopt::Number* gradient) override
            {
                if (n != static_cast<Ipopt::Index>(this->owner.nX)
                    || !this->owner.evaluatePoint(x, true))
                    return false;

                const std::vector<double> values =
                    this->owner.derivativeLayout->objectiveGradient(
                        this->owner.A,
                        this->owner.G);
                std::copy(values.begin(), values.end(), gradient);
                const bool valid = std::all_of(
                    values.begin(), values.end(),
                    [](const double value)
                    {
                        return std::isfinite(value);
                    });
                if (!valid)
                    this->owner.status = NLPStatus::EvaluationError;
                return valid;
            }

            bool eval_g(Ipopt::Index n,
                        const Ipopt::Number* x,
                        bool,
                        Ipopt::Index m,
                        Ipopt::Number* constraints) override
            {
                if (n != static_cast<Ipopt::Index>(this->owner.nX)
                    || m != static_cast<Ipopt::Index>(this->owner.nF - 1)
                    || !this->owner.evaluatePoint(x, false))
                    return false;

                for (size_t index = 1; index < this->owner.nF; ++index)
                {
                    constraints[index - 1] =
                        this->owner.F[index] _GETVALUE;
                    if (!std::isfinite(constraints[index - 1]))
                        return false;
                }
                return true;
            }

            bool eval_jac_g(Ipopt::Index n,
                            const Ipopt::Number* x,
                            bool,
                            Ipopt::Index m,
                            Ipopt::Index numberOfEntries,
                            Ipopt::Index* rows,
                            Ipopt::Index* columns,
                            Ipopt::Number* values) override
            {
                const auto& entries =
                    this->owner.derivativeLayout->getConstraintEntries();
                if (n != static_cast<Ipopt::Index>(this->owner.nX)
                    || m != static_cast<Ipopt::Index>(this->owner.nF - 1)
                    || numberOfEntries != static_cast<Ipopt::Index>(entries.size()))
                    return false;

                if (values == nullptr)
                {
                    for (size_t index = 0; index < entries.size(); ++index)
                    {
                        rows[index] = static_cast<Ipopt::Index>(entries[index].row);
                        columns[index] =
                            static_cast<Ipopt::Index>(entries[index].column);
                    }
                    return true;
                }

                if (!this->owner.evaluatePoint(x, true))
                    return false;
                const std::vector<double> derivatives =
                    this->owner.derivativeLayout->constraintJacobian(
                        this->owner.A,
                        this->owner.G);
                std::copy(derivatives.begin(), derivatives.end(), values);
                const bool valid = std::all_of(
                    derivatives.begin(), derivatives.end(),
                    [](const double value)
                    {
                        return std::isfinite(value);
                    });
                if (!valid)
                    this->owner.status = NLPStatus::EvaluationError;
                return valid;
            }

            void finalize_solution(Ipopt::SolverReturn,
                                   Ipopt::Index n,
                                   const Ipopt::Number* x,
                                   const Ipopt::Number*,
                                   const Ipopt::Number*,
                                   Ipopt::Index m,
                                   const Ipopt::Number* constraints,
                                   const Ipopt::Number*,
                                   Ipopt::Number objective,
                                   const Ipopt::IpoptData*,
                                   Ipopt::IpoptCalculatedQuantities*) override
            {
                if (n != static_cast<Ipopt::Index>(this->owner.nX)
                    || m != static_cast<Ipopt::Index>(this->owner.nF - 1))
                    return;

                for (size_t index = 0; index < this->owner.nX; ++index)
                    this->owner.X_scaled[index] = x[index];
                this->owner.unscaleX();
                this->owner.F.front() = objective;
                for (size_t index = 1; index < this->owner.nF; ++index)
                    this->owner.F[index] = constraints[index - 1];
            }

        private:
            IPOPT_interface& owner;
        };

        IPOPT_interface::IPOPT_interface(problem* myProblem,
                                         const NLPoptions& myOptions) :
            NLP_interface(myProblem, myOptions)
        {
            const bool filamentFinder =
                this->myOptions.get_SolverMode() == NLPMode::FilamentFinder;
            this->derivativeLayout = std::make_unique<SparseDerivativeLayout>(
                this->nX,
                this->nF,
                filamentFinder ? std::vector<size_t>() : this->iAfun,
                filamentFinder ? std::vector<size_t>() : this->jAvar,
                this->iGfun,
                this->jGvar);
        }

        bool IPOPT_interface::evaluatePoint(const double* scaledX,
                                            const bool needDerivatives)
        {
            try
            {
                for (size_t index = 0; index < this->nX; ++index)
                    this->X_scaled[index] = scaledX[index];
                this->unscaleX();

                if (this->myOptions.get_SolverMode() == NLPMode::FilamentFinder)
                {
                    this->myProblem->evaluate(this->X_unscaled,
                                              this->myProblem->F,
                                              this->myProblem->G,
                                              needDerivatives);
                    this->F.front() = 0.0;
                    for (size_t functionIndex = 1;
                         functionIndex < this->myProblem->total_number_of_constraints;
                         ++functionIndex)
                    {
                        if (this->myProblem->F_equality_or_inequality[functionIndex - 1])
                        {
                            const double value =
                                this->myProblem->F[functionIndex] _GETVALUE;
                            this->F.front() += value * value;
                        }
                    }

                    std::fill(this->G.begin(), this->G.end(), 0.0);
                    for (size_t derivativeIndex = 0;
                         derivativeIndex < this->myProblem->Gdescriptions.size();
                         ++derivativeIndex)
                    {
                        const size_t functionIndex =
                            this->myProblem->iGfun[derivativeIndex];
                        const size_t variableIndex =
                            this->myProblem->jGvar[derivativeIndex];
                        if (functionIndex > 0
                            && this->myProblem->F_equality_or_inequality[functionIndex - 1])
                        {
                            this->G[variableIndex] +=
                                2.0
                                * (this->myProblem->F[functionIndex] _GETVALUE)
                                * this->myProblem->G[derivativeIndex];
                        }
                    }

                    for (size_t functionIndex = 1;
                         functionIndex < this->nF;
                         ++functionIndex)
                    {
                        this->F[functionIndex] = this->myProblem->F[
                            this->myProblem
                                ->F_indices_of_filament_critical_inequality_constraints[
                                    functionIndex - 1]];
                    }
                    for (size_t derivativeIndex = this->nX;
                         derivativeIndex < this->nG;
                         ++derivativeIndex)
                    {
                        this->G[derivativeIndex] = this->myProblem->G[
                            this->original_G_indices_of_filament_critical_inequality_constraints[
                                derivativeIndex - this->nX]];
                    }
                }
                else
                {
                    this->myProblem->evaluate(this->X_unscaled,
                                              this->F,
                                              this->G,
                                              needDerivatives);
                }
            }
            catch (...)
            {
                this->status = NLPStatus::EvaluationError;
                return false;
            }

            const bool valid = std::all_of(
                this->F.begin(), this->F.end(),
                [](const doubleType& value)
                {
                    return std::isfinite(value _GETVALUE);
                });
            if (!valid)
                this->status = NLPStatus::EvaluationError;
            return valid;
        }

        void IPOPT_interface::run_NLP(const bool& X0_is_scaled)
        {
            if (X0_is_scaled)
                this->unscaleX0();
            else
                this->scaleX0();

            this->X_scaled = this->X0_scaled;
            this->status = NLPStatus::NotRun;

            Ipopt::SmartPtr<Ipopt::IpoptApplication> application =
                IpoptApplicationFactory();
            application->Options()->SetStringValue(
                "hessian_approximation", "limited-memory");
            application->Options()->SetStringValue(
                "nlp_scaling_method", "none");
            application->Options()->SetNumericValue(
                "tol", this->myOptions.get_optimality_tolerance());
            application->Options()->SetNumericValue(
                "constr_viol_tol", this->myOptions.get_feasibility_tolerance());
            application->Options()->SetIntegerValue(
                "max_iter",
                static_cast<int>(this->myOptions.get_major_iterations_limit()));
            application->Options()->SetNumericValue(
                "max_cpu_time",
                static_cast<double>(this->myOptions.get_max_run_time_seconds()));
            if (this->myOptions.get_quiet_NLP())
                application->Options()->SetIntegerValue("print_level", 0);
            if (this->myOptions.get_check_derivatives())
                application->Options()->SetStringValue(
                    "derivative_test", "first-order");

            if (application->Initialize() != Ipopt::Solve_Succeeded)
            {
                this->status = NLPStatus::Error;
                throw std::runtime_error("Failed to initialize IPOPT");
            }

            Ipopt::SmartPtr<Ipopt::TNLP> bridge = new TNLPBridge(*this);
            const Ipopt::ApplicationReturnStatus ipoptStatus =
                application->OptimizeTNLP(bridge);
            if (this->status != NLPStatus::EvaluationError)
            {
                this->status = translateIPOPTTermination(
                    translateApplicationStatus(ipoptStatus));
            }

            this->myProblem->check_feasibility(
                this->X_unscaled,
                this->F,
                this->worst_decision_variable,
                this->worst_constraint,
                this->feasibility_metric,
                this->normalized_feasibility_metric,
                this->distance_from_equality_filament,
                this->decision_vector_feasibility_metric);
        }
    }
}