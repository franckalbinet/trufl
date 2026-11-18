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
- It gives each remaining sample to the unit with the largest drop of `expected_wrong` per sample over the next 1 to `horizon` samples (10 by default; 5 left needless restrictions in place, see the plume evidence).
- `prior` is an optional raster, such as an airborne survey, and `strength` the number of samples it is worth.

With a value layer, the gain of each unit is multiplied by its stake weight, so a sample goes where it most lowers the stake-weighted number of wrong decisions. With no value layer, every weight is 1.

`allocate` (proportional allocation after a minimum) is a shared helper. `bayes`, `equal` and `neyman` are baselines, and stay in the simulation module.

## Placement within a unit

Where samples go inside a unit matters as much as how many each unit gets, once the field is spatially correlated. Proposed: placement as a part next to the information layer. Nothing here is decided.

The binomial model in `bayes` and `voi` assumes samples placed uniformly at random within the unit. Then each sample is above the level with probability equal to the share of the unit's area above it, whatever the spatial pattern, so the model is exact. It does not assume an uncorrelated field.

Evidence, from "Placement within a unit" in `nbs/_scoring_experiments.ipynb`: synthetic Gaussian random fields on one unit, 1,000 fields per setting, correlation set by a smoothing width `sigma` (16 cells is 1/8 of the unit width):

- Random placement gives the binomial error whatever the correlation.
- At `sigma` 16, a systematic grid of 16 samples estimates the share about as well as 49 random samples; 36 as well as about 150; 64 as well as about 400.
- At `sigma` 16 and a true share of 12%, 64 random samples give a wrong decision 38% of the time, and 64 systematic samples 12%.
- Clustered placement (4 clusters, as when teams sample near roads or one farm) is wrong 56 to 58% of the time at 12%, and more samples don't help. Most clusters miss the patch, so the errors are missed restrictions.
- With no correlation, all placements are the same.

What it would change:

- Recommend a systematic or stratified layout within each unit. It costs no extra samples. Without correlation it matched random placement within simulation noise, and with correlation it did better.
- In `voi`, replace each unit's sample count by an effective count that depends on the placement and on the correlation range relative to the unit size. Without it, `voi` overspends on spread units and is overconfident on clustered ones.
- Estimate the correlation range from a variogram or the scale of the prior raster. Moran's I from a unit's samples shows whether correlation is present, but not its range.
- With strong correlation, the exceedances form a patch, which makes "partially restrict" meaningful and opens adaptive placement near the first exceedances.

### Directional fields and plumes

After an accident, contamination follows the plume. That gives two effects. Within a unit, the correlation is anisotropic: a long range along the plume and a short one across it. Between units, there is a trend: values fall with distance from the source and away from the plume axis, so decisions are close only along the plume edge. The usual model is `log value = trend + correlated residual`, with the trend from a dispersion model or the airborne survey. Nothing here is decided.

Evidence, from "Directional fields", "A synthetic plume", "Placement in the plume" and "Replication over plumes" in `nbs/_scoring_experiments.ipynb` (synthetic fields only):

- Within a unit (36 samples, 2,000 fields per setting), strata stretched along the plume, by rotating the coordinates to the plume axis and dividing by the range in each direction, are worth about 10 more samples than square strata when the anisotropy is strong (ranges 2 by 32 cells), and 1 to 7 more when it is mild (4 by 16). Stretched along the wrong axis, they lose most of the gain from stratifying. Square strata are the safe choice when the direction is uncertain.
- Between units (a synthetic Gaussian plume over 10 by 10 units, 40 seeds, wrong decisions after round 6): `voi` with a survey or perfect prior 3.2 to 4.5, with a dispersion-model prior at strength 4 5.0, with no prior 5.8, equal allocation 6.2. With the wind 10° off, the dispersion prior at strength 4 gives no gain (5.7). At strength 20, both dispersion priors are worse than equal allocation (9.1 and 8.0), because the trend lacks the residual patches.
- Placement in the plume (`Campaign(placement=...)`, five strategies, 40 seeds): against uniform placement, `spread` along the plume lowers wrong decisions after round 6 by 0.78 ± 0.17 on average over the strategies, `spread` in every direction by 0.30 ± 0.16, and the wrong axis by 0.04 ± 0.16. `voi` with the dispersion prior and spread along the plume makes 4.3 wrong decisions, as few as `voi` with the survey prior and uniform placement (4.4).
- Replication over ten plume fields (own seed, wind angle, spread and residual strength; seven strategies, three placements, 20 seeds each), differences between fields: the survey prior at strength 4 lowers wrong decisions against `voi` with no prior by 1.1 ± 0.26 (9 of 10 fields) and the dispersion prior by 0.48 ± 0.18 (7 of 10). `spread` lowers them by 0.51 ± 0.25 and `spread` along the plume by 0.63 ± 0.31, averaged over strategies; the two do not differ clearly (0.12 ± 0.09). `bayes` gains most from spreading (1.29 ± 0.34, all 10 fields) and `voi` least (0.14 ± 0.43). Not confirmed from the single plume: no gain with the wind 10° off (over ten fields, 0.38 ± 0.22), harm from the dispersion prior at strength 20 on every plume (5 of 10), `voi` better than `bayes` (no difference).
- `voi`'s horizon ("Diagnosis" and "`voi`'s horizon" in the experiments notebook): with a horizon of 5, `voi` stopped sampling units with an early exceedance, such as 1 of 3 above the level, because the measured share drops to 10% only after 7 more clean samples. These became needless restrictions. Over the ten plume fields, a horizon of 10 lowers wrong decisions for 8 of the 9 pairs of strategy and placement, by 0.4 to 1.4, more with spread placement than without. It also raises missed restrictions by 0.1 to 1.3. With horizon 10 and spread placement, `voi` with the survey prior makes 2.7 wrong decisions and with the dispersion prior 3.2 to 3.4, the fewest of the realistic strategies tested. The default `horizon` in `nbs/07_scoring.ipynb` is now 10.

