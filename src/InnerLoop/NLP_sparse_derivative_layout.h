#pragma once

#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

namespace EMTG
{
    namespace Solvers
    {
        struct SparseDerivativeEntry
        {
            size_t row;
            size_t column;
            std::vector<size_t> linearIndices;
            std::vector<size_t> nonlinearIndices;
        };

        class SparseDerivativeLayout
        {
        public:
            SparseDerivativeLayout(
                const size_t numberOfVariables,
                const size_t numberOfFunctions,
                const std::vector<size_t>& linearRows,
                const std::vector<size_t>& linearColumns,
                const std::vector<size_t>& nonlinearRows,
                const std::vector<size_t>& nonlinearColumns) :
                numberOfVariables(numberOfVariables)
            {
                if (linearRows.size() != linearColumns.size()
                    || nonlinearRows.size() != nonlinearColumns.size())
                {
                    throw std::invalid_argument(
                        "Sparse derivative row and column arrays differ in size");
                }

                this->objectiveLinearIndices.resize(numberOfVariables);
                this->objectiveNonlinearIndices.resize(numberOfVariables);
                std::map<std::pair<size_t, size_t>, SparseDerivativeEntry>
                    constraintEntries;

                this->addSources(numberOfFunctions,
                                 linearRows,
                                 linearColumns,
                                 true,
                                 constraintEntries);
                this->addSources(numberOfFunctions,
                                 nonlinearRows,
                                 nonlinearColumns,
                                 false,
                                 constraintEntries);

                for (const auto& item : constraintEntries)
                    this->constraints.push_back(item.second);
            }

            const std::vector<SparseDerivativeEntry>&
            getConstraintEntries() const
            {
                return this->constraints;
            }

            std::vector<double> objectiveGradient(
                const std::vector<double>& linearValues,
                const std::vector<double>& nonlinearValues) const
            {
                std::vector<double> gradient(this->numberOfVariables, 0.0);
                for (size_t column = 0;
                     column < this->numberOfVariables;
                     ++column)
                {
                    gradient[column] = this->sumSources(
                        this->objectiveLinearIndices[column],
                        linearValues,
                        this->objectiveNonlinearIndices[column],
                        nonlinearValues);
                }
                return gradient;
            }

            std::vector<double> constraintJacobian(
                const std::vector<double>& linearValues,
                const std::vector<double>& nonlinearValues) const
            {
                std::vector<double> values;
                values.reserve(this->constraints.size());
                for (const SparseDerivativeEntry& entry : this->constraints)
                {
                    values.push_back(this->sumSources(entry.linearIndices,
                                                      linearValues,
                                                      entry.nonlinearIndices,
                                                      nonlinearValues));
                }
                return values;
            }

        private:
            void addSources(
                const size_t numberOfFunctions,
                const std::vector<size_t>& rows,
                const std::vector<size_t>& columns,
                const bool linear,
                std::map<std::pair<size_t, size_t>, SparseDerivativeEntry>&
                    constraintEntries)
            {
                for (size_t sourceIndex = 0;
                     sourceIndex < rows.size();
                     ++sourceIndex)
                {
                    const size_t functionRow = rows[sourceIndex];
                    const size_t column = columns[sourceIndex];
                    if (functionRow >= numberOfFunctions
                        || column >= this->numberOfVariables)
                    {
                        throw std::out_of_range(
                            "Sparse derivative index is outside the NLP dimensions");
                    }

                    if (functionRow == 0)
                    {
                        std::vector<size_t>& indices = linear
                            ? this->objectiveLinearIndices[column]
                            : this->objectiveNonlinearIndices[column];
                        indices.push_back(sourceIndex);
                        continue;
                    }

                    const std::pair<size_t, size_t> key(
                        functionRow - 1,
                        column);
                    auto insertion = constraintEntries.emplace(
                        key,
                        SparseDerivativeEntry{
                            functionRow - 1, column, {}, {} });
                    std::vector<size_t>& indices = linear
                        ? insertion.first->second.linearIndices
                        : insertion.first->second.nonlinearIndices;
                    indices.push_back(sourceIndex);
                }
            }

            static double sumSources(
                const std::vector<size_t>& linearIndices,
                const std::vector<double>& linearValues,
                const std::vector<size_t>& nonlinearIndices,
                const std::vector<double>& nonlinearValues)
            {
                double value = 0.0;
                for (const size_t index : linearIndices)
                {
                    if (index >= linearValues.size())
                        throw std::out_of_range("Missing linear derivative value");
                    value += linearValues[index];
                }
                for (const size_t index : nonlinearIndices)
                {
                    if (index >= nonlinearValues.size())
                        throw std::out_of_range("Missing nonlinear derivative value");
                    value += nonlinearValues[index];
                }
                return value;
            }

            size_t numberOfVariables;
            std::vector<std::vector<size_t>> objectiveLinearIndices;
            std::vector<std::vector<size_t>> objectiveNonlinearIndices;
            std::vector<SparseDerivativeEntry> constraints;
        };
    }
}