# Scoring plan

Working plan for scoring sampling campaigns against a ground truth and comparing sampling strategies (#12). Still to be refined.

## Role of MCDM

MCDM does two jobs in the current framework, in one weighted sum:

- It expresses what decision makers value. Criteria such as contamination level, population, food production or economic value cannot be compared directly. Someone has to own the trade-offs between them, the trade-offs change during an emergency, and they must be visible. MCDM does this well: each rank follows from criteria and weights that a person chose and can defend.
- It decides where samples teach the most. Standard deviation, count and Moran's I are about information, not value. A decision maker cannot meaningfully set "Count weighs 0.2": that weight is a technical setting presented as a preference.

The metrics so far (error of the mean, Wasserstein distance) score only the second job, which MCDM was not designed for. Equal allocation and the oracle beat MCDM on it, as expected. The results do not show that MCDM is wrong. They show that it was scored on a job that is not its own.

trufl's approach is justified by interpretability and ownership. Sampling decisions in an emergency are public and get challenged: "we sampled here because the prior is high and people live there, under the weights you agreed" can be defended, "the policy chose it" cannot. This holds only if decision makers set criteria they actually have views on. The direction is to separate the two jobs:

- Value criteria, owned by decision makers: what is at stake in each unit, and the action level that matters. MCDM aggregates them.
- An information layer, technical: it turns the stakes and the current uncertainty into an allocation. The principled version is value of information: sample where a measurement is likely to change a decision, such as a unit whose mean could lie on either side of the action level, weighted by what is at stake there. The rule stays explainable: "this unit could be above the action level, and 2,000 people live there".

The headline score follows from this: the cost of wrong decisions, weighted by the decision makers' own stakes. Strategies are compared under the same stated preferences. The question becomes measurable: how much learning efficiency does surfacing preferences cost, compared with the best allocation for those preferences?

End-to-end reinforcement learning still needs a reward that encodes the decision makers' values, so the values must be stated anyway, and RL would hide how they are traded off. It keeps interpretability only as the information layer, with stated preferences as input.

`StdCB`, `CountCB` and `MoranICB` are information criteria. Their fixes are needed under any framing; with this split they feed the information layer rather than the MCDM weights.

## Decision rule from DSS4NAFA

The DSS4NAFA restrictions dashboard suggests an action for each administrative unit, for one radionuclide and one foodstuff, from three sliders that decision makers adjust during a response:

- Permissible level (Bq/kg). It changes during an emergency or remediation.
- Minimum number of samples. Below it, the unit shows "Sample (too few samples analyzed)". With no samples, it shows "Undefined".
- Proportion over permissible level accepted (%). The unit is restricted when the share of its samples above the permissible level exceeds it. This rule is assumed from the dashboard, not checked in its code.

"Partially restrict" means the samples above the permissible level lie mainly on one side of the unit: the unit is too coarse for one decision. This links to the roadmap question on grids finer than administrative units. The first steps leave it out and score each unit as restrict or do not restrict.

The dashboard's purpose is to lower decision makers' cognitive load and let them project scenarios, including how a change of permissible level changes the restrictions. For trufl this gives:

- The headline score without new elicitation: apply the rule to the campaign's samples and to the ground truth (share of cells above the permissible level in each unit), and count units where the actions differ, and units left at "Sample" or "Undefined".
- The estimate that matters is the share of a unit above the permissible level, not its mean. Value of information follows from a binomial or beta model of that share: a unit whose share is close to the accepted proportion, with few samples, is where another sample most likely changes the decision.
- The minimum number of samples is a decision maker's preference. It is the cumulative minimum, and it comes from the slider rather than being a strategy parameter.
- The same scenario use: show where samples go under the current sliders, and how that changes with the permissible level. Allocating for a range of plausible levels keeps samples useful when the level changes.

Not covered by the sliders: the asymmetry between a missed restriction and a needless one, the stakes of each unit (such as foodstuff production), and how several foodstuffs and radionuclides share one sampling budget.

## Done

- `trufl.utils.zonal_values` returns the raster cells inside one unit as a flat array, without nodata or NaN cells. `PriorCB` uses it.
- `nbs/07_scoring.ipynb` holds `unit_stats`, a per-unit table with the true and measured mean and maximum, the sample count and the Wasserstein distance between the true cell values and the sample values. Units without samples have a count of 0 and `NaN` for the rest. It is not exported yet.
- The notebook runs campaigns with `Campaign` and `run` (see Campaigns). A six-round run takes about 1.2 seconds, and the same seed gives the same tables.
- Baselines in the notebook. `allocate` splits a budget in proportion to a weight per unit, after a minimum per unit. `equal`, `neyman` (standard deviation estimated from the samples so far) and `oracle` (true standard deviation) use it. `mcdm` takes its criteria as arguments, which gives the prior-only, max-only and std-only strategies. Strategies take a fourth argument, the campaign's random generator. `compare` runs every strategy once per seed.

## Baseline comparison

Seven strategies, 5 seeds each, 6 rounds of 150 samples on `ground-truth-01`, at least 1 sample per unit. After round 6, mean over seeds, with the standard deviation over seeds in brackets:

| Strategy | Mean absolute error of the mean | Mean error of the maximum | Mean Wasserstein distance |
|---|---|---|---|
| equal | 0.0099 (0.0009) | -0.0289 (0.0009) | 0.0143 (0.0008) |
| oracle | 0.0104 (0.0011) | -0.0275 (0.0022) | 0.0144 (0.0008) |
| neyman | 0.0104 (0.0016) | -0.0278 (0.0020) | 0.0147 (0.0010) |
| std only | 0.0104 (0.0009) | -0.0297 (0.0014) | 0.0150 (0.0006) |
| how-to | 0.0107 (0.0006) | -0.0307 (0.0017) | 0.0154 (0.0004) |
| max only | 0.0111 (0.0009) | -0.0319 (0.0018) | 0.0163 (0.0008) |
| prior only | 0.0120 (0.0006) | -0.0319 (0.0008) | 0.0170 (0.0005) |

- No strategy beats equal allocation on these metrics. The how-to strategy is worse than equal on all three.
- `min=1` takes 100 of the 150 samples in each round. The oracle can only give each unit 1 or 2 samples, although true standard deviations range from 0.005 to 0.104.
- These metrics weight every unit's accuracy equally, which is what equal allocation aims for. A strategy that concentrates samples on high-priority units can show its value only under a score that rewards it, such as the decision score in the open questions.
- Next checks: ground truths with more contrast between units, and a larger budget per round.

## Minimum number of samples

A minimum per round is itself an allocation decision: with 100 units, `min=1` fixes 100 of 150 samples in each round and 600 of 900 over six rounds. The reasons for a minimum concern the samples a unit has in total: each unit needs a measurement for its decision, `StdCB` and `MoranICB` need several samples, and a minimum protects against a wrong prior. `cumulative_min(strategy, k)` in the notebook tops up every unit with fewer than `k` samples so far, then lets `strategy` target the rest of the budget with no minimum of its own.

Mean Wasserstein distance after round 6, mean of 3 seeds (largest standard deviation over seeds: 0.0013):

| Strategy | No minimum | 1 per round | 1 in total | 2 in total |
|---|---|---|---|---|
| equal | 0.0146 | 0.0146 | 0.0146 | 0.0146 |
| oracle | 0.0136 | 0.0143 | 0.0138 | 0.0137 |
| neyman | 0.0161 | 0.0149 | 0.0161 | 0.0169 |
| how-to | 0.0194 | 0.0153 | 0.0193 | 0.0176 |
| std only | 0.0214 | 0.0147 | 0.0233 | 0.0164 |

- Without a minimum per round, only the oracle improves. It beats equal allocation, by about 7% on the Wasserstein distance and 11% on the error of the mean.
- Every strategy that estimates from the samples gets worse without a minimum per round. The minimum per round was limiting how far they concentrate samples.
- `std only` gets worst. A unit with one sample has a standard deviation of 0 from `StdCB` and is never chosen again: with 1 in total and seed 0, 25 units still have one sample after six rounds.
- 1 in total gives about the same results as no minimum. Without any minimum, the how-to run with seed 0 still ends with at least one sample in every unit; I have not checked the other strategies.
- Targeting by the true standard deviation helps, a little, on this smooth ground truth. Targeting by estimates from 1 to 3 samples per unit does not help yet.
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
- The campaign runner is an environment. `Campaign(fname_raster, gdf_units)` holds the ground truth; `reset(seed)` starts with no samples; `step(n)` draws and measures `n` samples per unit and returns `unit_stats` for all samples so far. A strategy is a function `(samples, gdf_units, budget) -> n`. `run(campaign, strategy, budgets, seed)` plays a strategy and returns the per-unit tables of every round, indexed by `round` and `loc_id`. Baselines, comparisons and a later reinforcement learning agent use the same interface.

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
- Reinforcement learning fits as the information layer (see Role of MCDM): it takes the decision makers' stated preferences as input and learns where samples teach the most, checked against value of information and the oracle. It needs the decision score and many ground truths first. Learning weight schedules is dropped: learned weights would mean "what works" while still looking like preferences, which mixes the two roles again.

## Approach

trufl is bending towards decisions, so the work goes in small steps:

- The library stays as it is while we find out. New work happens in `nbs/07_scoring.ipynb`. Published modules change only when a result shows the change is worth it. The `StdCB` and `MoranICB` fixes wait too: whether information criteria stay in MCDM depends on steps 1 and 2.
- trufl takes the decision rule as an input and does not copy the dashboard. A decision rule is a function from a unit's values to an action; the DSS4NAFA rule is the first example. trufl's core stays the same (describe the units, rank them, allocate the budget, sample). The rule enters only through scoring and through strategies that use it.
- Each step answers one question, fits in one commit and ends with its result recorded here.

Done: the campaign runner over rounds, the baseline strategies and the comparison of minimums.

1. The decision score. The DSS4NAFA rule as a function, the true action of each unit from the share of its raster cells above the permissible level, and a score per round counting wrong and unresolved decisions. Rerun the existing strategies and baselines under it. Question: does the ranking of strategies change when they are scored on decisions instead of means?
   Result. Done in the notebook: `decide`, `decisions` (a `score` for `Campaign`, which now takes its scoring function as an argument) and `summarise_decisions`; `compare` takes the summary function. On `ground-truth-01` with a permissible level of 0.8 and 10% accepted, 35 of 100 units should be restricted, and only 9 units have between 2% and 30% of their cells above the level. With one sample per unit per round and 5 seeds, wrong decisions after round 6 range from 2.6 (neyman) to 4.2 (std only), mostly missed restrictions, with a standard deviation over seeds of up to 2.7. Equal, how-to and max only all get 3.6. The how-to strategy no longer trails equal allocation and is ahead in rounds 2 and 3 (4.2 and 4.0 against 5.6 and 4.6). The score works, but this raster has too few close decisions to separate the strategies. Steps 2 and 3 (a decision oracle and contrasting ground truths) are needed for a signal.
2. A decision-aware strategy. A beta posterior on each unit's exceedance share, sampling where the decision is most likely to flip. The oracle samples the units whose true share is closest to the accepted proportion. Question: how close does a simple, explainable rule get to the oracle, and does MCDM add anything on top?
   Result. In `07_scoring.ipynb`: `bayes` (Jeffreys prior Beta(0.5, 0.5), allocation in proportion to the posterior probability that a unit's decision is wrong) and `decision_oracle` (the same probability from the true share and a binomial model). `Campaign` now reads the true values once (`true_values`), and score functions take them in place of the raster. Comparisons moved to `nbs/_scoring_experiments.ipynb`, which `nbdev-test` skips; it loads the definitions by running the code cells of `07_scoring.ipynb`, because IPython's `%run` of a notebook needs `nbformat`, which is not installed. Setup: 5 strategies, 20 seeds, 6 rounds of 150 samples, at least one sample per unit over the campaign, 10% accepted; `ground-truth-01` at a level of 0.8 (35 units to restrict, 9 near the boundary) and `ground-truth-02` at 0.473 (48 to restrict, 32 near the boundary). Wrong decisions after round 6:

   | Strategy | gt-01 at 0.8 | gt-02 at 0.473 |
   |---|---|---|
   | oracle | 1.4 | 6.5 |
   | bayes | 2.5 | 7.8 |
   | how-to | 2.8 | 9.2 |
   | equal | 3.2 | 10.0 |
   | neyman | 3.8 | 10.0 |

   The standard deviation over seeds is up to 3.2, so each mean has a standard error below 0.8. A simple, explainable rule (`bayes`) beats equal allocation and the how-to strategy, and the oracle shows room for a better one. The how-to strategy lies between equal and `bayes`: a likely reason, not checked, is that its benefit criteria (Max, Prior) point it at contaminated units, where the decisions near the level are. Neyman allocation, which targets estimation of the mean, does not help decisions.

   Finding about the dashboard rule: with "share of samples above the level exceeds the accepted proportion", one more sample can make a decision less reliable. With 10% accepted, the 10th sample raises the number of exceedances needed to restrict from 1 to 2: for a unit whose true share is 12%, the probability of a wrong decision is 32% with 9 samples and 66% with 10. This explains why the oracle on `ground-truth-02` gets worse from round 2 (6.6) to round 3 (9.0). The rule could be made monotonic, for example with a confidence bound on the share instead of the raw share; this is a question for DSS4NAFA, not only for trufl.

   With a few samples per unit the posterior on a share stays wide: after six rounds of the how-to campaign, `bayes` gives only 19 of 150 samples to the 5 units whose measured share is near 10%. A unit with 6 samples, none above the level, still has a 25% probability of a share above 10%.
3. More than one ground truth: `ground-truth-02` and, for internal checks only, windows of the Fukushima raster. Question: does the answer of steps 1 and 2 hold when units differ more?
4. Library changes decided from the evidence: exporting the scoring module, the callback fixes if information criteria stay, documenting the role of MCDM.

Waiting until these steps show which matter: stakes per unit, the asymmetry between the two kinds of error, several foodstuffs and radionuclides, "Partially restrict", a ground-truth generator, plots, and reinforcement learning for the information layer.

## Implementation notes

- Add `scipy` to the dependencies in `pyproject.toml` with the scoring code. `callbacks` already imports it directly, but it arrives only through `pysal`.
- `zonal_values` counts a cell whose centre lies exactly on a unit border in both units. Only `gridder` grids whose units are not a whole number of cells wide have such borders: on `ground-truth-02`, 1,376 of 705,200 cells are counted twice. Rounding `gridder` units to whole cells would remove the double count.
- `esda.Moran`, which `MoranICB` uses, takes no seed: its permutation test uses NumPy's global random state. `Campaign.reset` seeds it with `np.random.seed`. A `seed` or `rng` argument on `MoranICB` would remove that global side effect.
- In the how-to strategy, Moran's I is NaN for every unit when ranking rounds 2 and 3: units have at most 3 or 4 samples, and `MoranICB` needs more than `min_n=5`. `mcdm.py` warns "All-NaN slice encountered". The ranking is the same as without Moran's I with the other weights rescaled: `get_rank` fills the column with the same value for every unit, and in `CP` that adds the same distance to every unit.

## Open questions

- How should `StdCB` and `MoranICB` report unknown values? Today `get_rank` fills every NaN with the highest priority after normalisation, and `LINEAR1` turns every criterion into a benefit. `StdCB` returns `np.std` (`ddof=0`): 0 for one sample, which normalises to the lowest priority, so the most uncertain units look the most certain. After round 1 of the how-to strategy, 75 units are in that case. `MoranICB` returns NaN both for too few samples (unknown) and for a Moran's I that is not significant (no evidence of spatial structure). With Moran's I as a cost, both get top priority, which matches the intent only by coincidence; as a benefit, "not significant" would get top priority. Returning 0 for "not significant" conflicts with `LINEAR1`, which raises `ValueError` when a cost criterion's minimum is 0, and negative values would leave [0, 1]. Options for `MoranICB`: return 0 and move strategies using it to `LINEAR2`; return I always, with the pseudo p-value as a second variable; keep NaN and document its two meanings. Proposed: `StdCB` returns NaN below 2 samples and uses `ddof=1`; `MoranICB` returns 0 when not significant; the how-to strategy moves to `LINEAR2`. This changes published behaviour and the how-to page's ranking. Not decided.

- Headline score: classify each unit against an action level and count misclassifications, with a false negative costing more than a false positive? This needs the action levels and the costs of the two errors from domain experts. Do DSS4NAFA users have action levels we could use?
- How should true values be weighted in the Wasserstein distance? The ground truth may be polygons of different sizes, such as agricultural fields. On a raster, weights could come from cell area or from the share of a cell inside the unit. `wasserstein_distance` takes weights for both distributions.
- Should the how-to page show per-round tables, or should the scoring notebook keep its own campaign?
- Who needs to agree before results derived from the Fukushima data are published?
- What does `_data/output_raster.tif` represent? It is a 13.5 km by 13 km extract at 50 m, with values from 0.15 to 1.26.

## Later, from #12

- Hotspot detection: for each unit with hotspot cells, did its samples find one?
- Hotspot coverage: the share of hotspot cells within a given distance of a sample.
- Surface metrics from interpolation (IDW first), compared with the raster cell by cell.
