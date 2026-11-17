# Scoring and allocation: design proposal

Status: proposal for discussion. Nothing here is decided. The evidence is in `scoring-plan.md`, and the code in `nbs/07_scoring.ipynb` and `nbs/_scoring_experiments.ipynb`.

## Summary

trufl would allocate samples so that decision makers' decisions are right, not so that every unit is described equally well. Four parts, each with one job:

- A decision rule, given as input: the rule decision makers apply to a unit's samples, such as the DSS4NAFA restriction rule.
- An information layer: it allocates each round's budget where samples most lower the expected number of wrong decisions under that rule. `voi` is the current version.
- A value layer: MCDM, as today, but on value criteria only (population, production, economic value), giving each unit a weight for what is at stake there.
- A simulation module: campaigns over a ground truth, strategies and scores, to compare strategies before an emergency.

## Evidence

From `scoring-plan.md`, wrong restriction decisions after six rounds of 150 samples, 20 seeds:

- On `ground-truth-02` at a level of 0.473: 10.0 with equal allocation, 7.8 with `bayes`, 4.0 with `voi` and a perfect prior.
- On three windows of the 2011 Fukushima raster, `bayes` beats equal allocation in all six settings, and the how-to MCDM strategy in five.
- Scored on the error of unit means instead of decisions, no strategy beats equal allocation. MCDM was scored on a job it was not designed for.
- A prior helps only when the allocation predicts the decision the rule will make from the samples (`voi`). With `bayes`, which trusts the prior, even a perfect prior makes decisions worse.
- With realistic priors, `voi` gains only if the prior's weight matches its quality: a poor prior with too much weight does worse than equal allocation.

## Decision rule

A decision rule takes a unit's sample values and returns an action: `restrict`, `no restrict`, `sample` (too few samples) or `undefined` (no samples). The first rule is the DSS4NAFA rule with three settings: permissible level, minimum number of samples and accepted proportion over the level.

The information layer needs more than the action. To predict a future decision, it needs the number of exceedances the rule requires for each number of samples. Proposed: a small class per rule, for example `ShareRule(level, accepted, min_n)`, with `decide(values)` and `needed(n)`. `expected_wrong` then works for any rule that decides on a count of exceedances. A rule on the measured values themselves (see the sawtooth in `nbs/_explain_04_sawtooth.ipynb`) would need a different `expected_wrong`.

## Information layer

A strategy is a function `(samples, gdf_units, budget, rng) -> n`, giving the number of samples for each unit in `gdf_units` order. The proposed public strategy is `voi(rule, min_total, prior, strength, horizon)`:

- It tops each unit up to `min_total` samples over the whole campaign. This is the dashboard's minimum number of samples, a decision makers' setting.
- It gives each remaining sample to the unit with the largest drop of `expected_wrong` per sample over the next 1 to `horizon` samples.
- `prior` is an optional raster, such as an airborne survey, and `strength` the number of samples it is worth.

With a value layer, the gain of each unit is multiplied by its stake weight, so a sample goes where it most lowers the stake-weighted number of wrong decisions. With no value layer, every weight is 1.

`allocate` (proportional allocation after a minimum) is a shared helper. `bayes`, `equal` and `neyman` are baselines, and stay in the simulation module.

## Value layer

`Optimizer`, `State` and the callbacks keep their role of ranking units, on value criteria. The proposed change is in what they are used for: they give `voi` a weight per unit instead of deciding the allocation themselves through `rank_to_sample`.

Two open points:

- How a rank becomes a weight. A rank loses the size of the differences between units; the `CP` or `TOPSIS` score keeps it. Proposed: use the score, rescaled to [0, 1].
- Whether the information criteria (`StdCB`, `CountCB`, `MoranICB`) stay in the recommended path. With `voi` handling information, they are not needed for allocation. They stay in the library for existing users.

## Simulation module

Proposed module `trufl.simulation`, exported from `nbs/07_scoring.ipynb`:

- `Campaign(fname_raster, gdf_units, score)` with `reset(seed)` and `step(n)`, `run(campaign, strategy, budgets, seed)` and `compare(campaign, strategies, budgets, seeds, summary)`.
- `unit_values`, `degrade` (prior rasters), and the scores `decisions` and `unit_stats` with their summaries.
- The baselines `equal`, `neyman`, `bayes`, the oracles, `cumulative_min`, and `mcdm` for the how-to strategy.

Its main use is comparing strategies before an emergency, on simulated ground truths. Measurement noise in `DataCollector` (#11) belongs here too.

## Changes to published behaviour

Each of these needs your decision:

1. `StdCB` returns NaN below 2 samples, and uses the sample standard deviation (`ddof=1`). Today a unit with one sample gets 0, which ranks it as the least uncertain.
2. `MoranICB`: return 0 when Moran's I is not significant, return I always with the p-value as a second variable, or keep NaN for both cases and document it. A significant negative Moran's I already stopped a run (`LINEAR1` rejects negative values).
3. `LINEAR1` rejects any zero or negative value. Options: make `LINEAR2` the default in examples and the how-to, or clip, or document. This matters less if information criteria leave the recommended path, since value criteria are rarely negative.
4. `rank_to_sample` stays as it is. The how-to page keeps working; a new how-to shows `voi`.
5. New public modules or functions: the rule class, `voi`, `expected_wrong`, `allocate`, and `trufl.simulation`. Names and module boundaries are open.

## Out of scope for the first version

- Stakes data and their elicitation. The value layer starts with weight 1 for every unit.
- The asymmetry between a missed and a needless restriction.
- Several foodstuffs and radionuclides sharing one budget.
- "Partially restrict", and placement within a unit (uniform random for now).
- How to set the weight of a prior from its quality.
- Reinforcement learning for the information layer.

## Questions for DSS4NAFA

- The sawtooth: with the current rule, one more sample can make a decision less reliable. With 10% accepted, a unit whose true share is 12% is decided wrongly 32% of the time with 9 samples and 66% with 10.
- Should restriction decisions use prior information, such as the airborne survey, as well as samples?

## Proposed order

Each step fits one commit, after your decisions above:

1. The `StdCB` and `MoranICB` changes, if agreed.
2. The decision rule class, `expected_wrong` and `voi` in the library, with `voi` taking stake weights (all 1 by default).
3. `trufl.simulation`, exported from `nbs/07_scoring.ipynb`, with measurement noise.
4. A how-to that plans a round with `voi`, and an explanation page on the roles of the decision rule, the information layer and MCDM.
5. Turning MCDM scores into stake weights, once stakes data exist.