What it would change:

- Placement: spread samples away from a unit's earlier samples. Across rounds this needs a placement such as `spread` in `nbs/07_scoring.ipynb` (best-candidate sampling), because strata built each round hold one or two samples. Over ten plumes, stretching the distances along the plume added little to spreading in every direction (0.12 ± 0.09 fewer wrong decisions). It may matter more with stronger anisotropy or larger units, which is not tested.
- Priors: a dispersion model can serve as `voi`'s prior before a survey exists, with a small weight (about 4 samples). Over ten plumes it lowered wrong decisions in 7, and a weight of 20 was harmful on some plumes. A survey, once available, is the better prior.
- Decisions: a unit cut by the plume edge is the clearest case for "partially restrict", and the trend gives the line along which to split it.
- Publication: the synthetic plume is a candidate ground truth that resembles a real accident without using Fukushima data.

## Value layer

`Optimizer`, `State` and the callbacks keep their role of ranking units, on value criteria. The proposed change is in what they are used for: they give `voi` weights per unit instead of deciding the allocation themselves through `rank_to_sample`. With two costs per unit, they give two weights, one for each kind of wrong decision (see "Costs from MCDM" under "Dilemmas").

Two open points:

- How a rank becomes a weight. A rank loses the size of the differences between units; the `CP` or `TOPSIS` score keeps it. Proposed: use the score, rescaled to [0, 1].
- Whether the information criteria (`StdCB`, `CountCB`, `MoranICB`) stay in the recommended path. With `voi` handling information, they are not needed for allocation. They stay in the library for existing users.

## Dilemmas

A nuclear response weighs one harm against another. Economic value against health risk is one example. This section lists the dilemmas found so far, and what each one would change in trufl. Nothing here is decided.

### Two costs per unit

Today `voi` counts every wrong decision as 1, and the value layer proposes one stake weight per unit. A needless restriction and a missed restriction have different stakes. The cost of a needless restriction grows with what the restriction destroys, such as the economic value of a crop. The cost of a missed restriction grows with the risk to consumers. Proposed: two weights per unit, from the value layer, and `voi` lowers the expected cost:

    expected cost = c_needless * P(needless restriction) + c_missed * P(missed restriction)

Example: a field with a crop of high economic value, with 2 of 20 samples above the level, which is exactly the 10% accepted. The decision is close, so `voi` already gives the field priority. A high `c_needless` raises it further, and sends extra samples to settle whether the true share is below 10%.

The costs set where to sample, not what to decide. The decision stays with the decision rule. Raising the accepted share for valuable crops would trade health protection for money, which is a policy choice for the authorities.

### Costs from MCDM

MCDM turns the criteria of each unit into its two costs. The trade-off between the two kinds of error stays outside MCDM, as one setting for decision makers. Nothing here is decided.

Each cost has its own criteria:

- `c_needless` (restricting a unit that did not need it): economic value of the crop, dependence of local food security on it, number of farms and jobs, market reputation of the region.
- `c_missed` (releasing a unit that should have been restricted): population eating the produce, share eaten by the households that grow it, consumption rates, children, transfer of contamination from soil to crop.

Two MCDM runs give each unit a score between 0 and 1 for each cost. The existing machinery does this without change: callbacks compute the criteria per unit, `Optimizer` normalises and weights them, and the `CP` or `TOPSIS` score is the result. Most of these criteria are rasters (population, crop value, land use). `PriorCB` reads the mean of any raster over a unit, these included.

Normalised scores are relative to the other units. A score of 0.8 for economic value cannot be compared with a score of 0.8 for health risk. The ratio between the two costs is a policy choice, made explicit as one setting `r`:

    expected cost = c_needless * P(needless restriction) + r * c_missed * P(missed restriction)

