
# Unit

# Benchmarks


# Tests

## Replay

> **Replay takes the decision-variable values recorded in the SNOPT result, applies those values to the current EMTG mission setup, evaluates that mission without changing the values, then compares the newly calculated result with the saved SNOPT result.**

Step by step:

1. **Read the reference values.** The SNOPT `.emtg` file contains a decision vector: the numbers describing the mission, such as its times, states, and control variables.
2. **Check that the numbers still mean the same things.** Replay aligns the saved values with the current setup’s decision variables by their descriptions and order. If the descriptions don’t match, it stops rather than applying values to the wrong variables. The seed-alignment code is in `inject_aligned_mission_seed`.
3. **Evaluate the current mission at those fixed values.** EMTG uses the current mission model, settings, and dependencies to calculate the trajectory-related quantities, objective, and constraints. It does **not** search for better values or adjust the decision vector. In this mode, EMTG evaluates the supplied trial vector; `run_inner_loop = 0` selects that mode (`enum`, `evaluation path`).
4. **Compare the fresh calculation with the stored SNOPT result.** Checks include mission structure, decision-variable descriptions, objective, mission totals, and endpoint states, with specified tolerances (`comparison code`). The integration harness also checks feasibility (`replay checks`).

An analogy: SNOPT’s result is a saved set of inputs and outputs. Replay holds the inputs fixed, runs today’s calculation on them, and checks whether today’s outputs are sufficiently close to the saved outputs. It is **not** rerunning SNOPT, and it is **not** asking IPOPT to improve the solution.

So “still works” means **“the current mission setup, evaluated at the old SNOPT decision vector, reproduces the agreed checks within tolerance.”** It does not mean the original optimization process is repeatable, that the solution is globally optimal, or that every point along the trajectory is compared exactly.

## Refinement

> **Refinement starts IPOPT from the decision-variable values recorded in the SNOPT result, lets IPOPT adjust those values to optimize the current EMTG mission, then evaluates and compares the resulting mission with the saved SNOPT result.**

Step by step:

1. **Start from the same aligned reference values.** The SNOPT `.emtg` result
   provides the initial decision vector. The setup checks that the values
   align with the current mission's decision-variable descriptions and are
   within the current bounds, just as for Replay.
2. **Evaluate the starting point.** EMTG calculates the objective and
   constraints for that seed, then passes the vector to IPOPT as its starting
   point.
3. **Let IPOPT change the decision variables.** Unlike Replay, the values are
   no longer fixed. IPOPT searches for a point that satisfies the constraints
   and improves the configured objective. The run uses the current mission
   model, settings, and dependencies; it does not rerun SNOPT.
4. **Evaluate and compare IPOPT's result.** EMTG evaluates the final vector,
   and the result is checked for IPOPT success, feasibility, mission
   structure, objective, mission totals, and endpoint states against the
   reference, using the applicable tolerances (`refinement comparison code`).

An analogy: Replay checks what today's calculator produces when given the old
SNOPT inputs and does not change them. Refinement gives those same inputs to an
optimizer and allows it to adjust them before checking the resulting outputs
against the SNOPT reference.

So refinement means **“starting from the SNOPT solution, can IPOPT find an
acceptable solution for the current mission, and how does that solution
compare with SNOPT's?”** It does not guarantee that IPOPT will find a better
solution, the same decision vector, or even an acceptable solution. It is a
local optimization run; its outcome depends on the starting point, formulation,
solver settings, and available dependencies.

## Monotonic Basin Hopping (no such test implemented yet)

**MBH—Monotonic Basin Hopping—is used when you want EMTG to search broadly for a good solution, rather than run one local optimization from one starting point.**

Trajectory-optimization problems can have many **local optima**: solutions that are best nearby, but not necessarily best across the whole search space. A direct NLP run, such as IPOPT refinement, starts from one guess and typically converges to an optimum in its neighborhood. MBH tries to find better neighborhoods:

1. It starts from a random point or, if configured, a supplied seed.
2. It runs the configured NLP solver to locally optimize that point.
3. It perturbs the current point (“hops”) and runs another local optimization from the perturbed point.
4. It keeps track of good solutions and continues until it reaches its configured trial limit or time limit.

In EMTG, MBH is selected with `run_inner_loop 1` (`solver modes`). The “monotonic” part means it generally moves its incumbent toward better solutions, while the hops let it explore other regions. It’s a **heuristic search**, not a guarantee of finding the global optimum. The project’s `solver design documentation` describes this pattern.

In practice, MBH is useful for **preliminary design or difficult, highly multimodal problems**, where a single initial guess may lead to a poor local optimum. Once you have a promising solution, you might then run a direct NLP solve to refine it. MBH can optionally start from a seed (`MBH configuration`).

For the distinction we discussed earlier: **Replay evaluates a fixed SNOPT solution; refinement runs one IPOPT optimization from it; MBH repeatedly perturbs points and runs local optimizations to search across multiple regions.** The repository’s `IPOPT benchmark guide` describes replay and refinement; those stages are separate from MBH.

```for testing implementation
Select the SNOPT optimal solution seed to prime MBH
Allow MBH to search for a global solution.
The solution just needs to compare on an order of magnitude level.
What to do when days are out or delta V small or big? Dont know. Will deal with it when it comes up.
```

