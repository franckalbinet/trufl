# Scoring plan

Working plan for scoring sampling campaigns against a ground truth and comparing sampling strategies (#12). Still to be refined.

## Done

- `trufl.utils.zonal_values` returns the raster cells inside one unit as a flat array, without nodata or NaN cells. `PriorCB` uses it.
- `nbs/07_scoring.ipynb` holds `unit_stats`, a per-unit table with the true and measured mean and maximum, the sample count and the Wasserstein distance between the true cell values and the sample values. Units without samples have a count of 0 and `NaN` for the rest. It is not exported yet.
- The notebook runs the multi-year how-to's campaign with fixed seeds (150 samples a round, 4 rounds) and keeps the table after each round.

## First results

On the how-to campaign over `ground-truth-01`, averaged over units:

| Round | Samples | Mean absolute error of the mean | Mean error of the maximum | Mean Wasserstein distance |
|---|---|---|---|---|
| 1 | 150 | 0.0309 | -0.0608 | 0.0416 |
| 2 | 300 | 0.0116 | -0.0461 | 0.0219 |
| 3 | 450 | 0.0160 | -0.0430 | 0.0216 |
| 4 | 600 | 0.0076 | -0.0317 | 0.0153 |

- The measured maximum is always below the true maximum. A few samples rarely hit a unit's highest cell, so a score built on the maximum rewards sample count alone.
- Round 3 does not improve on round 2. We have not yet looked at which units cause this.
- `min=1` gives every unit a sample each round, so this campaign never has units without samples.
- Without a reference strategy, these numbers show only that more samples help.

## Campaigns

- Use "round" for one sampling step, not "year": a round can be a day, a week or a year during an emergency or remediation.
- A campaign takes any number of rounds and a budget for each round, as a list. This covers the roadmap's question of spending early or spreading the budget.
- Write the campaign runner as an environment, `reset(ground_truth, seed)` and `step(decision) -> table`. Baselines, comparisons and a later reinforcement learning agent then use one interface.

## Strategies

A strategy is the set of decisions made at each round: criteria, weights, benefit or cost for each criterion, optimizer settings, allocation policy and budget schedule. Placement within a unit stays uniform random for now, so comparisons isolate allocation. Candidates to start with:

- Equal allocation: the same number of samples in every unit. The baseline.
- Prior only: rank from the prior every round and ignore the measurements. Shows what the measurements add.
- The how-to strategy: six criteria, fixed weights.
- Single criteria, such as the standard deviation alone or the maximum alone. Shows what each criterion contributes.
- Neyman allocation: samples in proportion to each unit's standard deviation, estimated from the prior or the measurements.
- An oracle that allocates from the true per-unit values. Not possible in a real campaign. It gives an upper bound, so a strategy can be placed between equal allocation and the oracle.

## Ground truths

- Results from one raster are an anecdote. Each comparison needs several ground truths, and several seeds for each, with the spread across seeds reported.
- `_data/airdose_all_2011.tif` holds log10 air dose rates (µSv/h) from Fukushima in 2011: UTM 54N, 50 m cells, about 166 km by 155 km, 58% valid cells (sea and gaps are NaN). The plant is about 0.7 km from its east edge, at mid-height. `_data` is in `.gitignore`.
- Publication will need synthetic ground truths. The real raster serves to fit the generator's parameters, to set realistic ranges, and for internal checks that a strategy that wins on synthetic fields also wins on real ones.
- Generator: a trend from the release point (decay with distance, plume direction) plus a Gaussian random field residual, with parameters fitted on windows of the real raster. Fit on log values, and fit locally, because one stationary model does not fit the whole region. Modelling choices are explicit arguments.
- Describe each ground truth by position (distance and bearing from the release point) and by structure (mean level, gradient, correlation range, nugget, share of hotspot cells). Choose ground truths by position for variety, and explain results by structure: strategy results depend on structure, and the same distance gives very different fields inside and outside the plume.
- `anonymize_raster` only moves the origin, and it raises `NameError` (#10). Moving the origin does not hide the plume's outline.

## Comparing strategies

- Visualise first: one curve per strategy for each metric against the round, with a band across seeds, and per-unit error maps.
- Report each strategy relative to equal allocation and the oracle.
- The per-unit table stays as diagnostics. A headline score is still open (see below).
- Reinforcement learning fits the problem: the state is the per-unit state table, the action is the weights, benefit or cost choices and policy of a round, the step samples the ground truth, and the reward is the score improvement. Keeping actions at the level of weights keeps the policy readable. It needs a scalar score and many ground truths first. Before it, a search over fixed weight schedules shows how much adapting the weights between rounds is worth. RL is worth building only if the best weights depend on the state of the round.

## Proposed order

1. A campaign runner over rounds, with the environment interface.
2. The baseline strategies.
3. A headline score, with the per-unit table kept as diagnostics.
4. A ground-truth generator, and a few contrasting ground truths.
5. Plots comparing strategies.
6. A search over weight schedules, then reinforcement learning only if that search shows adapting the weights matters.

## Implementation notes

- Add `scipy` to the dependencies in `pyproject.toml` with the scoring code. `callbacks` already imports it directly, but it arrives only through `pysal`.
- `zonal_values` counts a cell whose centre lies exactly on a unit border in both units. Only `gridder` grids whose units are not a whole number of cells wide have such borders: on `ground-truth-02`, 1,376 of 705,200 cells are counted twice. Rounding `gridder` units to whole cells would remove the double count.
- `Sampler.sample` passes `rng` on through `**kwargs`, and its docs do not mention it.

## Open questions

- Headline score: classify each unit against an action level and count misclassifications, with a false negative costing more than a false positive? This needs the action levels and the costs of the two errors from domain experts. Do DSS4NAFA users have action levels we could use?
- How should true values be weighted in the Wasserstein distance? The ground truth may be polygons of different sizes, such as agricultural fields. On a raster, weights could come from cell area or from the share of a cell inside the unit. `wasserstein_distance` takes weights for both distributions.
- Should the how-to page show per-round tables, or should the scoring notebook keep its own campaign?
- Who needs to agree before results derived from the Fukushima data are published?
- What does `_data/output_raster.tif` represent? It is a 13.5 km by 13 km extract at 50 m, with values from 0.15 to 1.26.

## Later, from #12

- Hotspot detection: for each unit with hotspot cells, did its samples find one?
- Hotspot coverage: the share of hotspot cells within a given distance of a sample.
- Surface metrics from interpolation (IDW first), compared with the raster cell by cell.