MCDM sets the stakes among units for each kind of error. `r` sets the trade-off between the two kinds of error. Decision makers see and set `r` directly, next to the permissible level and the accepted proportion, instead of leaving it implicit in criteria weights.

MCDM also gives:

- A record of why each unit gets its samples: its decision is close (information layer) and its stakes are high (value layer).
- Sensitivity analysis: vary the criteria weights and `r`, then compare allocations and expected wrong decisions. Units sampled under every reasonable weighting are safe choices. Units whose samples depend on the weights show where decision makers must agree.

Gaps in the current MCDM layer:

- `LINEAR1` gives the lowest unit a score of 0. Its cost would be 0 and `voi` would never sample it, however close its decision. Costs need a floor, such as `c = c_min + score`, or a normalisation that never gives 0.
- Scores depend on the set of units. Adding or removing a unit changes every cost. Normalising against fixed reference values, such as the economic value of a typical field, keeps costs stable across campaigns.
- Sampler dose and deadlines are not stakes. They belong to the budget and the timing (see "Dilemmas that need new parts in trufl"), not to MCDM.

### Health as a limit

The testbed ("Two costs per unit" in `nbs/_scoring_experiments.ipynb`) shows that costs used only to allocate samples weaken health protection where economic value is high. Under the dashboard's rule, more samples can only restrict a unit that is not restricted, and can only lift a restricted one. When a needless restriction is expensive, sampling a clean-looking unit raises its expected cost. `voi` then stops sampling it, and contamination there goes unfound. On ten synthetic plumes, with a needless restriction costing 5 in half the units, missed restrictions in that half rose from 0.3 to 1.8 per campaign for `voi` without a prior, and from 1.3 to 8.5 with the dispersion prior.

Proposed: health is a limit, not a cost. `voi` first samples every unit whose probability of a missed restriction is above a bound, such as 5%, until it falls below it or more samples cannot lower it. The costs then decide where the remaining samples go. Economic value can then add samples to valuable units but cannot take them away from the health check. The bound is a policy setting, like the permissible level, for decision makers and DSS4NAFA to set. Nothing here is decided.

First test ("Health as a limit" in the experiments notebook, same plumes and costs, `voi(max_missed=...)`): a bound of 5% brings missed restrictions in the valuable half down to 0.2 to 0.3, but takes the whole budget, so the costs no longer act. A bound of 20% with the dispersion prior gives 1.6 missed restrictions there (8.5 without a bound, 1.3 with equal costs) and fewer needless ones than with equal costs (0.30 against 0.53). Without a prior, a bound of 20% barely helps, because a clean unit needs about 8 samples to reach it. The bound sets the trade-off between health protection and room for economic costs.

### Dilemmas that fit the two-cost model

- Food security against contamination. Where a staple feeds subsistence farmers, a restriction can cause more harm to health, through hunger and poor diet, than the dose it prevents. This raises `c_needless` for staples in poor areas.
- Livelihoods and communities against precaution. At Fukushima, the harm from relocation and loss of farming was large compared with the dose avoided. This cost belongs in `c_needless`, beyond the market price of the crop.
- Self-consumption against market produce. Market produce passes later checks; food a household grows and eats itself does not. A missed restriction on home gardens has no second barrier, so `c_missed` is higher there.
- Stigma against evidence ("fuhyo higai", harm from rumours). Buyers avoided Fukushima produce even below the limits. A needless restriction damages a region's reputation for years after it is lifted, which raises `c_needless`.

### Dilemmas that need new parts in trufl

- Speed against certainty. Leafy vegetables and milk can't wait for more rounds; stored grain can. trufl runs rounds with no clock. This needs a deadline, or a cost of delay, per unit.
- Sampler dose against information. Sampling near the plant exposes the teams, so a sample there costs more in dose as well as money. This needs a cost per sample that varies by unit, so the budget is no longer a count of samples.
- Coverage and equity against efficiency. `voi` sends samples where decisions are close, so settled or small units get few. Communities that see no sampling lose trust, and smallholders may get less protection than valuable estates. A minimum number of samples per unit is partly a fairness and trust constraint, not only a statistical one.
- Restriction against countermeasures. Potassium fertiliser, deep ploughing, clean feed for livestock and a change of crop are options as well as restriction. With more than two actions, the decision rule chooses among options instead of comparing with a threshold.
- Which commodity to sample. Transfer from soil to crop differs a lot between crops, so one field can be safe for grain and unsafe for mushrooms. The unit becomes a pair of field and crop.

Proposed priority: speed (deadlines) and sampler dose (variable sample cost) first, since both occur in every response and both change where samples go. Equity and decisions with several actions are larger design changes, for after the core is stable.

### Dilemmas for the policy, not for trufl

- Strict against lenient levels. Japan's limit for general food is 100 Bq/kg; the Codex guideline level is 1000 Bq/kg. A strict level builds trust and helps trade, but leads to more restrictions. The authorities set the level, and trufl takes it as input.
- Fine against coarse restriction units. Restricting a whole municipality is simple but restricts clean land. Partial restrictions need more samples. trufl could show what each unit size costs in samples, but the choice stays with the authorities.

## Simulation module

Proposed module `trufl.simulation`, exported from `nbs/07_scoring.ipynb`:

- `Campaign(fname_raster, gdf_units, score)` with `reset(seed)` and `step(n)`, `run(campaign, strategy, budgets, seed)` and `compare(campaign, strategies, budgets, seeds, summary)`.
- `unit_values`, `degrade` (prior rasters), and the scores `decisions` and `unit_stats` with their summaries.
- The baselines `equal`, `neyman`, `bayes`, the oracles, `cumulative_min`, and `mcdm` for the how-to strategy.

Its main use is comparing strategies before an emergency, on simulated ground truths. Measurement noise in `DataCollector` (#11) belongs here too.

### Reinforcement learning as a benchmark

`voi` is greedy: each round, it gives samples where they help most now, looks at most `horizon` samples ahead per unit, and treats units as independent. A policy trained by reinforcement learning could plan the whole campaign. It could save budget for later rounds, stop sampling a unit that later rounds will settle more cheaply, and use links between units, such as neighbours in a plume. It could also handle effects that have no closed form: spatial correlation, adaptive placement within a unit, measurement noise, deadlines and sampler dose.

`Campaign` already has the interface of an environment (`reset`, `step`). The reward would be minus the cost of the wrong decisions at the end of the campaign, with the health bound as a constraint (constrained reinforcement learning).

The costs: training needs many simulated campaigns, so the policy is only as good as the synthetic ground truths are realistic. A learned policy is much harder to explain to decision makers than `voi`. A hard health bound is harder to guarantee than with `voi`'s explicit first pass.

Proposed: use reinforcement learning as a benchmark, not as the method. It would show how far any strategy can improve on `voi`, and in which situations. Where the gap is large, the insight goes into `voi` in an explainable form, such as an effective sample count or a rule for saving budget across rounds. Nothing here is decided.

## Changes to published behaviour

Each of these needs your decision:

1. `StdCB` returns NaN below 2 samples, and uses the sample standard deviation (`ddof=1`). Today a unit with one sample gets 0, which ranks it as the least uncertain.
2. `MoranICB`: return 0 when Moran's I is not significant, return I always with the p-value as a second variable, or keep NaN for both cases and document it. A significant negative Moran's I already stopped a run (`LINEAR1` rejects negative values).
3. `LINEAR1` rejects any zero or negative value. Options: make `LINEAR2` the default in examples and the how-to, or clip, or document. This matters less if information criteria leave the recommended path, since value criteria are rarely negative.
4. `rank_to_sample` stays as it is. The how-to page keeps working; a new how-to shows `voi`.
5. New public modules or functions: the rule class, `voi`, `expected_wrong`, `allocate`, and `trufl.simulation`. Names and module boundaries are open.

## Out of scope for the first version

- Stakes data and their elicitation. The value layer starts with weight 1 for every unit.
- The asymmetry between a missed and a needless restriction (see "Two costs per unit"), and the other dilemmas.
- Several foodstuffs and radionuclides sharing one budget.
- "Partially restrict". Placement within a unit stays uniform random in the first version (see "Placement within a unit").
- How to set the weight of a prior from its quality.
- Reinforcement learning, except as a benchmark (see "Reinforcement learning as a benchmark").

## Questions for DSS4NAFA

- The sawtooth: with the current rule, one more sample can make a decision less reliable. With 10% accepted, a unit whose true share is 12% is decided wrongly 32% of the time with 9 samples and 66% with 10.
- Should restriction decisions use prior information, such as the airborne survey, as well as samples?
- Would decision makers accept setting the ratio `r` between the cost of a missed and of a needless restriction openly, as a dashboard setting next to the permissible level and the accepted proportion? See "Costs from MCDM".
- What bound on the probability of a missed restriction per unit would be acceptable, and should it be the same for every unit? See "Health as a limit".

## Proposed order

Each step fits one commit, after your decisions above:

1. The `StdCB` and `MoranICB` changes, if agreed.
2. The decision rule class, `expected_wrong` and `voi` in the library, with `voi` taking stake weights (all 1 by default).
3. `trufl.simulation`, exported from `nbs/07_scoring.ipynb`, with measurement noise.
4. A how-to that plans a round with `voi`, and an explanation page on the roles of the decision rule, the information layer and MCDM.
5. Turning MCDM scores into stake weights, once stakes data exist.
